# BLS Nährwertdatenbank — Home Assistant Integration (HACS)

Dieser Ordner ist ein **eigenständiges HACS-Integrationspaket**.

## Warum nicht `henryhst/hassio-addons` in HACS?

Das Haupt-Repository enthält `repository.json` und ist ein **Supervisor Add-on Repository**.
HACS erkennt es deshalb als Add-on-Repo und lehnt die Integration ab:

> *The repository does not seem to be a integration, but an add-on repository.*

## Installation

### Option A: Manuelle Installation (ohne HACS)

Kopiere den Inhalt von `custom_components/bls_nutrition` nach:

```text
config/custom_components/bls_nutrition/
```

Home Assistant neu starten.

### Option B: HACS (separates GitHub-Repository)

1. Erstelle ein **neues** GitHub-Repository, z. B. `homeassistant-bls-nutrition`
2. Kopiere den Inhalt **dieses Ordners** (`integration/`) als Root in das neue Repo:
   - `custom_components/bls_nutrition/`
   - `hacs.json`
   - `README.md`
3. **Kein** `repository.json` im neuen Repo!
4. In HACS: Custom Repository hinzufügen → Kategorie **Integration**
5. URL: `https://github.com/<dein-user>/homeassistant-bls-nutrition`

### Add-on

Das Add-on wird weiterhin über das Add-on-Repository installiert:

```text
https://github.com/henryhst/hassio-addons
```
