require('dotenv').config();
const express = require('express');
const axios = require('axios');
const { exec } = require('child_process');
const fs = require('fs');
const { promisify } = require('util');
const execAsync = promisify(exec);

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const GITLAB_API = 'https://gitlab.com/api/v4';
const GITLAB_HEADERS = { 'PRIVATE-TOKEN': process.env.GITLAB_TOKEN };
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const MISTRAL_API_KEY = process.env.MISTRAL_API_KEY;
const MISTRAL_MODEL = process.env.MISTRAL_MODEL || 'mistral-large-latest';
const DOCKER_IMAGE = process.env.DOCKER_IMAGE || 'myapp:latest';

// ─────────────────────────────────────────────
//  Helper Mistral — API Chat Completions (standard)
//  Compatible: api.mistral.ai/v1/chat/completions
// ─────────────────────────────────────────────
async function callMistral(systemPrompt, userMessage) {
  if (!MISTRAL_API_KEY) throw new Error('MISTRAL_API_KEY manquant dans .env');

  const endpoint = 'https://api.mistral.ai/v1/chat/completions';

  const payload = {
    model: MISTRAL_MODEL,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user',   content: userMessage  },
    ],
    temperature: 0.3,
    max_tokens: 1024,
  };

  const headers = {
    'Authorization': `Bearer ${MISTRAL_API_KEY}`,
    'Content-Type':  'application/json',
    'Accept':        'application/json',
  };

  const resp = await axios.post(endpoint, payload, { headers, timeout: 60000 });

  // Format standard OpenAI/Mistral: choices[0].message.content
  const content = resp.data?.choices?.[0]?.message?.content;
  if (!content) throw new Error('Réponse Mistral vide ou format inattendu: ' + JSON.stringify(resp.data));
  return content.trim();
}

// ─────────────────────────────────────────────
//  Helper Anthropic — fallback si Mistral absent
// ─────────────────────────────────────────────
async function callAnthropic(systemPrompt, userMessage) {
  if (!ANTHROPIC_API_KEY) throw new Error('ANTHROPIC_API_KEY manquant dans .env');

  const resp = await axios.post(
    'https://api.anthropic.com/v1/messages',
    {
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1024,
      system: systemPrompt,
      messages: [{ role: 'user', content: userMessage }],
    },
    {
      headers: {
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json',
      },
      timeout: 60000,
    }
  );
  return resp.data.content[0]?.text?.trim() || '';
}

// ─────────────────────────────────────────────
//  Routeur IA : Mistral en priorité, Claude en fallback
// ─────────────────────────────────────────────
async function callAI(systemPrompt, userMessage) {
  if (MISTRAL_API_KEY) {
    return await callMistral(systemPrompt, userMessage);
  }
  if (ANTHROPIC_API_KEY) {
    return await callAnthropic(systemPrompt, userMessage);
  }
  throw new Error('Aucun LLM configuré. Ajoutez MISTRAL_API_KEY ou ANTHROPIC_API_KEY dans .env');
}

// ─────────────────────────────────────────────
//  Prompt système DevSecOps
// ─────────────────────────────────────────────
const AGENT_SYSTEM_PROMPT = `Tu es un agent expert DevSecOps. Tu aides les équipes à:
- Analyser les résultats de pipelines CI/CD GitLab
- Interpréter les vulnérabilités de sécurité (SAST, dépendances, Docker, secrets)
- Recommander des corrections concrètes et priorisées
- Expliquer les bonnes pratiques DevSecOps
- Diagnostiquer les échecs de déploiement

Réponds TOUJOURS en français, de façon concise et actionnable.
Si une action est dangereuse (exposer des secrets, supprimer des ressources), refuse poliment.`;

// ─────────────────────────────────────────────
//  Helpers GitLab + logs
// ─────────────────────────────────────────────
async function gitlabGet(path) {
  const res = await axios.get(`${GITLAB_API}${path}`, { headers: GITLAB_HEADERS });
  return res.data;
}

function writeLog(entry) {
  const line = JSON.stringify({ ...entry, timestamp: new Date().toISOString() }) + '\n';
  try { fs.appendFileSync('/var/log/devsecops-agent.log', line); } catch (_) {}
}

