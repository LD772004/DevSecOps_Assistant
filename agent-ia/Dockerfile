# ═══════════════════════════════════════════════════════════
#  Dockerfile — Agent IA DevSecOps
# ═══════════════════════════════════════════════════════════

FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev --ignore-scripts

FROM node:20-alpine AS runtime

RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Trivy pour les scans locaux (optionnel)
RUN apk add --no-cache wget curl python3 && \
    wget -q https://github.com/aquasecurity/trivy/releases/download/v0.50.0/trivy_0.50.0_Linux-64bit.tar.gz \
    -O /tmp/trivy.tar.gz && \
    tar -xzf /tmp/trivy.tar.gz -C /usr/local/bin trivy && \
    rm /tmp/trivy.tar.gz || true

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY --chown=appuser:appgroup . .

RUN mkdir -p /var/log && chown appuser:appgroup /var/log

USER appuser

ENV NODE_ENV=production \
    PORT=3000 \
    NODE_OPTIONS="--max-old-space-size=512"

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "server.js"]
