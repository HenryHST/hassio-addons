# Changelog

All notable changes to the Corosync QNetd Home Assistant Add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-06

### Security

- **CRITICAL**: Removed SSH server from container (openssh-server package)
- **CRITICAL**: Removed hardcoded root password ('root:proxmox')
- **CRITICAL**: Removed `PermitRootLogin yes` configuration
- **CRITICAL**: Removed password authentication exposure
- Added security updates during Docker build process (`apt-get upgrade`)
- Implemented package version pinning for reproducible builds
- Removed port 22 (SSH) from exposed ports

### Added

- Initial release of Corosync QNetd Home Assistant Add-on
- Corosync QNetd 3.1.7 support
- Multi-architecture builds (aarch64, amd64, armv7)
- Configurable QNetd port (default: 5403)
- Configurable log levels (trace, debug, info, notice, warning, error, fatal)
- Dual versioning system (addon version + core version)
- Startup banner showing addon and Corosync versions
- Health check monitoring (30-second intervals)
- Comprehensive documentation (README.md, DOCS.md, VERSIONING.md)
- Proxmox VE integration guide
- Troubleshooting documentation
- Configuration validation
- Home Assistant Supervisor integration

### Changed

- Updated base image from `debian:12.12-slim` to `debian:bookworm-slim`
- Restructured Dockerfile following Home Assistant add-on best practices
- Improved entrypoint script with proper error handling
- Enhanced configuration parsing from `/data/options.json`
- Updated config.yaml to remove NUT (Network UPS Tools) configuration
- Removed unnecessary permissions (uart, udev, usb)
- Disabled homeassistant_api (not required for network service)

### Fixed

- Removed incorrect NUT configuration from config.yaml (lines 24-41)
- Fixed Docker labels for Home Assistant compatibility
- Added SHELL directive with pipefail for safer script execution
- Improved error handling in entrypoint script with proper exit codes
- Added shellcheck directive for better script linting

### Documentation

- Created comprehensive README.md with installation guide
- Created detailed DOCS.md with Proxmox VE integration steps
- Created VERSIONING.md explaining dual versioning strategy
- Added troubleshooting section for common issues
- Documented network requirements and firewall configuration
- Added certificate management documentation
- Created README.j2 template for dynamic documentation generation

### Infrastructure

- Added GitHub Actions workflow for multi-arch builds
- Integrated Trivy security scanning
- Added Hadolint Dockerfile linting
- Added ShellCheck script linting
- Added YAML linting (yamllint)
- Configured automated Docker image signing with Cosign
- Added VEX (Vulnerability Exploitability eXchange) support

### Developer Notes

This release represents a complete security overhaul and production-ready implementation of Corosync QNetd as a Home Assistant add-on. The removal of SSH server and hardcoded credentials makes this addon suitable for public use.

**Breaking Changes from Pre-release:**
- SSH server removed: If you relied on SSH access, use Home Assistant's built-in SSH add-on instead
- Port 22 no longer exposed
- Configuration schema changed: Old NUT configuration options removed

**Migration from Pre-release:**
If upgrading from a pre-release version with SSH:
1. Remove any SSH-based automation
2. Update configuration to remove NUT-related options
3. Reinstall add-on with new configuration
4. Reconfigure Proxmox cluster: `pvecm qdevice setup <HA_IP>`

---

## Version History Summary

| Version | Date | Core Version | Highlights |
|---------|------|--------------|------------|
| 1.0.0 | 2025-01-06 | 3.1.7 | Initial secure release, SSH removed |

---

**Note**: This changelog documents changes to the **Home Assistant Add-on**. For changes to the underlying Corosync QNetd software, see the [Corosync project changelog](https://github.com/corosync/corosync/blob/main/ChangeLog).

