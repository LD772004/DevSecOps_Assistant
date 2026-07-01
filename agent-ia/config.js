// config.js — Configuration centralisée de l'Agent DevSecOps IA
require('dotenv').config();

module.exports = {
  server: {
    port: parseInt(process.env.PORT || '3000'),
    env: process.env.NODE_ENV || 'production',
  },

  gitlab: {
    apiUrl: 'https://gitlab.com/api/v4',
    token: process.env.GITLAB_TOKEN,
    projectId: process.env.GITLAB_PROJECT_ID,
    webhookSecret: process.env.GITLAB_WEBHOOK_SECRET,
    defaultBranch: process.env.GITLAB_DEFAULT_BRANCH || 'main',
  },

  telegram: {
    token: process.env.TELEGRAM_TOKEN,
    chatId: process.env.TELEGRAM_CHAT_ID,
    allowedUsers: process.env.ALLOWED_TELEGRAM_USERS
      ? process.env.ALLOWED_TELEGRAM_USERS.split(',').map(Number)
      : [],
  },

  // Mistral (priorité) — API Chat Completions standard
  mistral: {
    apiKey: process.env.MISTRAL_API_KEY,
    // Endpoint fixe : /v1/chat/completions (seul endpoint officiel supporté)
    endpoint: 'https://api.mistral.ai/v1/chat/completions',
    // Modèles disponibles: mistral-large-latest, mistral-medium-latest, mistral-small-latest, open-mistral-7b
    model: process.env.MISTRAL_MODEL || 'mistral-large-latest',
    maxTokens: 1024,
    temperature: 0.3,
  },

  // Anthropic / Claude — fallback si Mistral absent
  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY,
    model: 'claude-sonnet-4-20250514',
    maxTokens: 1024,
  },

  docker: {
    image: process.env.DOCKER_IMAGE || 'myapp:latest',
    registry: process.env.DOCKER_REGISTRY || 'registry.gitlab.com',
  },

  security: {
    thresholds: {
      critical: parseInt(process.env.SEC_THRESHOLD_CRITICAL || '0'),
      high: parseInt(process.env.SEC_THRESHOLD_HIGH || '5'),
      medium: parseInt(process.env.SEC_THRESHOLD_MEDIUM || '20'),
    },
    tools: {
      sast: process.env.ENABLE_SAST !== 'false',
      dependencyScanning: process.env.ENABLE_DEPENDENCY_SCANNING !== 'false',
      containerScanning: process.env.ENABLE_CONTAINER_SCANNING !== 'false',
      secretDetection: process.env.ENABLE_SECRET_DETECTION !== 'false',
      dast: process.env.ENABLE_DAST === 'true',
    },
  },

  polling: {
    intervalMs: parseInt(process.env.POLL_INTERVAL_MS || '30000'),
    maxAttempts: parseInt(process.env.POLL_MAX_ATTEMPTS || '40'),
  },
};
