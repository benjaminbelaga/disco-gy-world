#!/bin/bash
# DiscoWorld deploy to Contabo (world.yoyaku.io)
# Usage: ./scripts/deploy.sh
set -euo pipefail

REMOTE="yoyaku-server"
REMOTE_PATH="/var/www/world.yoyaku.io"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=== Building frontend ==="
cd packages/web && npm run build && cd "$PROJECT_ROOT"

echo "=== Ensuring remote directories ==="
ssh ${REMOTE} "mkdir -p ${REMOTE_PATH}/packages/api ${REMOTE_PATH}/packages/pipeline ${REMOTE_PATH}/data"

echo "=== Syncing packages/__init__.py ==="
rsync -avz packages/__init__.py ${REMOTE}:${REMOTE_PATH}/packages/

echo "=== Syncing API ==="
rsync -avz --delete \
  --exclude='__pycache__' \
  --exclude='.env' \
  --exclude='Dockerfile' \
  --exclude='tests/' \
  packages/api/ ${REMOTE}:${REMOTE_PATH}/packages/api/

echo "=== Syncing built frontend (to root, not dist/) ==="
rsync -avz \
  --exclude='data/' \
  packages/web/dist/ ${REMOTE}:${REMOTE_PATH}/

echo "=== Syncing static data files ==="
rsync -avz \
  packages/web/public/data/ ${REMOTE}:${REMOTE_PATH}/data/

echo "=== Syncing database (if exists) ==="
[ -f data/discoworld.db ] && rsync -avz data/discoworld.db ${REMOTE}:${REMOTE_PATH}/data/ || echo "  No local DB, skipping"

echo "=== Syncing PM2 config ==="
rsync -avz ecosystem.config.cjs ${REMOTE}:${REMOTE_PATH}/

echo "=== Installing API dependencies ==="
ssh ${REMOTE} "pip3 install fastapi uvicorn httpx requests requests-oauthlib pydantic 2>/dev/null || true"

echo "=== Restarting API ==="
ssh ${REMOTE} "cd ${REMOTE_PATH} && pm2 delete discoworld-api 2>/dev/null; pm2 start ecosystem.config.cjs"

echo "=== Health check ==="
sleep 3
curl -sf https://world.yoyaku.io/api/health && echo
curl -sf https://world.yoyaku.io/api/stats | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"genreCount\"]} genres, {d[\"sceneCount\"]} scenes')" 2>/dev/null || echo "Stats endpoint not available yet"

echo "=== Deploy complete ==="
