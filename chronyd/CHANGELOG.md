# Changelog

All notable changes to the Chrony NTP Home Assistant Add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-06-28

### Changed

- Pool and `ntp_server` list can be configured **simultaneously** (ported from [addon-chrony PR #215](https://github.com/hassio-addons/addon-chrony/pull/215))
- `mode` (`pool`|`server`) is deprecated and ignored; validation requires at least one of `ntp_pool` or `ntp_server`
- Default `ntp_server` is an empty list; configure pool only, servers only, or both

### Added

- `pool_maxsources` option (1–16, default 4) for `pool … maxsources` chrony directive

## [2.0.0] - 2026-06-28

### Changed

- **Breaking:** Replaced Alpine `entrypoint.sh` / `startup.sh` with Debian + bashio + s6-overlay (same pattern as `nut/`), aligned with [hassio-addons/addon-chrony](https://github.com/hassio-addons/addon-chrony)
- **Breaking:** Configuration schema: `mode` (`pool`|`server`), `ntp_pool`, `ntp_server` (list), `set_system_clock` — replaces `ntp_servers`, `enable_sysclk`, `noclientlog`, `timezone`
- PTP `refclock` is only added when `enable_ptp: true` (fixes spurious `/dev/ptp0` on hosts where the device node exists but is unusable)
- `privileged: [SYS_TIME]` and `hassio_api: true` for host clock sync
- AppArmor profile updated for s6-overlay and bashio

### Added

- `initstepslew` upstream configuration (community addon behaviour)
- bashio `log_level` (trace through fatal)

### Removed

- Debug instrumentation from 1.0.x troubleshooting
- Alpine-based image and `su-exec` startup path

## [1.0.0] - 2026-06-28

### Added

- Initial Home Assistant add-on import from [ha-chronyd](https://github.com/HenryHST/ha-chronyd)
- Chrony NTP server on UDP port 123
- Options: `ntp_servers`, `enable_nts`, `enable_sysclk`, `noclientlog`, `log_level`, `timezone`, `enable_ptp`
- Persistent drift file under `/data/chronyd/lib`
- Custom AppArmor profile
- ESP32 reference clock firmware projects under `ESP32/`
- CI: build, smoke test, Trivy scan
