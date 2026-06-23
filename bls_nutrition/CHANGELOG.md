# Changelog

All notable changes to the BLS Nährwertdatenbank Home Assistant Add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.2] - 2025-06-22

### Fixed

- Ingress UI: „Zur Einkaufsliste“-Button wird zuverlässig ausgeblendet, wenn `todo_list_enabled` deaktiviert ist

## [1.6.1] - 2025-06-21

### Added

- Add-on option `search_recents_enabled` (default `true`) to show or hide „Zuletzt berechnet“ chips in the Ingress search UI

## [1.6.0] - 2025-06-21

### Added

- Ingress UI: live search with 300 ms debounce (min. 2 characters) and request cancellation
- Quick-portion expandable cards with 50/100/150 g chips and custom amount
- Skeleton loaders for OFF search results; sessionStorage recents (last 5 calculations)
- Camera barcode scan via `BarcodeDetector` + `getUserMedia` (with manual EAN fallback)
- Dynamic recipe ingredients (add/remove rows, source per ingredient)
- Manual dark mode toggle (auto / light / dark) with FOUC-free theme init

### Changed

- Ingress search: BLS results render first; OFF column loads asynchronously
- Recipe form replaces fixed three-ingredient fields with dynamic list

## [1.5.0] - 2025-06-21

### Added

- SQLite FTS5 full-text index for BLS food search (~7.140 items)
- OFF text search: local cache lookup in `off_products` before API call
- OFF search query cache (`off_search_cache` table) with option `off_search_cache_ttl_days` (default 7)
- Negative barcode cache (`off_barcode_miss`) to avoid repeated OFF API calls for unknown EANs

### Changed

- Ingress UI shows BLS search results immediately; OFF column loads separately
- BLS search uses FTS5 with LIKE fallback for edge cases

## [1.4.1] - 2025-06-21

### Fixed

- Add-on updates via Home Assistant: pre-built GHCR image (`image:` in config.yaml)
- Docker build on armv7: removed `uvicorn[standard]` (uvloop/httptools cross-compile failure)
- CI publishes multi-arch manifest even when individual arch builds fail

### Changed

- Added `build.yaml` for Supervisor local-build fallback

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
