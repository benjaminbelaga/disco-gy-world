#!/bin/bash
# DiscoWorld server setup — run ONCE on Contabo as root
# Usage: ssh yoyaku-server 'bash -s' < scripts/server-setup.sh
set -euo pipefail

APP_DIR="/var/www/world.yoyaku.io"

echo "=== Creating directory structure ==="
mkdir -p ${APP_DIR}/{dist,data,packages/api}

echo "=== Installing Python dependencies ==="
pip3 install --upgrade pip
pip3 install fastapi 'uvicorn[standard]' pydantic httpx aiofiles

echo "=== Verifying PM2 ==="
pm2 --version || npm install -g pm2

echo "=== Setting up nginx ==="
if [ ! -f /etc/nginx/sites-available/world.yoyaku.io ]; then
    echo "Copy nginx config:"
    echo "  scp scripts/nginx-discoworld.conf root@95.111.255.235:/etc/nginx/sites-available/world.yoyaku.io"
    echo "  ssh yoyaku-server 'ln -sf /etc/nginx/sites-available/world.yoyaku.io /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx'"
else
    echo "nginx config already exists"
fi

echo "=== SSL certificate ==="
if [ ! -d /etc/letsencrypt/live/world.yoyaku.io ]; then
    echo "Getting SSL cert..."
    certbot certonly --nginx -d world.yoyaku.io --non-interactive --agree-tos -m ben@yoyaku.fr
else
    echo "SSL cert already exists"
fi

echo "=== Setting permissions ==="
chown -R www-data:www-data ${APP_DIR}

echo "=== Setup complete ==="
echo "Next: run ./scripts/deploy.sh from your local machine"
