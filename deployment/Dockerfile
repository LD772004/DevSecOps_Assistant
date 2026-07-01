# ═══════════════════════════════════════════════════════════
#  Dockerfile — Telegram Bot DevSecOps
# ═══════════════════════════════════════════════════════════

# Étape 1 : build
FROM node:20-alpine AS builder

WORKDIR /app

# Dépendances d'abord (cache Docker layer)
COPY package*.json ./
RUN npm ci --omit=dev --ignore-scripts

# ─────────────────────────────────────────────
# Étape 2 : runtime minimal
# ─────────────────────────────────────────────
FROM node:20-alpine AS runtime

# Sécurité : utilisateur non-root
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

WORKDIR /app

# Copie depuis le builder
COPY --from=builder /app/node_modules ./node_modules
COPY --chown=appuser:appgroup . .

# Dossier logs
RUN mkdir -p /var/log && chown appuser:appgroup /var/log

# Passer en utilisateur non-root
USER appuser

# Variables d'environnement par défaut
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=256"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD node -e "process.exit(0)"

CMD ["node", "bot.js"]
