# Home Assistant Add-on: BLS Nährwertdatenbank

![Version](https://img.shields.io/badge/version-1.6.1-blue.svg)
![Supports aarch64 Architecture](https://img.shields.io/badge/aarch64-yes-green.svg)
![Supports amd64 Architecture](https://img.shields.io/badge/amd64-yes-green.svg)
![Supports armv7 Architecture](https://img.shields.io/badge/armv7-yes-green.svg)

Bundeslebensmittelschlüssel (BLS) 4.0 Nährwertdatenbank mit Diabetes-Einheiten und Barcode-Lookup für Home Assistant.

**Hinweis:** Keine medizinische Beratung. Diabetes-Berechnungen dienen nur der Information.

## About

![Ingress Web-UI](docs/images/ingress-navigation.png)

Dieses Add-on lädt die offizielle [BLS 4.0](https://blsdb.de/download)-Datenbank (7.140 Lebensmittel, CC BY 4.0) und stellt eine REST-API bereit für:

- Lebensmittelsuche
- Portions- und Rezeptberechnung
- Diabetes-Einheiten: **gKH**, **BE**, **KE**, **FPE** (WETID-inspiriert)
- Barcode-Lookup über **Open Food Facts** (inkl. Nutri-Score, Nova-Score, Eco-Score)
- Eigene Lebensmittel und Rezepte

Eine Custom Integration für Home Assistant ist im Ordner `integration/` enthalten.

> **HACS:** Das Add-on-Repository `henryhst/hassio-addons` kann in HACS **nicht** als
> Integration hinzugefügt werden. Siehe [`integration/README.md`](integration/README.md).

## Installation

1. Repository hinzufügen: `https://github.com/henryhst/hassio-addons`
2. Add-on **BLS Nährwertdatenbank** installieren und starten
3. Beim ersten Start werden BLS-Daten heruntergeladen (kann einige Minuten dauern)
4. Integration installieren (siehe [DOCS.md](DOCS.md))

## Configuration

| Option | Default | Beschreibung |
|--------|---------|--------------|
| `auto_update` | `true` | BLS-Daten automatisch aktualisieren |
| `update_interval_days` | `30` | Update-Intervall in Tagen |
| `language` | `de` | Anzeigesprache (`de`/`en`) |
| `enable_open_food_facts` | `true` | Barcode-Lookup und OFF-Suche aktivieren |
| `off_cache_ttl_days` | `90` | OFF-Barcode-Cache (Tage) |
| `off_search_cache_ttl_days` | `7` | OFF-Textsuche-Cache (Tage) |
| `search_layout` | `stacked` | Suchergebnis-Layout: `stacked` oder `side_by_side` |
| `search_recents_enabled` | `true` | Chips „Zuletzt berechnet“ in der Suche anzeigen |
| `todo_list_enabled` | `true` | OFF-Produkte zur HA-To-do-Liste hinzufügen |
| `todo_list_entity_id` | `todo.shopping_list` | Ziel-To-do-Entity |

## API Endpoints

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /health` | Status und BLS-Version |
| `GET /foods/search?q=` | BLS-Lebensmittelsuche |
| `GET /foods/search/off?q=` | Open Food Facts Textsuche |
| `GET /foods/barcode/{ean}` | Barcode-Lookup |
| `POST /calculate/portion` | Portion berechnen |
| `POST /calculate/recipe` | Rezept aggregieren |

## Attribution

- **BLS 4.0:** Max Rubner-Institut (2025), CC BY 4.0, DOI: 10.25826/Data20251217-134202-0
- **Open Food Facts:** ODbL


## Support

- [DOCS.md](DOCS.md) — Vollständige Dokumentation
- [GitHub Issues](https://github.com/henryhst/hassio-addons/issues)
