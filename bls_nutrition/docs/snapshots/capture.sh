#!/usr/bin/env bash
# Regenerate documentation screenshots from demo HTML (requires Node.js 18+).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGES_DIR="${SCRIPT_DIR}/../images"
MIN_NODE_MAJOR=18

err() {
  echo "Error: $*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || err "$1 is required but not installed."
}

need_cmd node
need_cmd npm

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if (( NODE_MAJOR < MIN_NODE_MAJOR )); then
  err "Node.js ${MIN_NODE_MAJOR}+ required (found $(node -v))."
fi

if [[ ! -d "${IMAGES_DIR}" ]]; then
  mkdir -p "${IMAGES_DIR}"
fi
if [[ ! -w "${IMAGES_DIR}" ]]; then
  err "Output directory is not writable: ${IMAGES_DIR}"
fi

for demo in demo-overview.html demo-search.html demo-portion.html demo-barcode.html demo-recipe.html demo-dark.html; do
  [[ -f "${SCRIPT_DIR}/${demo}" ]] || err "Missing ${demo} in ${SCRIPT_DIR}"
done

cd "${SCRIPT_DIR}"

if [[ -f package-lock.json ]]; then
  npm ci --no-audit --no-fund
else
  npm install --no-audit --no-fund
fi

if npx playwright install --dry-run chromium 2>/dev/null | grep -q "Download url:.*chromium"; then
  echo "Installing Playwright Chromium…"
  npx playwright install chromium
else
  echo "Playwright Chromium already installed (or system Chrome will be used as fallback)."
fi

node capture.mjs "$@"
