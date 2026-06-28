# Archiving ha-chronyd

After the Chrony NTP add-on is merged into [hassio-addons](https://github.com/henryhst/hassio-addons/tree/main/chronyd), archive the standalone repository [HenryHST/ha-chronyd](https://github.com/HenryHST/ha-chronyd).

## Steps (after merge to main)

1. Copy [`ARCHIVE_README_HA_CHRONYD.md`](ARCHIVE_README_HA_CHRONYD.md) to `README.md` in `HenryHST/ha-chronyd`.
2. On GitHub: **Settings → General → Archive this repository**.
3. Optional: Update Docker Hub `henryhst/ha-chronyd` description.

## gh CLI

```bash
gh api repos/HenryHST/ha-chronyd/contents/README.md -X PUT \
  -f message="docs: archive repository, redirect to hassio-addons/chronyd" \
  -f content="$(base64 < chronyd/ARCHIVE_README_HA_CHRONYD.md)"

gh repo edit HenryHST/ha-chronyd --description "Archived — use hassio-addons/chronyd"
gh api -X PATCH repos/HenryHST/ha-chronyd -f archived=true
```
