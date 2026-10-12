# Changelog

All notable changes to this Home Assistant Add-on will be documented in this file.

**Note**: The add-on version is independent of upstream layers:
- **Webapp** (UI): currently `0.7.6` (`netbootxyz/webapp`)
- **Menus / boot files**: currently pinned to `3.0.3` (`netbootxyz/netboot.xyz` releases)

## [1.3.0] - 2026-10-12

### Added

- Option `tftpd_opts` (e.g. `--tftp-single-port`) via `/tftpd.sh` wrapper for firewalls/NAT
- Metal TFTP boot files (`netboot.xyz-metal*.efi` / `.kpxe`) and optional `netboot.xyz-rpi4-snp.efi` (skipped if missing from the menu release)
- CI container smoke test (web UI :3000, TFTP :69, `menu.ipxe` present)

### Changed

- DOCS: Ingress vs host-IP/ports clarified for PXE/DHCP
- AppArmor: execute rules for `ha-sensors.sh` and `tftpd.sh`

### Notes

- Still uses **tftp-hpa** (no dnsmasq/ProxyDHCP in this add-on; deferred)

## [1.2.0] - 2026-10-12

### Added

- Home Assistant sensors via Core States API: `sensor.netboot_xyz_menu_version`, `sensor.netboot_xyz_last_download`, `binary_sensor.netboot_xyz_tftp`
- Options `enable_ha_sensors` (default `true`) and `sensor_poll_interval` (30–300, default `60`)

### Changed

- `boot: auto` — add-on starts with Home Assistant
- `host_network: true` — improves PXE/TFTP reliability; nginx listens on **8080** (avoids host port 80 conflict)
- Port mapping documented as `8080/tcp` (was container `80` → host `8080`)

### Notes

- `mqtt:want` remains removed (unused since 1.1.0); status uses `homeassistant_api`, not MQTT

## [1.1.0] - 2026-10-12

### Added

- UEFI Secure Boot: downloads signed iPXE binaries (`ipxeboot.tar.gz` v2.0.0) and `autoexec.ipxe` into `secureboot-x86_64/` / `secureboot-arm64/`
- Options `enable_secure_boot` (default `true`) and `ipxe_sb_version` (empty = `v2.0.0`)

### Changed

- Multi-stage Dockerfile: npm only in build stage; runtime without `git`, `sudo`, `busybox`, `npm`, `syslog-ng`
- Removed unused `mqtt:want` service declaration

### Removed

- `syslog-ng` and `messages-log` supervisor programs (upstream no longer uses them; avoids FATAL spam)

## [1.0.9] - 2026-10-12

### Changed

