# Home Assistant Add-on: BLS Nährwertdatenbank

## About

Das Add-on stellt die deutsche BLS 4.0 Nährwertdatenbank lokal in Home Assistant bereit — mit WETID-inspirierten Diabetes-Einheiten und Barcode-Scanner über Open Food Facts.

## Installation

### Add-on

1. **Einstellungen** → **Add-ons** → **Add-on Store** → Repository hinzufügen
2. **BLS Nährwertdatenbank** installieren und starten
3. Ingress-Tab öffnen oder `http://<host>:8090/health` prüfen

Beim ersten Start lädt das Add-on die BLS-Daten von [blsdb.de](https://blsdb.de/download). Das kann 5–15 Minuten dauern.

### Custom Integration

> **HACS-Hinweis:** Das Repository `henryhst/hassio-addons` ist ein **Add-on Repository**
> (`repository.json` im Root). HACS kann es **nicht** als Integration hinzufügen.

#### Option A: Manuelle Installation (empfohlen)

Kopiere den Ordner `integration/custom_components/bls_nutrition` nach
`config/custom_components/bls_nutrition` und starte Home Assistant neu.

#### Option B: HACS

Verwende ein **separates** Integrations-Repository. Siehe
[`integration/README.md`](integration/README.md) für die Veröffentlichung als
eigenes GitHub-Repo (z. B. `homeassistant-bls-nutrition`).

### Integration einrichten

1. **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**
2. **BLS Nährwertdatenbank** wählen
3. Host: `bls_nutrition` (Supervisor-intern), Port: `8090`

## Configuration

```yaml
auto_update: true
update_interval_days: 30
language: de
enable_open_food_facts: true
off_cache_ttl_days: 90
```

## Services

### `bls_nutrition.search_food`

```yaml
service: bls_nutrition.search_food
data:
  query: Apfel
  limit: 10
```

Feuert Event `bls_nutrition_search_result`.

### `bls_nutrition.lookup_barcode`

```yaml
service: bls_nutrition.lookup_barcode
data:
  barcode: "4008400407321"
```

### `bls_nutrition.calculate_portion`

```yaml
service: bls_nutrition.calculate_portion
data:
  source: bls
  id: "F110000"
  amount_g: 150
```

Feuert Event `bls_nutrition_calculation_result` mit gKH, BE, KE, FPE.

### `bls_nutrition.calculate_recipe`

```yaml
service: bls_nutrition.calculate_recipe
data:
  servings: 2
  ingredients:
    - source: bls
      id: "F110000"
      amount_g: 200
    - source: bls
      id: "M711000"
      amount_g: 50
```

## Dashboard

Importiere `integration/custom_components/bls_nutrition/dashboards/bls_nutrition.yaml` oder erstelle diese Helper:

```yaml
input_text:
  bls_search_query:
    name: BLS Suche
  bls_barcode:
    name: Barcode
  bls_food_id:
    name: Lebensmittel ID

input_number:
  bls_amount_g:
    name: Menge g
    min: 1
    max: 5000
    step: 1
    unit_of_measurement: g
```

## Diabetes-Einheiten

| Einheit | Formel |
|---------|--------|
| gKH | Kohlenhydrate in Gramm |
| BE | gKH / 12 |
| KE | gKH / 10 |
| FPE | (Fett×9 + Protein×4) / 100 |

## Datenquellen & Lizenzen

| Quelle | Lizenz | Attribution |
|--------|--------|-------------|
| BLS 4.0 | CC BY 4.0 | Max Rubner-Institut, DOI: 10.25826/Data20251217-134202-0 |
| Open Food Facts | ODbL | openfoodfacts.org |

## Einschränkungen

- BLS enthält ~7.140 Grundlebensmittel (keine 350k wie WETID)
- Barcode-Lookup benötigt Internet und deckt primär Packungsprodukte ab
- Keine Insulin-Dosierungsempfehlung — nur Nährwertberechnung

## Support

- [GitHub Issues](https://github.com/henryhst/hassio-addons/issues)
- [Home Assistant Community](https://community.home-assistant.io)
