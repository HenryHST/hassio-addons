# Changelog

All notable changes to the BLS Nährwertdatenbank Home Assistant Add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
