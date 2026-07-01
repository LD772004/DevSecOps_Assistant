FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev --ignore-scripts

FROM node:20-alpine AS runtime
RUN addgroup -g 1001 -S appgroup && adduser -u 1001 -S appuser -G appgroup
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --chown=appuser:appgroup . .
RUN mkdir -p /var/log && chown appuser:appgroup /var/log
USER appuser
ENV NODE_ENV=production NODE_OPTIONS="--max-old-space-size=256"
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD node -e "process.exit(0)"
CMD ["node", "bot.js"]
