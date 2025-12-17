# Changelog

## [0.7.6] - 2025-01-17

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

