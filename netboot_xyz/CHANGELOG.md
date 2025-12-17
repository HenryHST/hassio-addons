# Changelog

All notable changes to this Home Assistant Add-on will be documented in this file.

**Note**: The add-on version (e.g., 1.0.0) is independent of the netboot.xyz core version (currently 0.7.6). 
The add-on version tracks changes to the Home Assistant integration, configuration, and wrapper functionality.

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

