# Versioning Strategy

The Corosync QNetd Home Assistant Add-on uses a **dual versioning** approach to provide clarity about both the add-on features and the underlying Corosync QNetd software version.

## Two Independent Versions

### 1. Addon Version

**Format:** Semantic Versioning (MAJOR.MINOR.PATCH)  
**Example:** `1.0.0`  
**Visible in:**
- Add-on info panel in Home Assistant
- Startup logs: "Add-on Version: 1.0.0"
- `config.yaml` version field
- Docker image tags
- GitHub releases

**What it tracks:**
- Add-on feature additions and changes
- Configuration option updates
- Integration improvements with Home Assistant
- Documentation updates
- Bug fixes in add-on logic
- Security updates to the add-on container

**Version bump rules:**
- **MAJOR (1.x.x)**: Breaking changes to configuration or behavior
- **MINOR (x.1.x)**: New features, new configuration options
- **PATCH (x.x.1)**: Bug fixes, documentation updates, security patches

**Examples:**
```
1.0.0 → 1.0.1  Security patch, documentation fix
1.0.1 → 1.1.0  Added TLS configuration option
1.1.0 → 2.0.0  Changed configuration schema (breaking)
```

### 2. Corosync Core Version

**Format:** Upstream Version (MAJOR.MINOR.PATCH-DEBIAN_REVISION)  
**Example:** `3.1.7-1` (Debian Bookworm default)  
**Visible in:**
- Startup logs: "Corosync Version: corosync-qnetd 3.1.7-1"
- Available via `corosync-qnetd -v` command
- Documentation

**What it tracks:**
- Upstream Corosync QNetd version from Debian repositories
- Core functionality of QNetd
- Protocol improvements
- Upstream bug fixes
- Debian package version

**Update policy:**
- Uses the latest version available in Debian Bookworm repositories
- Automatically updated when Debian releases security updates
- Version is determined at build time from apt repositories
- Tested before integration into addon

## Version Display

### At Addon Startup

```
-----------------------------------------------------------
 Corosync QNetd Add-on
 Add-on Version: 1.0.0
 Corosync Version: corosync-qnetd 3.1.7-1
-----------------------------------------------------------
```

### In Container Environment

Corosync version is available at runtime via:
```bash
corosync-qnetd -v
# Output: corosync-qnetd 3.1.7-1
```

### In Documentation

Both versions are clearly documented:
- README.md includes both versions
- CHANGELOG.md tracks addon version changes
- DOCS.md references core version for compatibility

## Why Dual Versioning?

### Clarity

Users can distinguish between:
- Add-on updates (new features, config changes)
- Core software updates (Corosync functionality)

### Independence

- Add-on can be updated without changing core
- Core can be updated without breaking add-on features
- Security patches can be applied to either independently

### Compatibility

Users can determine:
- Which Proxmox versions are compatible (based on core version)
- Which configuration options are available (based on addon version)
- Whether to upgrade (based on changelog for relevant version)

## Version Relationship Examples

### Scenario 1: Add-on Update Only

```
Before: Addon 1.0.0 + Core 3.1.7
After:  Addon 1.1.0 + Core 3.1.7

Change: Added new configuration option for custom certificate paths
```

### Scenario 2: Core Update Only

```
Before: Addon 1.1.0 + Core 3.1.7
After:  Addon 1.1.1 + Core 3.1.8

Change: Updated to Corosync 3.1.8 with upstream bug fix
```

### Scenario 3: Both Updated

```
Before: Addon 1.1.1 + Core 3.1.8
After:  Addon 2.0.0 + Core 3.2.0

Change: Major add-on rewrite for Corosync 3.2.0 with new features
```

## Checking Versions

### From Home Assistant UI

1. Go to **Supervisor** → **Corosync QNetd**
2. Click **Info** tab
3. See version: `1.0.0`

### From Add-on Logs

```
s6-rc: info: service init-corosync: starting
-----------------------------------------------------------
 Corosync QNetd Add-on
 Add-on Version: 1.0.0
 Corosync Version: 3.1.7
-----------------------------------------------------------
```

### From Command Line

```bash
# Check addon version
curl -s http://supervisor/addons/local_corosyncd/info \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
  | jq -r '.data.version'

# Check Docker labels
docker inspect local_corosyncd \
  | jq -r '.[0].Config.Labels["io.hass.version"]'
docker inspect local_corosyncd \
  | jq -r '.[0].Config.Labels["io.hass.corosync.version"]'
```

### From Container

```bash
# Connect to container
docker exec -it addon_local_corosyncd bash

# Check environment variables
echo $ADDON_VERSION     # 1.0.0
echo $COROSYNC_VERSION  # 3.1.7

# Check Corosync binary version
corosync-qnetd -v
```

## Compatibility Matrix

| Addon Version | Core Version | Proxmox VE | Home Assistant | Notes |
|--------------|--------------|------------|----------------|-------|
| 1.0.0 | 3.1.7 | 7.x, 8.x | 2023.1+ | Initial release |

**Note:** This matrix will be expanded as new versions are released.

## Version Update Policy

### Addon Version Updates

**When to update:**
- New features requested/implemented
- Configuration schema changes
- Bug fixes
- Documentation improvements
- Security patches to add-on

**Release cycle:**
- As needed (no fixed schedule)
- Security updates: Immediate
- Feature updates: When stable

### Core Version Updates

**When to update:**
- New stable Corosync release available
- Security vulnerabilities in current version
- Bug fixes that affect functionality
- Compatibility with new Proxmox versions

**Testing before release:**
- Build verification
- Integration tests with Proxmox
- Security scanning
- Compatibility verification

## Deprecation Policy

When either version requires breaking changes:

1. **Announce** deprecation in CHANGELOG
2. **Document** migration path
3. **Provide** transition period (1-2 versions)
4. **Update** MAJOR version number
5. **Support** old version for 6 months minimum

## Historical Versions

| Date | Addon | Core | Notes |
|------|-------|------|-------|
| 2025-01-06 | 1.0.0 | 3.1.7 | Initial secure release |

---

## Related Documentation

- [CHANGELOG.md](CHANGELOG.md) - Detailed change history
- [README.md](README.md) - Current version information
- [DOCS.md](DOCS.md) - Version-specific documentation
- [Corosync Releases](https://github.com/corosync/corosync/releases) - Upstream version history

## Questions?

- **Q: Which version should I care about?**
  - A: Both. Addon version affects configuration, Core version affects Proxmox compatibility.

- **Q: Can I downgrade versions?**
  - A: Addon version yes (reinstall). Core version requires container rebuild.

- **Q: Do I need to reconfigure Proxmox when updating?**
  - A: Usually no, unless CHANGELOG mentions breaking changes.

- **Q: How do I know if an update is safe?**
  - A: Check CHANGELOG for breaking changes and test in non-production first.

