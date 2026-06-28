# HACS-Repository veröffentlichen

Die Integration kann **nicht** aus `henryhst/hassio-addons` per HACS installiert werden, weil das Hauptrepo ein Supervisor Add-on Repository ist (`repository.json`).

## Neues Repository anlegen

1. GitHub: neues Repository erstellen, z. B. `homeassistant-bls-nutrition` (öffentlich)
2. **Kein** `repository.json` im Root des neuen Repos
3. Inhalt aus diesem Ordner (`integration/`) als Root kopieren:

```text
homeassistant-bls-nutrition/
├── custom_components/bls_nutrition/
├── packages/bls_nutrition.yaml
├── brand/icon.png
├── hacs.json
└── README.md
```

## Sync aus hassio-addons

Vom Monorepo-Root:

```bash
rsync -av --delete \
  bls_nutrition/integration/custom_components/ \
  /pfad/zu/homeassistant-bls-nutrition/custom_components/

rsync -av \
  bls_nutrition/integration/packages/ \
  /pfad/zu/homeassistant-bls-nutrition/packages/

cp bls_nutrition/integration/hacs.json /pfad/zu/homeassistant-bls-nutrition/
cp bls_nutrition/integration/README.md /pfad/zu/homeassistant-bls-nutrition/
cp bls_nutrition/integration/brand/icon.png /pfad/zu/homeassistant-bls-nutrition/brand/
```

Version in `custom_components/bls_nutrition/manifest.json` muss zum Add-on passen.

## HACS einrichten

1. Home Assistant → HACS → Integrationen → **Benutzerdefinierte Repositories**
2. URL: `https://github.com/<user>/homeassistant-bls-nutrition`
3. Kategorie: **Integration**
4. Integration **BLS Nährwertdatenbank** installieren und neu starten

## Add-on (separat)

Das Add-on bleibt im Add-on-Repository:

```text
https://github.com/henryhst/hassio-addons
```

## Release-Checkliste

- [ ] `manifest.json` Version = Add-on `config.yaml` Version
- [ ] `translations/de.json` und `en.json` aktuell
- [ ] `services.yaml` mit Services in `__init__.py` abgeglichen
- [ ] GitHub Release mit Tag `vX.Y.Z`
- [ ] HACS zeigt neue Version nach Refresh
