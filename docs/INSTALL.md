# 🚀 Guide d'Installation — Agent DevSecOps Telegram

## Prérequis

| Outil | Version minimale | Vérification |
|-------|-----------------|--------------|
| Docker | 24.x | `docker --version` |
| Docker Compose | 2.x | `docker compose version` |
| Node.js (dev) | 20.x | `node --version` |
| Git | 2.x | `git --version` |

---

## 1. Cloner / Récupérer le projet

```bash
git clone https://gitlab.com/votre-namespace/devsecops-agent.git
cd devsecops-agent
```

---

## 2. Créer votre bot Telegram

1. Ouvrez Telegram et cherchez **@BotFather**
2. Tapez `/newbot` et suivez les instructions
3. Notez le **Token** fourni (format: `1234567890:AAAA...`)
4. Récupérez votre **Chat ID** via [@userinfobot](https://t.me/userinfobot)

---

## 3. Configurer les variables d'environnement

```bash
cp .env.example .env
nano .env   # ou votre éditeur préféré
```

Remplissez **obligatoirement** :

```env
TELEGRAM_TOKEN=votre_token_botfather
TELEGRAM_CHAT_ID=votre_chat_id
GITLAB_TOKEN=glpat-votre_token_gitlab
GITLAB_PROJECT_ID=12345678
ANTHROPIC_API_KEY=sk-ant-votre_cle_anthropic
```

### Obtenir un token GitLab

1. Gitlab → **Settings** → **Access Tokens**
2. Créer un token avec les scopes : `api`, `read_api`, `read_repository`
3. Copier le token dans `.env`

### Obtenir une clé Anthropic

1. [console.anthropic.com](https://console.anthropic.com)
2. **API Keys** → **Create Key**
3. Copier dans `.env`

---

## 4. Configurer les variables CI/CD GitLab

Dans votre projet GitLab : **Settings → CI/CD → Variables**

| Variable | Description | Masquée |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Token du bot | ✅ |
| `TELEGRAM_CHAT_ID` | Chat ID notifications | ✅ |
| `CI_REGISTRY_USER` | Username GitLab Registry | Non |
| `CI_REGISTRY_PASSWORD` | Mot de passe Registry | ✅ |

> Les variables `CI_REGISTRY_*` et `CI_PIPELINE_URL` sont injectées automatiquement par GitLab.

---

## 5. Configurer le Webhook GitLab (optionnel mais recommandé)

1. GitLab → **Settings → Webhooks**
2. URL: `https://votre-serveur.com:3000/webhook/gitlab`
3. Secret: valeur de `GITLAB_WEBHOOK_SECRET` dans `.env`
4. Événements: ✅ Pipeline events, ✅ Job events

---

## 6. Lancer la stack

```bash
# Mode production (détaché)
docker compose -f deployment/docker-compose.yml up -d

# Vérifier le démarrage
docker compose -f deployment/docker-compose.yml ps
docker compose -f deployment/docker-compose.yml logs -f
```

### Vérifier que tout fonctionne

```bash
# Santé de l'agent IA
curl http://localhost:3000/health

# Logs du bot Telegram
docker logs telegram-bot -f
```

---

## 7. Tester sur Telegram

Ouvrez votre bot Telegram et tapez :
- `/start` — Message de bienvenue
- `/status` — Statut du dernier pipeline GitLab
- `/help` — Liste des commandes

---

## 8. Activer le pipeline GitLab

Copiez `.gitlab-ci.yml` à la racine de votre projet applicatif :

```bash
cp gitlab-ci/.gitlab-ci.yml /chemin/vers/votre-projet/.gitlab-ci.yml
```

Puis adaptez selon votre stack applicative (remplacer `npm` par votre outil de build).

---

## Structure des fichiers

```
DevSecOpsAgent/
├── .env.example              # Template variables d'environnement
├── telegram-bot/
│   ├── bot.js               # ✅ Bot Telegram complet
│   ├── package.json
│   └── Dockerfile
├── agent-ia/
│   ├── server.js            # ✅ API Agent IA (Express + Claude)
│   ├── config.js            # ✅ Configuration centralisée
│   ├── package.json
│   └── Dockerfile
├── gitlab-ci/
│   └── .gitlab-ci.yml       # ✅ Pipeline DevSecOps complet
├── deployment/
│   ├── docker-compose.yml   # ✅ Stack complète
│   ├── Dockerfile           # (bot)
│   └── prometheus.yml       # Monitoring
└── security-tools/
    ├── sast-config.yml      # ✅ Règles Semgrep
    ├── dependency-scan.yml  # ✅ Politique dépendances
    ├── docker-scan.yml      # ✅ Config Trivy
    └── secrets-scan.yml     # ✅ Config Gitleaks
```

---

## Commandes utiles

```bash
# Redémarrer un service
docker compose restart telegram-bot

# Voir les logs en temps réel
docker compose logs -f agent-ia

# Arrêter la stack
docker compose down

# Mettre à jour et redéployer
git pull && docker compose build && docker compose up -d
```

---

## Dépannage

### Le bot ne répond pas
- Vérifiez `TELEGRAM_TOKEN` dans `.env`
- `docker logs telegram-bot` pour voir les erreurs

### Erreur 401 GitLab
- Le `GITLAB_TOKEN` est invalide ou expiré
- Vérifiez les scopes (`api`, `read_api`)

### L'agent IA ne démarre pas
- Vérifiez `ANTHROPIC_API_KEY`
- `docker logs agent-ia` pour le détail

### Pipeline GitLab échoue sur les scans
- Les templates GitLab Security nécessitent GitLab Ultimate/Gold
- En version Free: utilisez les jobs manuels (`scan:semgrep`, `scan:trivy`, etc.)
