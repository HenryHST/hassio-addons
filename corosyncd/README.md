# Home Assistant Add-on: Corosync QNetd

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Supports aarch64 Architecture](https://img.shields.io/badge/aarch64-yes-green.svg)
![Supports amd64 Architecture](https://img.shields.io/badge/amd64-yes-green.svg)
![Supports armv7 Architecture](https://img.shields.io/badge/armv7-yes-green.svg)

Corosync QNetd (Quorum Network Daemon) for Home Assistant - provides an external vote for Proxmox VE cluster quorum calculations.

## About

This add-on runs **Corosync QNetd**, a daemon that provides a quorum vote to Corosync-based clusters (particularly Proxmox VE). It's essential for:

- **2-node Proxmox VE clusters**: Provides the third vote needed for quorum
- **Even-numbered clusters**: Prevents split-brain scenarios in 2, 4, 6+ node clusters
- **High availability**: Ensures cluster remains operational even when network partitions occur

### What is Corosync QNetd?

Corosync QNetd is an external quorum device that helps clusters make decisions when nodes can't reach each other. In a 2-node cluster, if the nodes lose connection, neither can determine which should continue operating. QNetd provides an external "tie-breaker" vote.

**Example Scenario:**
```
Node A ──────X────── Node B
              │
              │ (network split)
              │
           QNetd
           (decides which node continues)
```

### Key Features

- ✅ **Secure**: No SSH server, no hardcoded passwords
- ✅ **Multi-architecture**: Supports aarch64, amd64, armv7
- ✅ **Configurable**: Adjustable port and log level
- ✅ **Health monitoring**: Built-in health checks
- ✅ **Dual versioning**: Track addon and Corosync versions separately

## Installation

1. Navigate to **Supervisor** → **Add-on Store** in Home Assistant
2. Add this repository: `https://github.com/henryhst/hassio-addons`
3. Find **Corosync QNetd** in the add-on list
4. Click **Install**
5. Configure the add-on (see Configuration section)
6. Start the add-on
7. Check the logs to verify startup

## Configuration

### Basic Configuration

```yaml
qnetd_port: 5403
log_level: info
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `qnetd_port` | port | `5403` | Port for Corosync QNetd service |
| `log_level` | list | `info` | Log verbosity: `trace`, `debug`, `info`, `notice`, `warning`, `error`, `fatal` |
| `tls_enabled` | bool | `false` | Enable TLS support (future feature) |

### Example Configurations

**Minimal (default values):**
```yaml
qnetd_port: 5403
log_level: info
```

**Debug mode:**
```yaml
qnetd_port: 5403
log_level: debug
```

## Proxmox VE Integration

### Step 1: Install and Start the Add-on

Install and start the Corosync QNetd add-on in Home Assistant.

### Step 2: Configure Proxmox Cluster

On **one** Proxmox node, run:

```bash
# Add QNetd device to cluster
pvecm qdevice setup <HOME_ASSISTANT_IP>

# Verify QNetd status
pvecm status
```

You should see output showing the QNetd device:

```
Quorum information
------------------
Qdevice:
  Model:            Net
  Node ID:          1
  Configured:       Yes
  Member:           Yes
```

### Step 3: Verify Connection

Check that all nodes can reach QNetd:

```bash
# On each Proxmox node
corosync-qdevice-tool -s
```

### Network Requirements

- **Port 5403/TCP**: Must be accessible from all Proxmox cluster nodes
- **Firewall**: Ensure Home Assistant firewall allows port 5403
- **Network stability**: QNetd should be on a separate network segment from cluster nodes

## Troubleshooting

### QNetd not accessible from Proxmox

**Symptoms:** `pvecm qdevice setup` fails with connection timeout

**Solution:**
1. Check add-on logs for errors
2. Verify port 5403 is exposed in add-on configuration
3. Check Home Assistant firewall/network settings
4. Test connectivity: `nc -zv <HOME_ASSISTANT_IP> 5403` from Proxmox node

### Cluster loses quorum despite QNetd

**Symptoms:** Cluster shows "No quorum" even with QNetd running

**Solution:**
1. Check QNetd status on Proxmox: `pvecm status`
2. Verify QNetd is configured: `pvecm qdevice status`
3. Check network connectivity between all nodes and QNetd
4. Review Corosync logs: `journalctl -u corosync`

### Debug logging

Enable debug mode for detailed logs:

```yaml
log_level: debug
```

Then check add-on logs for detailed connection information.

## Version Information

This add-on uses **dual versioning**:

- **Addon Version** (1.0.0): Add-on features, configuration options, bug fixes
- **Corosync Core Version** (3.1.7): Upstream Corosync QNetd version

Both versions are displayed in:
- Add-on startup logs
- Add-on info panel
- Container labels

See [VERSIONING.md](VERSIONING.md) for details.

## Architecture Support

This add-on supports the following architectures:

- `aarch64` (ARM 64-bit) - Raspberry Pi 4, etc.
- `amd64` (x86-64) - Most PCs, Intel NUC, etc.
- `armv7` (ARM 32-bit) - Raspberry Pi 3, etc.

## Security

This add-on follows security best practices:

- ✅ No SSH server (removed in v1.0.0)
- ✅ No hardcoded passwords
- ✅ Security updates applied during build
- ✅ Minimal package installation
- ✅ Non-root execution where possible
- ✅ Regular security scanning with Trivy

See [SECURITY.md](../SECURITY.md) for vulnerability reporting.

## Support

- **Documentation**: [DOCS.md](DOCS.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/henryhst/hassio-addons/issues)
- **Repository**: [GitHub](https://github.com/henryhst/hassio-addons)

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

## License

MIT License - see repository for details.

## Credits

- **Corosync Project**: https://corosync.github.io/corosync/
- **Proxmox VE**: https://www.proxmox.com/
- **Home Assistant**: https://www.home-assistant.io/

---

**Disclaimer**: This is an unofficial add-on. It is not affiliated with or endorsed by the Corosync project or Proxmox VE.

