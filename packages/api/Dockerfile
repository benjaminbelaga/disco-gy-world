FROM python:3.11-slim

WORKDIR /app

COPY packages/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Package layout required for main.py's relative imports
# (`from .routes...`), so it must run as `packages.api.main:app`.
COPY packages/__init__.py packages/__init__.py
COPY packages/api packages/api

# Static datasets the API reads at import / runtime.
# world.json (genres) lives under the web package; copy the whole
# data dir so shop/city/label routes find their JSON too.
COPY packages/web/public/data packages/web/public/data

# style_cooccurrence.json + (optional) pipeline-built discoworld.db.
# The runtime ./data volume mount shadows this at compose up.
COPY data data

EXPOSE 8787

CMD ["uvicorn", "packages.api.main:app", "--host", "0.0.0.0", "--port", "8787"]
