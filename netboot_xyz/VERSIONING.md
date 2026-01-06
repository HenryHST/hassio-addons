# Versioning Strategy

## Overview

This add-on uses **dual versioning** to distinguish between the add-on wrapper and the underlying netboot.xyz core:

```
Add-on Version: 1.0.0 (semantic versioning)
Core Version: 0.7.6 (netboot.xyz upstream version)
```

## Add-on Version (Semantic Versioning)

The add-on version follows [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes to the add-on configuration or functionality
- **MINOR**: New features, improvements to Home Assistant integration
- **PATCH**: Bug fixes, documentation updates, minor tweaks

### Examples:
- `1.0.0` → `1.0.1`: Bug fix in nginx configuration
- `1.0.0` → `1.1.0`: Added new configuration option
- `1.0.0` → `2.0.0`: Changed config.yaml schema (breaking change)

## Core Version (netboot.xyz)

The core version indicates which version of netboot.xyz is bundled with the add-on:

- `0.7.6`: Current netboot.xyz webapp and boot files version

## Why Dual Versioning?

This approach allows:

1. **Independent Updates**: The add-on can be updated for Home Assistant compatibility, bug fixes, or new features without changing the netboot.xyz core
2. **Clear Communication**: Users know both what add-on version they're running AND what netboot.xyz version is included
3. **Flexible Upgrades**: Core updates can be done independently when new netboot.xyz releases are available

## Version Display

Both versions are displayed at add-on startup:

```
-----------------------------------------------------------
 Home Assistant Add-on Version: 1.0.0
 netboot.xyz Core Version: 0.7.6
-----------------------------------------------------------
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.



