# Changelog

All notable changes to this Home Assistant Add-on will be documented in this file.

**Note**: The add-on version (e.g., 1.0.0) is independent of the NUT core version (currently 2.8.1-5). 
The add-on version tracks changes to the Home Assistant integration, configuration, and wrapper functionality.

## [1.0.2] - 2025-12-17

### Security
- **CVE-2024-10918**: Applied security updates for libcurl4 (HIGH severity)
- **CVE-2025-6020**: Applied security updates for libpam modules (HIGH severity)
- **CVE-2025-7458**: Applied available updates for libsqlite3-0 (CRITICAL severity)
- **CVE-2023-45853**: Documented zlib1g vulnerability (marked will_not_fix by Debian)
- Added automated `apt-get upgrade` during build process
- Implemented security scanning workflow with Trivy

### Added
- Automated security patching during Docker build
- Package version logging for security auditing
- Daily vulnerability scanning

### Changed
- Enhanced build process with explicit security update step
- Improved package version tracking and logging

### Notes
- Some vulnerabilities may not have fixes available yet in Debian stable
- Security scanning runs daily to detect new vulnerabilities
- Base image updated to latest Debian bookworm-slim with security patches

## [1.0.1] - 2025-12-17

### Changed
- Switched to official Debian base image (`debian:bookworm-slim`)
- Improved Docker build process with official sources
- Added s6-overlay v3.1.6.2 for robust service management
- Enhanced package installation with system utilities (ca-certificates, tzdata, procps)

### Added
- GitHub Actions CI/CD workflows for automated builds
- Multi-architecture Docker image building (aarch64, amd64, armv7)
- Docker image signing with Cosign
- Automated linting (YAML, ShellCheck, Hadolint)
- s6-overlay integration for better service lifecycle management

### Fixed
- Hadolint warnings - improved Dockerfile best practices
- Shell pipefail option for safer script execution
- Service startup reliability with s6-overlay

## [1.0.0] - 2025-12-17

### Added
- Internal add-on versioning independent of NUT core version
- Version information display in startup logs showing both add-on and NUT core versions
- SSL/TLS Support: New `certverify` parameter to enforce certificate verification
- SSL/TLS Support: New `forcessl` parameter to enforce SSL-encrypted connections
- Comprehensive SSL documentation with security recommendations
- Input validation for environment variables in notify script
- Error handling for password generation

### Changed
- Add-on version changed from 0.13.0 to 1.0.0 (semantic versioning for add-on)
- NUT core version remains at 2.8.1-5
- Improved error handling in all shell scripts with `set -e`
- Enhanced notify script with proper curl error checking
- Unified base Docker image to ghcr.io/hassio-addons/debian-base:8.1.3

### Removed
- Deprecated `codenotary` field from config.yaml and build.yaml

### Fixed
- Directory permissions corrected from 0660 to 0770 for /etc/nut directories
- Exit code validation for upsdrvctl driver startup
- Notify script now validates required environment variables before execution
- Curl failures in notify script are now properly caught and logged

### Security
- SSL certificate verification capability (CERTVERIFY parameter)
- SSL connection enforcement capability (FORCESSL parameter)
- Improved error handling prevents silent failures
- Better permission management for NUT configuration files
- Environment variable validation in notification handler

## [0.13.0] - 2025-01-17

**Note**: This was the development version before implementing semantic versioning.

### Added
- **SSL/TLS Support**: New `certverify` parameter to enforce certificate verification for all upsd connections
- **SSL/TLS Support**: New `forcessl` parameter to enforce SSL-encrypted connections to upsd servers
- Comprehensive SSL documentation in DOCS.md with security recommendations
- Input validation for environment variables in notify script
- Error handling for password generation

### Changed
- Updated version from "dev" to semantic version 0.13.0
- Unified base Docker image to ghcr.io/hassio-addons/debian-base:8.1.3 (consistent with build.yaml)
- Improved error handling in all shell scripts with `set -e`
- Enhanced notify script with proper curl error checking

### Fixed
- Directory permissions corrected from 0660 to 0770 for /etc/nut directories
- Exit code validation for upsdrvctl driver startup
- Notify script now validates required environment variables before execution
- Curl failures in notify script are now properly caught and logged

### Security
- SSL certificate verification capability (CERTVERIFY parameter)
- SSL connection enforcement capability (FORCESSL parameter)
- Improved error handling prevents silent failures
- Better permission management for NUT configuration files
- Environment variable validation in notification handler

### Documentation
- Added detailed SSL configuration documentation
- Security warnings about SSL requirements
- Example configurations with SSL enabled
- Updated DOCS.md with certverify and forcessl options

## Notes

### SSL Parameters
Both SSL parameters default to `0` (disabled) for backward compatibility. To enable SSL security:

```yaml
certverify: 1  # Verify server certificates
forcessl: 1    # Enforce SSL connections
```

**Important**: Requires all upsd servers to have SSL properly configured.

