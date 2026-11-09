#!/usr/bin/env bash
# Run on the Mac: build the web app, copy everything to the server, then rebuild and
# restart the containers there. The server's .env is created once by hand (see DEPLOY.md).
set -euo pipefail

SERVER="roya@198.44.107.7"
REMOTE_DIR="audio-guide"  # inside roya's home folder on the server

cd "$(dirname "$0")/.."

echo "==> Building the web app"
(cd web && npm ci --no-audit --no-fund && npm run build)

echo "==> Copying files to $SERVER:~/$REMOTE_DIR"
# -R keeps the paths as given (web/dist stays web/dist). --delete removes files that were
# deleted locally, but only inside these folders; excluded files such as .env are never touched.
rsync -azR --delete \
  --exclude .env --exclude .venv --exclude __pycache__ --exclude .pytest_cache --exclude media \
  backend db web/dist scripts Caddyfile docker-compose.prod.yml \
  "$SERVER:$REMOTE_DIR/"

echo "==> Rebuilding and restarting the containers"
ssh "$SERVER" "cd $REMOTE_DIR \
  && docker compose -f docker-compose.prod.yml up -d --build --remove-orphans \
  && docker image prune -f"

echo "==> Done: https://audioguide.royaarkh.com"