// ─────────────────────────────────────────────
//  GET /health
// ─────────────────────────────────────────────
app.get('/health', (req, res) => {
  const provider = MISTRAL_API_KEY ? 'mistral' : ANTHROPIC_API_KEY ? 'anthropic' : 'none';
  res.json({
    status: 'ok',
    ai_provider: provider,
    model: MISTRAL_API_KEY ? MISTRAL_MODEL : 'claude-sonnet-4-20250514',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// ─────────────────────────────────────────────
//  POST /ask — Agent IA conversationnel
// ─────────────────────────────────────────────
app.post('/ask', async (req, res) => {
  const { question, user_id } = req.body;
  if (!question) return res.status(400).json({ error: 'Le champ "question" est requis.' });

  writeLog({ action: 'ask', user_id, question });

  // Enrichissement avec contexte GitLab en temps réel
  let gitlabContext = '';
  try {
    const project_id = process.env.GITLAB_PROJECT_ID;
    const [pipelines, jobs] = await Promise.all([
      gitlabGet(`/projects/${project_id}/pipelines?per_page=3`),
      gitlabGet(`/projects/${project_id}/jobs?per_page=5`),
    ]);
    gitlabContext =
      `\n\n[Contexte GitLab en temps réel]\n` +
      `- Dernier pipeline: #${pipelines[0]?.id} | statut=${pipelines[0]?.status} | branche=${pipelines[0]?.ref}\n` +
      `- Dernier job: ${jobs[0]?.name} (${jobs[0]?.status})\n`;
  } catch (_) {}

  try {
    const answer = await callAI(AGENT_SYSTEM_PROMPT + gitlabContext, question);
    res.json({ answer });
  } catch (err) {
    console.error('[/ask]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ─────────────────────────────────────────────
//  POST /scan/sast
// ─────────────────────────────────────────────
app.post('/scan/sast', async (req, res) => {
  const { project_id } = req.body;
  writeLog({ action: 'scan_sast', project_id });
  try {
    const reports = await gitlabGet(
      `/projects/${project_id}/vulnerability_findings?per_page=100&scanner_id=semgrep`
    ).catch(() => []);
    const vulns = Array.isArray(reports) ? reports : [];
    const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
    const details = [];
    vulns.forEach(v => {
      const sev = v.severity?.toLowerCase() || 'info';
      if (sev in counts) counts[sev]++;
      details.push({ severity: v.severity, title: v.name, location: v.location?.file });
    });
    res.json({ ...counts, total: vulns.length, details, scanner: 'Semgrep', scanned_at: new Date().toISOString() });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─────────────────────────────────────────────
//  POST /scan/deps
// ─────────────────────────────────────────────
app.post('/scan/deps', async (req, res) => {
  const { project_id } = req.body;
  writeLog({ action: 'scan_deps', project_id });
  try {
    const reports = await gitlabGet(
      `/projects/${project_id}/vulnerability_findings?per_page=100&report_type=dependency_scanning`
    ).catch(() => []);
    const vulns = Array.isArray(reports) ? reports : [];
    const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
    const details = [];
    vulns.forEach(v => {
      const sev = v.severity?.toLowerCase() || 'info';
      if (sev in counts) counts[sev]++;
      details.push({
        severity: v.severity,
        title: v.name,
        location: v.location?.dependency?.package?.name,
        cve: v.identifiers?.find(i => i.type === 'cve')?.value,
      });
    });
    res.json({ ...counts, total: vulns.length, details, scanner: 'Dependency Scanning', scanned_at: new Date().toISOString() });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─────────────────────────────────────────────
//  POST /scan/docker
// ─────────────────────────────────────────────
app.post('/scan/docker', async (req, res) => {
  const { project_id, image = DOCKER_IMAGE } = req.body;
  writeLog({ action: 'scan_docker', project_id, image });
  try {
    let result;
    try {
      const { stdout } = await execAsync(`trivy image --format json --quiet ${image}`, { timeout: 120000 });
      const report = JSON.parse(stdout);
      const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
      const details = [];
      (report.Results || []).forEach(r => {
        (r.Vulnerabilities || []).forEach(v => {
          const sev = (v.Severity || 'UNKNOWN').toLowerCase();
          if (sev in counts) counts[sev]++;
          details.push({ severity: v.Severity, title: v.VulnerabilityID, location: `${v.PkgName}@${v.InstalledVersion}` });
        });
      });
      result = { ...counts, total: details.length, details, scanner: 'Trivy', image, scanned_at: new Date().toISOString() };
    } catch (_) {
      const reports = await gitlabGet(
        `/projects/${project_id}/vulnerability_findings?per_page=100&report_type=container_scanning`
      ).catch(() => []);
      const vulns = Array.isArray(reports) ? reports : [];
      const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
      const details = [];
      vulns.forEach(v => {
        const sev = v.severity?.toLowerCase() || 'info';
        if (sev in counts) counts[sev]++;
        details.push({ severity: v.severity, title: v.name, location: v.location?.image });
      });
      result = { ...counts, total: vulns.length, details, scanner: 'GitLab Container Scanning', image, scanned_at: new Date().toISOString() };
    }
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─────────────────────────────────────────────
//  POST /scan/secrets
// ─────────────────────────────────────────────
app.post('/scan/secrets', async (req, res) => {
  const { project_id } = req.body;
  writeLog({ action: 'scan_secrets', project_id });
  try {
    const reports = await gitlabGet(
      `/projects/${project_id}/vulnerability_findings?per_page=100&report_type=secret_detection`
    ).catch(() => []);
    const vulns = Array.isArray(reports) ? reports : [];
    const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
    const details = [];
    vulns.forEach(v => {
      const sev = v.severity?.toLowerCase() || 'critical';
      if (sev in counts) counts[sev]++;
      details.push({ severity: v.severity, title: v.name, location: v.location?.file, line: v.location?.start_line });
    });
    res.json({ ...counts, total: vulns.length, details, scanner: 'Secret Detection (Gitleaks)', scanned_at: new Date().toISOString() });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─────────────────────────────────────────────
//  POST /report — Rapport complet avec recommandations IA
// ─────────────────────────────────────────────
app.post('/report', async (req, res) => {
  const { project_id } = req.body;
  writeLog({ action: 'report', project_id });
  try {
    const [pipelines, vulns] = await Promise.all([
      gitlabGet(`/projects/${project_id}/pipelines?per_page=1`),
      gitlabGet(`/projects/${project_id}/vulnerability_findings?per_page=200`).catch(() => []),
    ]);

    const pipeline = pipelines[0] || {};
    const all = Array.isArray(vulns) ? vulns : [];
    const counts = { critical: 0, high: 0, medium: 0, low: 0, secrets: 0 };
    all.forEach(v => {
      const sev = v.severity?.toLowerCase();
      if (sev in counts) counts[sev]++;
      if (v.report_type === 'secret_detection') counts.secrets++;
    });

    let score = 100 - counts.critical * 20 - counts.high * 10 - counts.medium * 5 - counts.secrets * 15;
    score = Math.max(0, Math.min(100, score));

    // Recommandations générées par Mistral (ou Claude en fallback)
    let recommendations = [];
    try {
      const userMsg =
        `Voici les résultats de sécurité du projet: ${JSON.stringify(counts)}. ` +
        `Score de sécurité calculé: ${score}/100. ` +
        `Donne exactement 5 recommandations prioritaires courtes en français (1 ligne chacune). ` +
        `Réponds UNIQUEMENT en JSON valide, sans texte avant ni après: {"recommendations": ["...", "...", "...", "...", "..."]}`;

      const raw = await callAI(
        'Tu es un expert en sécurité applicative. Réponds uniquement en JSON valide, sans markdown ni commentaire.',
        userMsg
      );
      const parsed = JSON.parse(raw.replace(/```json|```/g, '').trim());
      recommendations = parsed.recommendations || [];
    } catch (_) {
      recommendations = [
        'Corriger immédiatement toutes les vulnérabilités critiques',
        'Mettre à jour les dépendances avec des CVE connues',
        'Rotation immédiate de tous les secrets potentiellement exposés',
        'Activer les scans automatiques SAST et secrets dans la CI/CD',
        'Mettre en place une politique de revue de code obligatoire',
      ];
    }

    res.json({
      generated_at: new Date().toISOString(),
      ai_provider: MISTRAL_API_KEY ? 'mistral' : 'anthropic',
      summary: { pipeline_status: pipeline.status || 'unknown', ...counts, score, total_vulns: all.length },
      recommendations,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─────────────────────────────────────────────
//  POST /webhook/gitlab
// ─────────────────────────────────────────────
app.post('/webhook/gitlab', async (req, res) => {
  const event = req.headers['x-gitlab-event'];
  const token = req.headers['x-gitlab-token'];

  if (token !== process.env.GITLAB_WEBHOOK_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  res.json({ received: true });
  writeLog({ action: 'webhook', event });

  const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;
  const CHAT_ID = process.env.TELEGRAM_CHAT_ID;
  if (!TELEGRAM_TOKEN || !CHAT_ID) return;

  const notify = (text) =>
    axios.post(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`, {
      chat_id: CHAT_ID, text, parse_mode: 'Markdown',
    }).catch(() => {});

  const body = req.body;
  const emojiMap = { success: '✅', failed: '❌', running: '🔄', pending: '⏳', canceled: '⛔' };

  if (event === 'Pipeline Hook') {
    const { object_attributes: pa, project } = body;
    if (['success', 'failed', 'canceled'].includes(pa.status)) {
      const dur = pa.duration ? `${Math.round(pa.duration)}s` : 'N/A';
      await notify(`${emojiMap[pa.status] || '❓'} *Pipeline ${pa.status.toUpperCase()}*\n• Projet: ${project?.name}\n• Branche: \`${pa.ref}\`\n• ID: #${pa.id}\n• Durée: ${dur}`);
    }
  }

  if (event === 'Job Hook') {
    const { build_status, build_name, build_stage, project_name } = body;
    if (build_status === 'failed') {
      await notify(`❌ *Job échoué*\n• Projet: ${project_name}\n• Étape: \`${build_stage}\`\n• Job: ${build_name}`);
    }
  }
});

// ─────────────────────────────────────────────
//  Démarrage
// ─────────────────────────────────────────────
app.listen(PORT, () => {
  const provider = MISTRAL_API_KEY ? `Mistral (${MISTRAL_MODEL})` : ANTHROPIC_API_KEY ? 'Claude (Anthropic)' : '⚠️  AUCUN LLM configuré';
  console.log(`🤖 Agent IA DevSecOps démarré sur le port ${PORT}`);
  console.log(`🧠 Fournisseur IA actif: ${provider}`);
  console.log(`🔗 Health: http://localhost:${PORT}/health`);
});
