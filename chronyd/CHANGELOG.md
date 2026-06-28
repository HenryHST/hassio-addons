# Changelog

All notable changes to the Chrony NTP Home Assistant Add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-28

### Added

- Initial Home Assistant add-on import from [ha-chronyd](https://github.com/HenryHST/ha-chronyd)
- Chrony NTP server on UDP port 123
- Options: `ntp_servers`, `enable_nts`, `enable_sysclk`, `noclientlog`, `log_level`, `timezone`, `enable_ptp`
- Persistent drift file under `/data/chronyd/lib`
- Custom AppArmor profile
- ESP32 reference clock firmware projects under `ESP32/`
- CI: build, smoke test, Trivy scan
