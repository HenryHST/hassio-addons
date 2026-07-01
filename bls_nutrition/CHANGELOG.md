# Changelog

All notable changes to the BLS Nährwertdatenbank Home Assistant Add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.5] - 2026-07-01

### Added

- HA-Services `export_favorites` / `import_favorites` vervollständigt wie `search_food`
- Export optional in Datei (`file_path`), Sensor-Attribut `last_io` am Favoriten-Zähler
- Dashboard-Abschnitt Favoriten mit Export/Import-Buttons
- Package-Helper und Scripts `bls_nutrition_export_favorites` / `bls_nutrition_import_favorites`
- `strings.json`-Einträge für hassfest-Konsistenz

## [1.8.4] - 2026-07-01

### Added

- **Favoriten Import/Export**: JSON und CSV über Header-Icon im Favoriten-Tab (nur sichtbar bei aktivem Favoriten-Panel)
- Import-Modi `merge` (Duplikate überspringen) und `replace` (alle ersetzen)
- Lösch-Bestätigungsdialog beim „Entfernen“-Button, optional per `favorites_confirm_delete`
- REST: `GET /favorites/export`, `POST /favorites/import`
- HA-Services `export_favorites`, `import_favorites`

## [1.8.3] - 2026-07-01

### Fixed

- Startfehler: `python-multipart` für Favoriten-Bild-Upload (`UploadFile`) in `requirements.txt` ergänzt

## [1.8.2] - 2026-07-01

### Added

- **Favoriten**: Neuer Ingress-Tab mit Herz-Icon, optional per `favorites_enabled`
- Favoriten in DuckDB (Umbenennen, Standard-Portion in g, eigenes Bild)
- OFF-Bild-Fallback über Open Food Facts, wenn kein lokales Bild vorhanden ist
- Herz-Button in Suche, Barcode-Ansicht und „Zuletzt berechnet“
- HA-Services `add_favorite`, `list_favorites`, `remove_favorite`
- Sensor `sensor.bls_nutrition_favorites_count`

## [1.8.1] - 2026-07-01

### Fixed

- Supervisor-Start-Timeout: BLS-Import läuft im Hintergrund, API/Healthcheck startet sofort
- hassfest: Manifest-Keys alphabetisch sortiert (`integration_type` vor `issue_tracker`)

## [1.8.0] - 2026-06-23

### Changed

- Datenbank von SQLite auf **DuckDB** (`/data/bls.duckdb`) umgestellt
- Einmalige Migration bestehender `/data/bls.sqlite`-Installationen beim ersten Start
- BLS-Suche ohne FTS5: ILIKE/Prefix-Suche in DuckDB
- OFF-Cache: abgelaufene Einträge werden beim Start per TTL bereinigt
- Ingress-Footer zeigt DB-Engine, Status, letzten BLS-Import und OFF-Cache-Anzahl (Header-Badge entfernt)
- `/health`: Felder `database_engine`, `database_status`, `off_products_count`

### Added

- DuckDB-Abhängigkeit (`duckdb==1.2.2`); SQLite-Extension im Docker-Image vorinstalliert
- Unit-Tests für DuckDB-Schema, Suche und Cache-Purge

## [1.7.7] - 2026-06-29

### Fixed

- hassfest: `services.yaml` select option `off` quoted (YAML boolean pitfall)
- hassfest: removed unsupported `dashboards` key from `manifest.json`
- hassfest: added `CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)`

## [1.7.4] - 2025-06-23

### Added

- Unit tests (`pytest`) for calculator, diabetes units, and opening hours display
- CI workflow: pytest, hassfest, ruff (`test-bls-nutrition.yaml`)
- Trivy security scan for BLS Docker image and Dockerfile
- AppArmor profile (`apparmor.txt`)

### Changed

- Integration version synced with add-on (1.7.4)

## [1.7.3] - 2025-06-28

### Added

- Home Assistant integration: Options Flow (host, port, default barcode amount)
- Services return responses (`supports_response`) for search, barcode, portion, recipe
- Service field `config_entry_id` for multi-instance setups
- Service `lookup_barcode` accepts `amount_g`
- Sensor entity translations (DE/EN) and availability when add-on is unreachable
- Local Leaflet bundle (map works without CDN)
- DOCS: Schnellstart-Checklist for full HA setup
- HACS publish guide (`integration/HACS_PUBLISH.md`)

### Changed

- Integration version synced with add-on (1.7.3)
- Unified todo list default: `todo.shopping_list` everywhere
- Services unregister on last integration unload

### Fixed

- `todo_list_enabled` runtime default aligned with add-on config (`true`)
- `repository.json` maintainer typo

## [1.7.2] - 2025-06-23

### Added

- Map markers colored by opening status: blue (Home Assistant), green (open), red (closed), gray (unknown OSM hours)
- API field `is_open_now` on `/map/supermarkets` items

### Fixed

- Map tab hides calculation details from other panels

## [1.7.0] - 2025-06-23

### Added

- Map tab: supermarkets near the Home Assistant location (OpenStreetMap / Overpass / Leaflet)
- Add-on options `map_enabled` and `map_radius_km`
- Context-aware opening hours in map marker popups (today on weekdays, full week on Sundays, closed on public holidays)
- Regional public holidays via Nominatim reverse geocoding (cached in `/data/map_location_cache.json`)

### Fixed

- Map tab and hero tiles respect `map_enabled` and stay hidden when the map panel is inactive
- Overpass API requests include a `User-Agent` header (fixes HTTP 406)

## [1.6.3] - 2025-06-23

### Changed

- Removed deprecated `armv7` architecture (Home Assistant sunset of 32-bit platforms)

## [1.6.2] - 2025-06-22

### Fixed

- Ingress UI: „Zur Einkaufsliste“-Button wird zuverlässig ausgeblendet, wenn `todo_list_enabled` deaktiviert ist
- `todo_list_enabled` wird zur Laufzeit aus `/data/options.json` gelesen (nicht nur aus Start-Env)

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
