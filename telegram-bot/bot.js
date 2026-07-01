require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const bot = new TelegramBot(process.env.TELEGRAM_TOKEN, { polling: true });

// ─────────────────────────────────────────────
//  Configuration centrale
// ─────────────────────────────────────────────
const GITLAB_API = 'https://gitlab.com/api/v4';
const PROJECT_ID = process.env.GITLAB_PROJECT_ID;
const GITLAB_HEADERS = { 'PRIVATE-TOKEN': process.env.GITLAB_TOKEN };
const AGENT_URL = process.env.AGENT_URL || 'http://agent-ia:3000';
const ALLOWED_USERS = process.env.ALLOWED_TELEGRAM_USERS
  ? process.env.ALLOWED_TELEGRAM_USERS.split(',').map(Number)
  : [];

// ─────────────────────────────────────────────
//  Middleware : contrôle d'accès
// ─────────────────────────────────────────────
function isAllowed(userId) {
  if (ALLOWED_USERS.length === 0) return true;
  return ALLOWED_USERS.includes(userId);
}

function guard(msg, fn) {
  if (!isAllowed(msg.from.id)) {
    bot.sendMessage(msg.chat.id, '🚫 Accès refusé. Vous n\'êtes pas autorisé à utiliser ce bot.');
    return;
  }
  fn();
}

// ─────────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────────
function statusEmoji(status) {
  const map = {
    success: '✅', failed: '❌', running: '🔄', pending: '⏳',
    canceled: '⛔', skipped: '⏭️', manual: '🔧', created: '🆕',
  };
  return map[status] || '❓';
}

async function gitlabGet(path) {
  const res = await axios.get(`${GITLAB_API}${path}`, { headers: GITLAB_HEADERS });
  return res.data;
}

async function gitlabPost(path, data = {}) {
  const res = await axios.post(`${GITLAB_API}${path}`, data, { headers: GITLAB_HEADERS });
  return res.data;
}

async function gitlabDelete(path) {
  const res = await axios.delete(`${GITLAB_API}${path}`, { headers: GITLAB_HEADERS });
  return res.data;
}

async function agentQuery(endpoint, payload = {}) {
  const res = await axios.post(`${AGENT_URL}${endpoint}`, payload, { timeout: 30000 });
  return res.data;
}

// ✅ FIX: regex corrigée — les sauts de ligne dans la classe de caractères étaient invalides
function escapeMarkdown(text) {
  if (typeof text !== 'string') return text;
  return text.replace(/([_*[\]()~`>#+\-=|{}.!])/g, '\\$1');
}

// Nettoie le Markdown de Mistral/Claude pour Telegram
function cleanForTelegram(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '*$1*')
    .replace(/#{1,6}\s+(.+)/g, '*$1*')
    .replace(/`{3}[\w]*\n?([\s\S]*?)`{3}/g, '`$1`')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1')
    .replace(/^\s*[-*]\s+/gm, '• ')
    .trim();
}

// ─────────────────────────────────────────────
//  /start
// ─────────────────────────────────────────────
bot.onText(/\/start/, (msg) => {
  guard(msg, () => {
    const name = msg.from.first_name || 'utilisateur';
    bot.sendMessage(msg.chat.id, `
🤖 *Agent DevSecOps — Bienvenue, ${name} !*

Je contrôle votre pipeline DevSecOps complet depuis Telegram.

📋 *Commandes disponibles :*

*Pipeline CI/CD*
/status — État du dernier pipeline
/run\\_pipeline — Déclencher un pipeline
/stop\\_pipeline — Arrêter le pipeline en cours
/retry\\_pipeline — Relancer le pipeline
/logs — Logs du dernier job

*Sécurité*
/scan — Scan sécurité complet (SAST + dépendances + Docker + secrets)
/scan\\_sast — Scan SAST uniquement (Semgrep)
/scan\\_deps — Scan des dépendances (npm audit)
/scan\\_docker — Scan image Docker (Trivy)
/scan\\_secrets — Détection de secrets (Gitleaks)
/report — Rapport de sécurité complet

*Déploiement*
/deploy — Déployer l'application
/rollback — Rollback vers la version précédente

*IA*
/ask [question] — Demander à l'agent IA

/help — Afficher cette aide
`, { parse_mode: 'Markdown' });
  });
});

// ─────────────────────────────────────────────
//  /help
// ─────────────────────────────────────────────
bot.onText(/\/help/, (msg) => {
  guard(msg, () => {
    bot.sendMessage(msg.chat.id, `
ℹ️ *Aide — Agent DevSecOps*

*Pipeline*
• \`/status\` → Statut du dernier pipeline GitLab
• \`/run_pipeline [branche]\` → Lance un pipeline (défaut: main)
• \`/stop_pipeline\` → Annule le pipeline en cours
• \`/retry_pipeline\` → Relance le dernier pipeline échoué
• \`/logs\` → Logs du dernier job CI/CD

*Sécurité*
• \`/scan\` → Lance tous les scans de sécurité
• \`/scan_sast\` → Analyse statique du code (Semgrep)
• \`/scan_deps\` → Vulnérabilités des dépendances
• \`/scan_docker\` → Scan de l'image Docker (Trivy)
• \`/scan_secrets\` → Détection de secrets exposés
• \`/report\` → Rapport de sécurité complet

*Déploiement*
• \`/deploy [env]\` → Déploie sur staging ou production
• \`/rollback\` → Revenir à la version précédente

*IA*
• \`/ask [question]\` → Interroger l'agent IA

⚠️ _Toutes les actions critiques sont journalisées._
`, { parse_mode: 'Markdown' });
  });
});

