#!/bin/bash
# DiscoWorld Demo Tour — opens key views in browser
# Usage: ./scripts/demo-tour.sh [base_url]
#
# Requires: local dev server running (npm run dev in packages/web)

BASE="${1:-http://localhost:5173}"

echo "=== DiscoWorld Demo Tour ==="
echo "Base URL: $BASE"
echo ""

echo "1/5 — Genre World: Techno territory"
open "$BASE/?genre=techno"
sleep 4

echo "2/5 — Earth Globe: Berlin scene"
open "$BASE/?view=earth&city=berlin"
sleep 4

echo "3/5 — Genre Planet: 3D overview"
open "$BASE/?view=planet"
sleep 4

echo "4/5 — Deep linking: Ambient with year 1995"
open "$BASE/?genre=ambient&year=1995"
sleep 4

echo "5/5 — Drift mode: Serendipity auto-navigation"
open "$BASE/?drift=1"

echo ""
echo "Demo tour complete. Press L in any view to open the Strudel live coder."
