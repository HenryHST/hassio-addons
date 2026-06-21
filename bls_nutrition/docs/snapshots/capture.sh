#!/usr/bin/env bash
# Regenerate documentation screenshots (requires Node.js).
set -euo pipefail
cd "$(dirname "$0")"
npm install playwright --no-save
npx playwright install chromium
node capture.mjs