- Boot menus pinned to [netboot.xyz 3.0.3](https://github.com/netbootxyz/netboot.xyz/releases/tag/3.0.3) (no longer confused with webapp `0.7.6`)
- Existing installs re-download menus when stored `menuversion.txt` differs from the desired pin
- Startup banner shows webapp and menus versions separately

### Added

- Legacy boot files `netboot.xyz-legacy.kpxe` / `netboot.xyz-legacy.efi` (3.x+; skipped if unavailable)

## [1.0.8] - 2026-06-28

### Added

- Add-on icon (`icon.png`)
- CI: ShellCheck on `root/*.sh`, `nginx -t` on rendered configs
- Weekly scheduled npm audit re-run; Dependabot for GitHub Actions

### Changed

- DOCS: Ingress quick-start section

## [1.0.7] - 2025-06-23

### Added

- Docker `HEALTHCHECK` on web UI port 3000
- CI workflow: `npm audit` fails on HIGH+ vulnerabilities

### Changed

- AppArmor profile rewritten for supervisord stack (removed s6/bashio, `sys_admin`, broad `/dev/*`)
- Removed unused `docker_api`; `hassio_role` lowered to `default`
- Full OCI image labels in Dockerfile; `npm audit fix` no longer ignores failures
- Security patches use `npm install` (not `npm update`) for pinned dependency versions (`systeminformation`, `express`, `js-yaml`)

### Fixed

- CI npm-audit job: `EUPDATEARGS` from invalid `npm update package@version` syntax

## [1.0.6] - 2025-06-28

### Fixed

- Removed `image:` field (Supervisor builds locally; fixes GHCR `404 manifest unknown`)
- CI: multi-arch manifest via `buildx imagetools` instead of `docker manifest create`

## [1.0.5] - 2025-06-23

### Added

- `menu_version` add-on option (optional override for boot menus)
- `image:` field for GHCR publishing

### Changed

- Boot menus default to pinned webapp version (`NETBOOTXYZ_VERSION`), not GitHub `latest`
- `url` points to `main` branch
- Documentation synced to 1.0.5

## [1.0.4] - 2025-06-23

### Changed

- Removed deprecated `advanced` field from add-on config (ignored by current Supervisor)

## [1.0.3] - 2025-06-23

### Changed

- Removed deprecated `armv7` architecture (Home Assistant sunset of 32-bit platforms)

## [1.0.2] - 2025-12-17

### Security
- **CVE-2025-68154**: Updated `systeminformation` from 5.27.1 to 5.27.14 to fix OS Command Injection vulnerability
- Added automated security scanning with Trivy
- Implemented daily vulnerability checks

### Added
- Security scanning workflow with Trivy scanner
- Automated npm audit fix during build process
- SARIF reports uploaded to GitHub Security tab

### Changed
- Enhanced build process with security patching step
- Improved npm dependency management

## [1.0.1] - 2025-12-17

### Changed
- Switched to official Alpine Linux base image (`alpine:3.20`)
- Improved Docker build process with official sources
- Enhanced package installation with additional system tools (ca-certificates, tzdata)
- Added nginx log symlinks to stdout/stderr for better container logging

### Added
- GitHub Actions CI/CD workflows for automated builds
- Multi-architecture Docker image building (aarch64, amd64, armv7)
- Docker image signing with Cosign
- Automated linting (YAML, ShellCheck, Hadolint)

### Fixed
- Hadolint warnings (DL3003, DL4006) - improved Dockerfile best practices
- Shell pipefail option for safer script execution
- WORKDIR usage instead of cd for better maintainability

## [1.0.0] - 2025-12-17

### Added
- Internal add-on versioning independent of netboot.xyz core version
- Version information display in startup logs showing both add-on and core versions
- Improved supervisor configuration with proper service ordering
- Enhanced logging to stdout/stderr for better diagnostics

### Changed
- Add-on version changed from 0.7.6 to 1.0.0 (semantic versioning for add-on)
- netboot.xyz core version remains at 0.7.6
- Nginx configuration always updates on start to ensure latest settings
- Webapp listens on all interfaces (0.0.0.0) for proper Ingress support

### Fixed
- Nginx invalid condition syntax in site configuration
- Supervisor TFTPD_OPTS environment variable expansion
- File permissions for shell scripts (execute permissions)
- Service start order for proper initialization

## [0.7.6] - 2025-01-17

**Note**: This was the initial release using the netboot.xyz version as add-on version.

### Added
- Initial release of netboot.xyz Home Assistant Add-on
- Web management interface on port 3000 with Ingress support
- TFTP server for network booting (port 69/UDP)
- HTTP asset hosting server (port 8080)
- Support for multiple architectures: amd64, aarch64, armv7
- AppArmor security profile
- Nginx configuration for asset hosting

### Changed
- Updated to netboot.xyz version 0.7.6
- Unified Docker image sources to ghcr.io/netbootxyz/netbootxyz:0.7.6
- Improved nginx configuration with security headers
- Enhanced error handling in shell scripts

### Fixed
- Corrected AppArmor profile name (was incorrectly named bitwarden_addon)
- Fixed directory permissions in nginx configuration
- Improved script error handling with proper exit codes
- Added validation for GitHub API responses

### Security
- Added security headers: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- Hidden nginx version information (server_tokens off)
- Improved gzip compression configuration
- Restricted HTTP methods to GET and HEAD for asset server
- Blocked access to hidden files and sensitive directories

### Documentation
- Comprehensive README with Home Assistant specific instructions
- Detailed DHCP configuration examples
- Complete boot file reference table
- Asset mirroring documentation

