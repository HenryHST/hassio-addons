# Changelog

All notable changes to the BLS Nährwertdatenbank Home Assistant Add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-06-21

### Added

- Import OFF products to Home Assistant to-do list via **Zur Einkaufsliste** button in Ingress UI
- Add-on options `todo_list_enabled` and `todo_list_entity_id` (default `todo.einkaufsliste`)
- `POST /todo-list/items` API endpoint (Supervisor proxy to `todo.add_item`)
- Integration service `bls_nutrition.add_to_todo_list`

## [1.3.0] - 2025-06-21

### Added

- Nutri-Score, Nova-Score and Eco-Score from Open Food Facts (OFF)
- OFF cache columns `nutriscore`, `nova_group`, `ecoscore` in SQLite
- SVG score badges in Ingress UI (search, barcode, portion details)
- Integration sensors `sensor.bls_nutrition_nutriscore`, `_nova`, `_ecoscore`
- Lovelace dashboard entities for all three scores

### Changed

- OFF search API requests include score fields
- Portion calculation returns scores for OFF products

## [1.2.0] - 2025-06-21

### Added

- Dual-column search in Ingress UI: BLS 4.0 (left) and Open Food Facts (right)
- `GET /foods/search/off` endpoint for Open Food Facts text search
- Add-on option `search_layout`: `stacked` (default) or `side_by_side`
- Documentation screenshots for Ingress Web-UI (`docs/images/`)

### Changed

- Search results cache OFF products locally for immediate portion calculation
- Sidebar panel (`BLS Nährwert`) visible to all HA users via `panel_admin: false`

## [1.1.0] - 2025-06-21

### Added

- Ingress-Web-UI im diabetes-fokussierten Design (WETID-Stil)
- Hero-Tiles für gKH, BE, KE und FPE mit Bottom-Navigation
- Lebensmittelsuche, Barcode-Lookup, Portion- und Rezeptrechner in der Web-UI
- Dark-Mode-Unterstützung via `prefers-color-scheme`

### Changed

- Ingress-Startseite ersetzt minimale Status-HTML durch vollwertige Web-App
- Barcode-Route vor generischer Food-Route registriert

## [1.0.0] - 2025-06-21

### Added

- Initial release of BLS 4.0 Nährwertdatenbank add-on
- Automatic BLS 4.0 download and SQLite import on startup
- REST API for food search, portion and recipe calculation
- Diabetes units: gKH, BE, KE, FPE (WETID-inspired)
- Open Food Facts barcode lookup with local cache
- Custom foods and recipes storage
- Home Assistant custom integration with services and sensors
- Lovelace dashboard template
- Ingress web status page