// ─────────────────────────────────────────────
//  /status
// ─────────────────────────────────────────────
bot.onText(/\/status/, async (msg) => {
  guard(msg, async () => {
    try {
      bot.sendMessage(msg.chat.id, '⏳ Récupération du statut…');
      const [pipelines, project] = await Promise.all([
        gitlabGet(`/projects/${PROJECT_ID}/pipelines?per_page=3`),
        gitlabGet(`/projects/${PROJECT_ID}`),
      ]);

      const p = pipelines[0];
      const duration = p.duration ? `${Math.round(p.duration / 60)}m ${p.duration % 60}s` : 'N/A';
      const created = new Date(p.created_at).toLocaleString('fr-FR');

      let text = `📊 *Statut Pipeline — ${project.name}*\n\n`;
      text += `${statusEmoji(p.status)} *Dernier pipeline*\n`;
      text += `• ID: \`${p.id}\`\n`;
      text += `• Statut: \`${p.status}\`\n`;
      text += `• Branche: \`${p.ref}\`\n`;
      text += `• Créé: ${created}\n`;
      text += `• Durée: ${duration}\n`;
      text += `• [Voir sur GitLab](${p.web_url})\n\n`;

      if (pipelines.length > 1) {
        text += `*Historique récent :*\n`;
        pipelines.slice(1).forEach(pp => {
          text += `${statusEmoji(pp.status)} #${pp.id} \`${pp.ref}\` — ${pp.status}\n`;
        });
      }

      bot.sendMessage(msg.chat.id, text, { parse_mode: 'Markdown', disable_web_page_preview: true });
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur: ${err.response?.data?.message || err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /run_pipeline [branche]
// ─────────────────────────────────────────────
bot.onText(/\/run_pipeline(.*)/, async (msg, match) => {
  guard(msg, async () => {
    const branch = match[1]?.trim() || 'main';
    try {
      bot.sendMessage(msg.chat.id, `🚀 Déclenchement du pipeline sur \`${branch}\`…`, { parse_mode: 'Markdown' });
      const pipeline = await gitlabPost(`/projects/${PROJECT_ID}/pipeline`, { ref: branch });
      bot.sendMessage(msg.chat.id,
        `✅ *Pipeline déclenché !*\n\n• ID: \`${pipeline.id}\`\n• Branche: \`${pipeline.ref}\`\n• Statut: \`${pipeline.status}\`\n• [Suivre sur GitLab](${pipeline.web_url})`,
        { parse_mode: 'Markdown', disable_web_page_preview: true }
      );
      pollPipelineStatus(msg.chat.id, pipeline.id);
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur lancement: ${err.response?.data?.message || err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /stop_pipeline
// ─────────────────────────────────────────────
bot.onText(/\/stop_pipeline/, async (msg) => {
  guard(msg, async () => {
    try {
      const pipelines = await gitlabGet(`/projects/${PROJECT_ID}/pipelines?status=running`);
      if (!pipelines.length) {
        bot.sendMessage(msg.chat.id, '⚠️ Aucun pipeline en cours d\'exécution.');
        return;
      }
      const p = pipelines[0];
      await gitlabPost(`/projects/${PROJECT_ID}/pipelines/${p.id}/cancel`);
      bot.sendMessage(msg.chat.id, `⛔ *Pipeline #${p.id} annulé* (branche: \`${p.ref}\`)`, { parse_mode: 'Markdown' });
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur arrêt: ${err.response?.data?.message || err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /retry_pipeline
// ─────────────────────────────────────────────
bot.onText(/\/retry_pipeline/, async (msg) => {
  guard(msg, async () => {
    try {
      const pipelines = await gitlabGet(`/projects/${PROJECT_ID}/pipelines?status=failed&per_page=1`);
      if (!pipelines.length) {
        bot.sendMessage(msg.chat.id, '⚠️ Aucun pipeline échoué à relancer.');
        return;
      }
      const p = pipelines[0];
      const retried = await gitlabPost(`/projects/${PROJECT_ID}/pipelines/${p.id}/retry`);
      bot.sendMessage(msg.chat.id,
        `🔄 *Pipeline relancé !*\n• Ancien ID: \`${p.id}\`\n• Nouveau ID: \`${retried.id}\`\n• [Suivre](${retried.web_url})`,
        { parse_mode: 'Markdown', disable_web_page_preview: true }
      );
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur relance: ${err.response?.data?.message || err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /logs
// ─────────────────────────────────────────────
bot.onText(/\/logs/, async (msg) => {
  guard(msg, async () => {
    try {
      bot.sendMessage(msg.chat.id, '📥 Récupération des logs…');
      const jobs = await gitlabGet(`/projects/${PROJECT_ID}/jobs?per_page=5`);
      if (!jobs.length) {
        bot.sendMessage(msg.chat.id, '⚠️ Aucun job trouvé.');
        return;
      }

      const job = jobs[0];
      let text = `📜 *Dernier job: ${escapeMarkdown(job.name)}*\n`;
      text += `• Statut: ${statusEmoji(job.status)} ${escapeMarkdown(job.status)}\n`;
      text += `• Étape: ${escapeMarkdown(job.stage)}\n`;
      text += `• Durée: ${job.duration ? Math.round(job.duration) + 's' : 'N/A'}\n`;
      text += `• [Voir les logs complets](${job.web_url})\n\n`;
      text += `*5 derniers jobs :*\n`;
      jobs.forEach(j => {
        text += `${statusEmoji(j.status)} ${escapeMarkdown(j.stage)} → ${escapeMarkdown(j.name)}\n`;
      });

      bot.sendMessage(msg.chat.id, text, { parse_mode: 'Markdown', disable_web_page_preview: true });

      // ✅ FIX: GITLAB_PROJECT_ID → PROJECT_ID (variable inexistante corrigée)
      try {
        const trace = await axios.get(
          `${GITLAB_API}/projects/${PROJECT_ID}/jobs/${job.id}/trace`,
          { headers: GITLAB_HEADERS }
        );
        const lines = trace.data.split('\n').slice(-30).join('\n');
        if (lines.trim()) {
          bot.sendMessage(
            msg.chat.id,
            `\`\`\`\n${lines.slice(0, 3800)}\n\`\`\``,
            { parse_mode: 'Markdown' }
          );
        }
      } catch (_) {
        // trace non disponible
      }
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur logs: ${err.response?.data?.message || err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /scan (tous les scans en parallèle)
// ✅ FIX: commande manquante — présente dans /start et /help mais non implémentée
// ─────────────────────────────────────────────
bot.onText(/\/scan$/, async (msg) => {
  guard(msg, async () => {
    bot.sendMessage(msg.chat.id, '🔍 *Scan sécurité complet démarré…* (SAST + Dépendances + Docker + Secrets)', { parse_mode: 'Markdown' });
    try {
      const [sast, deps, docker, secrets] = await Promise.allSettled([
        agentQuery('/scan/sast', { project_id: PROJECT_ID }),
        agentQuery('/scan/deps', { project_id: PROJECT_ID }),
        agentQuery('/scan/docker', { project_id: PROJECT_ID }),
        agentQuery('/scan/secrets', { project_id: PROJECT_ID }),
      ]);

      const results = { sast, deps, docker, secrets };
      const labels = { sast: 'SAST (Semgrep)', deps: 'Dépendances', docker: 'Docker (Trivy)', secrets: 'Secrets (Gitleaks)' };

      for (const [key, settled] of Object.entries(results)) {
        if (settled.status === 'fulfilled') {
          formatScanResult(msg.chat.id, labels[key], settled.value);
        } else {
          bot.sendMessage(msg.chat.id, `❌ Erreur scan ${labels[key]}: ${settled.reason.message}`);
        }
      }
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur scan complet: ${err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /scan_sast
// ─────────────────────────────────────────────
bot.onText(/\/scan_sast/, async (msg) => {
  guard(msg, async () => {
    bot.sendMessage(msg.chat.id, '🔬 *Scan SAST (Semgrep) démarré…*', { parse_mode: 'Markdown' });
    try {
      const result = await agentQuery('/scan/sast', { project_id: PROJECT_ID });
      formatScanResult(msg.chat.id, 'SAST (Semgrep)', result);
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur SAST: ${err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /scan_deps
// ─────────────────────────────────────────────
bot.onText(/\/scan_deps/, async (msg) => {
  guard(msg, async () => {
    bot.sendMessage(msg.chat.id, '📦 *Scan des dépendances démarré…*', { parse_mode: 'Markdown' });
    try {
      const result = await agentQuery('/scan/deps', { project_id: PROJECT_ID });
      formatScanResult(msg.chat.id, 'Dépendances', result);
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur scan deps: ${err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /scan_docker
// ─────────────────────────────────────────────
bot.onText(/\/scan_docker/, async (msg) => {
  guard(msg, async () => {
    bot.sendMessage(msg.chat.id, '🐳 *Scan Docker (Trivy) démarré…*', { parse_mode: 'Markdown' });
    try {
      const result = await agentQuery('/scan/docker', { project_id: PROJECT_ID });
      formatScanResult(msg.chat.id, 'Docker (Trivy)', result);
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur scan Docker: ${err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /scan_secrets
// ─────────────────────────────────────────────
bot.onText(/\/scan_secrets/, async (msg) => {
  guard(msg, async () => {
    bot.sendMessage(msg.chat.id, '🔑 *Scan des secrets (Gitleaks) démarré…*', { parse_mode: 'Markdown' });
    try {
      const result = await agentQuery('/scan/secrets', { project_id: PROJECT_ID });
      formatScanResult(msg.chat.id, 'Secrets (Gitleaks)', result);
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur scan secrets: ${err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /report
// ─────────────────────────────────────────────
bot.onText(/\/report/, async (msg) => {
  guard(msg, async () => {
    bot.sendMessage(msg.chat.id, '📋 *Génération du rapport de sécurité…*', { parse_mode: 'Markdown' });
    try {
      const report = await agentQuery('/report', { project_id: PROJECT_ID });
      bot.sendMessage(msg.chat.id, formatFullReport(report), { parse_mode: 'Markdown' });
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur rapport: ${err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  /deploy [env]
// ─────────────────────────────────────────────
bot.onText(/\/deploy(.*)/, async (msg, match) => {
  guard(msg, async () => {
    const env = match[1]?.trim() || 'staging';
    if (!['staging', 'production'].includes(env)) {
      bot.sendMessage(msg.chat.id, '⚠️ Environnement invalide. Utilisez: `staging` ou `production`', { parse_mode: 'Markdown' });
      return;
    }

    if (env === 'production') {
      const keyboard = {
        inline_keyboard: [[
          { text: '✅ Confirmer déploiement PRODUCTION', callback_data: `deploy_confirm_production` },
          { text: '❌ Annuler', callback_data: 'deploy_cancel' },
        ]],
      };
      bot.sendMessage(msg.chat.id,
        `⚠️ *Attention!* Vous êtes sur le point de déployer en *PRODUCTION*.\nÊtes-vous sûr?`,
        { parse_mode: 'Markdown', reply_markup: keyboard }
      );
      return;
    }

    await executeDeploy(msg.chat.id, env);
  });
});

// ─────────────────────────────────────────────
//  /rollback
// ─────────────────────────────────────────────
bot.onText(/\/rollback/, async (msg) => {
  guard(msg, async () => {
    const keyboard = {
      inline_keyboard: [[
        { text: '✅ Confirmer rollback', callback_data: 'rollback_confirm' },
        { text: '❌ Annuler', callback_data: 'deploy_cancel' },
      ]],
    };
    bot.sendMessage(msg.chat.id,
      `⚠️ *Rollback demandé*\nCela va revenir à la version précédente. Confirmer?`,
      { parse_mode: 'Markdown', reply_markup: keyboard }
    );
  });
});

// ─────────────────────────────────────────────
//  /ask [question]
// ─────────────────────────────────────────────
bot.onText(/\/ask (.+)/, async (msg, match) => {
  guard(msg, async () => {
    const question = match[1];
    bot.sendMessage(msg.chat.id, '🤖 *Agent IA en cours de réflexion…*', { parse_mode: 'Markdown' });
    try {
      const result = await agentQuery('/ask', { question, user_id: msg.from.id });
      const cleaned = cleanForTelegram(result.answer);
      bot.sendMessage(msg.chat.id, `🤖 Réponse de l'agent IA:\n\n${cleaned}`);
    } catch (err) {
      bot.sendMessage(msg.chat.id, `❌ Erreur agent IA: ${err.message}`);
    }
  });
});

// ─────────────────────────────────────────────
//  Callbacks boutons inline
// ─────────────────────────────────────────────
bot.on('callback_query', async (query) => {
  const chatId = query.message.chat.id;
  const data = query.data;
  bot.answerCallbackQuery(query.id);

  if (data.startsWith('deploy_confirm_')) {
    const env = data.replace('deploy_confirm_', '');
    await executeDeploy(chatId, env);
  } else if (data === 'rollback_confirm') {
    await executeRollback(chatId);
  } else if (data === 'deploy_cancel') {
    bot.sendMessage(chatId, '❌ Opération annulée.');
  }
});

// ─────────────────────────────────────────────
//  Fonctions utilitaires internes
// ─────────────────────────────────────────────
async function executeDeploy(chatId, env) {
  bot.sendMessage(chatId, `🚀 *Déploiement sur ${env.toUpperCase()} en cours…*`, { parse_mode: 'Markdown' });
  try {
    const pipeline = await gitlabPost(`/projects/${PROJECT_ID}/pipeline`, {
      ref: 'main',
      variables: [
        { key: 'DEPLOY_ENV', value: env },
        { key: 'MANUAL_DEPLOY', value: 'true' },
      ],
    });
    bot.sendMessage(chatId,
      `✅ *Déploiement lancé sur ${env.toUpperCase()}*\n• Pipeline ID: \`${pipeline.id}\`\n• [Suivre](${pipeline.web_url})`,
      { parse_mode: 'Markdown', disable_web_page_preview: true }
    );
    pollPipelineStatus(chatId, pipeline.id);
  } catch (err) {
    bot.sendMessage(chatId, `❌ Erreur déploiement: ${err.response?.data?.message || err.message}`);
  }
}

async function executeRollback(chatId) {
  bot.sendMessage(chatId, '⏪ *Rollback en cours…*', { parse_mode: 'Markdown' });
  try {
    const pipeline = await gitlabPost(`/projects/${PROJECT_ID}/pipeline`, {
      ref: 'main',
      variables: [{ key: 'ROLLBACK', value: 'true' }],
    });
    bot.sendMessage(chatId,
      `✅ *Rollback lancé !*\n• Pipeline ID: \`${pipeline.id}\`\n• [Suivre](${pipeline.web_url})`,
      { parse_mode: 'Markdown', disable_web_page_preview: true }
    );
  } catch (err) {
    bot.sendMessage(chatId, `❌ Erreur rollback: ${err.message}`);
  }
}

function formatScanResult(chatId, scanType, result) {
  const { critical = 0, high = 0, medium = 0, low = 0, info = 0, details = [] } = result;
  const total = critical + high + medium + low;
  const level = critical > 0 ? '🔴 CRITIQUE' : high > 0 ? '🟠 ÉLEVÉ' : medium > 0 ? '🟡 MOYEN' : '🟢 OK';

  let text = `🔍 *Résultats du scan ${scanType}*\n\n`;
  text += `Niveau global: ${level}\n\n`;
  text += `• 🔴 Critique: ${critical}\n`;
  text += `• 🟠 Élevé: ${high}\n`;
  text += `• 🟡 Moyen: ${medium}\n`;
  text += `• 🔵 Faible: ${low}\n`;
  text += `• ℹ️ Info: ${info}\n`;
  text += `• Total: ${total} vulnérabilité(s)\n`;

  if (details.length > 0) {
    text += `\n*Top vulnérabilités :*\n`;
    details.slice(0, 5).forEach(v => {
      text += `• [${v.severity}] ${v.title} — ${v.location || ''}\n`;
    });
  }

  bot.sendMessage(chatId, text, { parse_mode: 'Markdown' });
}

function formatFullReport(report) {
  const { generated_at, summary, recommendations } = report;
  let text = `📋 *Rapport de sécurité DevSecOps*\n`;
  text += `_Généré le: ${new Date(generated_at).toLocaleString('fr-FR')}_\n\n`;
  text += `*Résumé :*\n`;
  text += `• Pipeline: ${statusEmoji(summary.pipeline_status)} ${summary.pipeline_status}\n`;
  text += `• Vulnérabilités critiques: ${summary.critical}\n`;
  text += `• Vulnérabilités élevées: ${summary.high}\n`;
  text += `• Secrets exposés: ${summary.secrets}\n`;
  text += `• Score de sécurité: ${summary.score}/100\n\n`;
  if (recommendations?.length > 0) {
    text += `*Recommandations :*\n`;
    recommendations.slice(0, 5).forEach((r, i) => {
      text += `${i + 1}. ${r}\n`;
    });
  }
  return text;
}

// Polling du statut pipeline avec notifications automatiques
function pollPipelineStatus(chatId, pipelineId) {
  let attempts = 0;
  const maxAttempts = 40;
  const interval = setInterval(async () => {
    attempts++;
    if (attempts > maxAttempts) {
      clearInterval(interval);
      bot.sendMessage(chatId, `⚠️ Timeout: le pipeline #${pipelineId} prend trop de temps.`);
      return;
    }
    try {
      const pipeline = await gitlabGet(`/projects/${PROJECT_ID}/pipelines/${pipelineId}`);
      const terminal = ['success', 'failed', 'canceled', 'skipped'];
      if (terminal.includes(pipeline.status)) {
        clearInterval(interval);
        const emoji = statusEmoji(pipeline.status);
        const duration = pipeline.duration ? `${Math.round(pipeline.duration)}s` : 'N/A';
        if (pipeline.status === 'success') {
          bot.sendMessage(chatId,
            `${emoji} *Pipeline #${pipelineId} terminé avec succès !*\nDurée: ${duration}\n[Voir résultats](${pipeline.web_url})`,
            { parse_mode: 'Markdown', disable_web_page_preview: true }
          );
        } else {
          bot.sendMessage(chatId,
            `${emoji} *Pipeline #${pipelineId} — ${pipeline.status.toUpperCase()}*\nDurée: ${duration}\n[Voir les erreurs](${pipeline.web_url})`,
            { parse_mode: 'Markdown', disable_web_page_preview: true }
          );
        }
      }
    } catch (_) {}
  }, 30000);
}

// Gestion des erreurs polling
bot.on('polling_error', (error) => {
  console.error('[Bot] Erreur polling:', error.message);
});

console.log('🤖 Agent DevSecOps Bot démarré...');
