#!/usr/bin/env bash
# DiscoWorld E2E harness — runs Playwright against vite preview (no Cloudflare
# between the test and the app). Usage: bash scripts/run-e2e.sh
#
# Background: prod is behind Cloudflare bot-challenge, so Playwright hits
# 403 / HTML-not-JSON on URL variants. Running against vite preview
# bypasses CF entirely and gives reproducible, reliable regression
# coverage across all 449 lines of e2e/discoworld.spec.js.
#
# Requires: Node 20+, Python 3.11+, API deps + Playwright browsers installed.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/packages/web"

echo "==> Building web..."
npm run build

echo "==> Running Playwright (chromium) against vite preview..."
# playwright.config.js already declares the webServer (vite preview + uvicorn API)
# so `playwright test` starts both automatically on ports 4173 and 8787.
npx playwright test --project=chromium "$@"
EC=$?

if [[ $EC -ne 0 ]]; then
  echo ""
  echo "E2E failed. HTML report: $ROOT/packages/web/playwright-report/index.html"
  echo "Open with: npx playwright show-report packages/web/playwright-report"
  exit $EC
fi

echo "==> E2E passed."
