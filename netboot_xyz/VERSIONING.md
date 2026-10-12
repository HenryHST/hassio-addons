# Versioning Strategy

## Overview

This add-on uses **multi-layer versioning** to distinguish the Home Assistant wrapper from upstream components:

```
Add-on Version: 1.3.0 (semantic versioning)
Webapp Version: 0.7.6 (netbootxyz/webapp)
Menus Version:  3.0.3 (netbootxyz/netboot.xyz releases)
iPXE SB:        v2.0.0 (ipxe/ipxe ipxeboot.tar.gz; option ipxe_sb_version)
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

## Webapp Version

Pinned in the Dockerfile as `NETBOOTXYZ_VERSION`. This is the Node.js management UI from
[`netbootxyz/webapp`](https://github.com/netbootxyz/webapp).

- Current: `0.7.6`

## Menus Version

Boot menus and iPXE binaries from [`netbootxyz/netboot.xyz` releases](https://github.com/netbootxyz/netboot.xyz/releases).
Downloaded at init time (not baked into the image).

- Default pin: `3.0.3`
- Override: add-on option `menu_version`
- Stored after download in `/config/menuversion.txt`
- Re-downloaded when the stored version differs from the desired pin

## Why Separate Versions?

1. **Independent updates**: Webapp and menus ship on different release trains
2. **Clear communication**: Users know which UI and which boot menus they run
3. **Flexible upgrades**: `menu_version` can pin or override without rebuilding the image

## Version Display

All three are shown at add-on startup:

```
-----------------------------------------------------------
 Home Assistant Add-on Version: 1.3.0
 netboot.xyz Webapp Version: 0.7.6
 netboot.xyz Menus Version: 3.0.3
-----------------------------------------------------------
```

Secure Boot download status is logged during init (not in the banner). Menu version, last download,
and TFTP status are also published as Home Assistant entities when `enable_ha_sensors` is true.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
