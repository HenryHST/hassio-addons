# Versioning Strategy

## Overview

This add-on uses **dual versioning** to distinguish between the add-on wrapper and the underlying NUT core:

```
Add-on Version: 1.0.0 (semantic versioning)
Core Version: 2.8.1-5 (Network UPS Tools Debian package version)
```

## Add-on Version (Semantic Versioning)

The add-on version follows [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes to the add-on configuration or functionality
- **MINOR**: New features, improvements to Home Assistant integration
- **PATCH**: Bug fixes, documentation updates, minor tweaks

### Examples:
- `1.0.0` → `1.0.1`: Bug fix in shell scripts
- `1.0.0` → `1.1.0`: Added new configuration option (e.g., SSL parameters)
- `1.0.0` → `2.0.0`: Changed config.yaml schema (breaking change)

## Core Version (Network UPS Tools)

The core version indicates which version of NUT is bundled with the add-on:

- `2.8.1-5`: Current Network UPS Tools Debian package version
- Format: `{NUT_VERSION}-{DEBIAN_RELEASE}`

## Why Dual Versioning?

This approach allows:

1. **Independent Updates**: The add-on can be updated for Home Assistant compatibility, bug fixes, or new features (like SSL support) without changing the NUT core
2. **Clear Communication**: Users know both what add-on version they're running AND what NUT version is included
3. **Flexible Upgrades**: Core updates can be done independently when new NUT releases are available
4. **Better Change Tracking**: SSL features, script improvements, etc. can be versioned independently of NUT releases

## Version Display

Both versions are displayed at add-on startup:

```
-----------------------------------------------------------
 Network UPS Tools Add-on
 Add-on Version: 1.0.0
 NUT Core Version: 2.8.1-5
-----------------------------------------------------------
```

## Version History

### Add-on 1.0.0 (NUT 2.8.1-5)
- Initial semantic versioning release
- Added SSL/TLS support (CERTVERIFY, FORCESSL)
- Improved error handling and security
- Enhanced logging and diagnostics

### Previous: 0.13.0
- Development version before semantic versioning

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.



