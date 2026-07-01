

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         TELEGRAM USER                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │ /run_pipeline /scan /deploy ...
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TELEGRAM BOT (bot.js)                       │
│  • Authentification utilisateurs                                 │
│  • Commandes: /start /status /run_pipeline /scan /deploy /logs  │
│  • Boutons inline (confirmation déploiement prod)               │
│  • Polling statut pipeline (notifications automatiques)         │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT IA (server.js)                        │
│  • API Express (Node.js)                                        │
│  • Intégration Claude (Anthropic)                               │
│  • Orchestration des scans sécurité                             │
│  • Rapport de sécurité avec recommandations IA                  │
│  • Réception webhooks GitLab                                    │
└────┬────────────────────┬───────────────────┬────────────────────┘
     │                    │                   │
     ▼                    ▼                   ▼
┌─────────┐     ┌──────────────────┐    ┌──────────────┐
│ GitLab  │     │  Outils sécurité │    │ Claude (IA)  │
│ CI/CD   │     │  • Semgrep SAST  │    │ Anthropic    │
│ API v4  │     │  • npm audit     │    │ API          │
│         │     │  • Trivy Docker  │    └──────────────┘
└─────────┘     │  • Gitleaks      │
                └──────────────────┘
```

---

## Fonctionnalités

### 🎛️ Contrôle du pipeline (Telegram)

| Commande | Description |
|----------|-------------|
| `/status` | Statut du dernier pipeline + historique |
| `/run_pipeline [branche]` | Déclencher un pipeline GitLab |
| `/stop_pipeline` | Annuler le pipeline en cours |
| `/retry_pipeline` | Relancer le pipeline échoué |
| `/logs` | Logs du dernier job CI/CD |

### 🔒 Sécurité DevSecOps

| Commande | Outil | Description |
|----------|-------|-------------|
| `/scan` | Tous | Scan complet via pipeline GitLab |
| `/scan_sast` | Semgrep | Analyse statique du code |
| `/scan_deps` | npm audit | Vulnérabilités dépendances |
| `/scan_docker` | Trivy | Scan image Docker |
| `/scan_secrets` | Gitleaks | Détection secrets exposés |
| `/report` | Claude AI | Rapport complet + recommandations IA |

### 🚀 Déploiement

| Commande | Description |
|----------|-------------|
| `/deploy staging` | Déployer sur staging |
| `/deploy production` | Déployer en prod (confirmation requise) |
| `/rollback` | Revenir à la version précédente |

### 🤖 Intelligence Artificielle

| Commande | Description |
|----------|-------------|
| `/ask [question]` | Interroger Claude (contexte GitLab enrichi) |

---

## Pipeline GitLab CI/CD

```
build → test → sast → dependency_scanning → container_scanning → secret_detection → deploy → notify
```

### Étapes

1. **Build** — Compilation app + image Docker
2. **Test** — Tests unitaires + linting
3. **SAST** — Semgrep + GitLab SAST (Bandit, ESLint Security)
4. **Dependency Scanning** — npm audit + GitLab Dependency Scanning
5. **Container Scanning** — Trivy + GitLab Container Scanning
6. **Secret Detection** — Gitleaks + GitLab Secret Detection
7. **Deploy** — Staging (auto) / Production (manuel ou via Telegram)
8. **Notify** — Notifications Telegram succès/échec/alertes sécurité

---

## Notifications automatiques

Le bot envoie automatiquement :

- ✅ Pipeline réussi
- ❌ Pipeline échoué (avec lien vers les logs)
- 🔴 Alerte sécurité (vulnérabilités critiques / secrets détectés)
- 🚀 Déploiement terminé
- ⏪ Rollback effectué

---

## Technologies

- **Bot Telegram** : `node-telegram-bot-api`
- **Agent IA** : Express.js + Claude (Anthropic)
- **CI/CD** : GitLab CI/CD avec templates Security
- **SAST** : Semgrep
- **Container** : Trivy (Aqua Security)
- **Secrets** : Gitleaks
- **Monitoring** : Prometheus + Grafana
- **Déploiement** : Docker / Docker Compose

---

## Installation rapide

```bash
cp .env.example .env
# Remplir les variables dans .env
docker compose -f deployment/docker-compose.yml up -d
```

Voir [docs/INSTALL.md](docs/INSTALL.md) pour le guide complet.

# DevSecOps_Assistant
