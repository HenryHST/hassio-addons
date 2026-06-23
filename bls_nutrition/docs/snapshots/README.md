# Documentation Screenshots

Regenerates PNG screenshots in [`../images/`](../images/) from static demo HTML pages that use the real Ingress styles from [`../../root/static/`](../../root/static/).

## Requirements

- Node.js **18+**
- npm
- ~500 MB disk space for Playwright Chromium (first run)

## Usage

From this directory:

```bash
./capture.sh
```

Capture only specific screens:

```bash
./capture.sh --only search,barcode
```

Valid `--only` ids: `navigation`, `search`, `portion`, `barcode`, `recipe`, `dark`.

## Output files

| PNG | Demo HTML |
|-----|-----------|
| `ingress-navigation.png` | `demo-overview.html` |
| `ingress-search.png` | `demo-search.html` |
| `ingress-portion.png` | `demo-portion.html` |
| `ingress-barcode.png` | `demo-barcode.html` |
| `ingress-recipe.png` | `demo-recipe.html` |
| `ingress-dark.png` | `demo-dark.html` |

## Troubleshooting

**Chromium download fails:** The script falls back to system Google Chrome (`channel: chrome`). Install Chrome or run `npx playwright install chromium` manually.

**Blank or broken layout:** Ensure paths to `../../root/static/styles/` and assets resolve — run from this folder only.

**Permission denied:** `chmod +x capture.sh`

`node_modules/` is gitignored; dependencies are installed locally on each run.
