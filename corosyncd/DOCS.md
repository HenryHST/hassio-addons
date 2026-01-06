# Corosync QNetd - Complete Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [What is Corosync QNetd?](#what-is-corosync-qnetd)
3. [Configuration](#configuration)
4. [Proxmox VE Integration](#proxmox-ve-integration)
5. [Network Requirements](#network-requirements)
6. [Certificate Management](#certificate-management)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)
9. [Version Information](#version-information)

## Introduction

Corosync QNetd (Quorum Network Daemon) is an external quorum device for Corosync-based clusters. This add-on makes it easy to run QNetd on your Home Assistant instance, providing a reliable quorum vote for Proxmox VE clusters.

## What is Corosync QNetd?

### The Problem: Split-Brain in 2-Node Clusters

In a 2-node cluster, if the nodes lose network connectivity, each node thinks the other has failed. Both nodes might try to take over resources, leading to data corruption (split-brain).

```
Before Network Split:
Node A ←→ Node B
(Both active, quorum = 2/2)

After Network Split:
Node A     X     Node B
(No quorum: 1/2)  (No quorum: 1/2)
```

### The Solution: External Quorum Device

QNetd provides an external "tie-breaker" vote:

```
Network Split with QNetd:
           QNetd
           ↙  ↘
Node A     X     Node B
(Quorum: 2/3) ✓  (No quorum: 1/3) ✗
```

Node A maintains quorum because it can reach QNetd, while Node B loses quorum and stops.

### Use Cases

1. **2-Node Proxmox VE Clusters**
   - Most common use case
   - Provides the critical third vote
   - Enables true high availability

2. **Even-Numbered Clusters**
   - 2, 4, 6, etc. node clusters
   - Prevents 50/50 split scenarios
   - Adds external arbitration

3. **Geographic Distribution**
   - Clusters across different locations
   - QNetd in a third location
   - Protects against site failures

## Configuration

### Configuration Options

#### `qnetd_port`

**Type:** `port`  
**Default:** `5403`  
**Description:** TCP port for Corosync QNetd service.

**Note:** Corosync QNetd typically uses port 5403 by default. Changing this requires additional configuration on both the QNetd side and the Proxmox cluster side.

```yaml
qnetd_port: 5403  # Default, recommended
```

#### `log_level`

**Type:** `list(trace|debug|info|notice|warning|error|fatal)`  
**Default:** `info`  
**Description:** Controls log verbosity.

**Levels:**
- `trace`: Most verbose, includes all internal operations
- `debug`: Detailed debugging information
- `info`: Normal operational messages (recommended)
- `notice`: Notable events
- `warning`: Warning conditions
- `error`: Error conditions
- `fatal`: Critical errors only

```yaml
log_level: info  # Production
log_level: debug  # Troubleshooting
```

#### `tls_enabled`

**Type:** `bool`  
**Default:** `false`  
**Description:** Enable TLS encryption for QNetd connections (future feature).

**Note:** Currently under development. When enabled, requires certificate setup.

```yaml
tls_enabled: false  # Currently not implemented
```

### Example Configurations

#### Production Configuration

```yaml
qnetd_port: 5403
log_level: info
```

#### Debug Configuration

```yaml
qnetd_port: 5403
log_level: debug
```

## Proxmox VE Integration

### Prerequisites

- Home Assistant with Corosync QNetd add-on installed and running
- Proxmox VE cluster (2 or more nodes)
- Network connectivity between all Proxmox nodes and Home Assistant
- SSH access to Proxmox nodes

### Step-by-Step Setup

#### Step 1: Verify Add-on Status

In Home Assistant:
1. Go to **Supervisor** → **Corosync QNetd**
2. Verify the add-on is **Started**
3. Check logs for startup message:
   ```
   -----------------------------------------------------------
    Corosync QNetd Add-on
    Add-on Version: 1.0.0
    Corosync Version: 3.1.7
   -----------------------------------------------------------
   [corosync-qnetd] Starting Corosync QNetd daemon...
   ```

#### Step 2: Note Home Assistant IP Address

You'll need the IP address of your Home Assistant instance. Find it in:
- **Settings** → **System** → **Network**
- Or check your router/DHCP server

Example: `192.168.1.100`

#### Step 3: Configure QNetd on Proxmox

**On any ONE Proxmox node** (run these commands):

```bash
# Install QNetd client tools (if not already installed)
apt update
apt install corosync-qnetd

# Add QNetd device to your cluster
pvecm qdevice setup 192.168.1.100

# This will:
# - Generate certificates
# - Configure corosync-qdevice on all nodes
# - Restart corosync service
```

**Expected output:**
```
corosync-qdevice certificate request
INFO: qdevice client cert request sent to qnetd server 192.168.1.100
INFO: qdevice client cert received from qnetd server 192.168.1.100
corosync-qdevice enable on boot
corosync-qdevice configure
```

#### Step 4: Verify QNetd Configuration

```bash
# Check cluster status
pvecm status

# Look for Qdevice section:
# Qdevice:
#   Model:            Net
#   Node ID:          1
#   Configured:       Yes
#   Member:           Yes
```

```bash
# Check qdevice status specifically
pvecm qdevice status

# Expected output:
# Qdevice configured:     Yes
# Qdevice active:         Yes
```

```bash
# Check corosync-qdevice service
corosync-qdevice-tool -s

# Expected output shows connection to QNetd
```

#### Step 5: Test Quorum

```bash
# Check current quorum status
pvecm status | grep -A 10 "Quorum information"

# With 2-node cluster + QNetd:
# Expected votes:   3
# Total votes:      3
# Quorum:           2
```

### Cluster Sizes and Quorum

| Cluster Nodes | Without QNetd | With QNetd | Votes Needed |
|--------------|---------------|------------|--------------|
| 2 nodes | No HA (need both) | 3 votes total | 2 votes |
| 3 nodes | 3 votes total | 4 votes total | 2 votes |
| 4 nodes | 4 votes total | 5 votes total | 3 votes |

### Removing QNetd

If you need to remove QNetd from your cluster:

```bash
# On any Proxmox node
pvecm qdevice remove
```

## Network Requirements

### Port Configuration

**Required Open Ports:**

| Port | Protocol | Direction | Purpose |
|------|----------|-----------|---------|
| 5403 | TCP | Proxmox → HA | Corosync QNetd |

### Firewall Configuration

#### Home Assistant Firewall

If Home Assistant has a firewall enabled:

```bash
# Allow port 5403 from Proxmox nodes
# (Example for UFW firewall)
ufw allow from 192.168.1.0/24 to any port 5403 proto tcp
```

#### Proxmox Firewall

If using Proxmox Datacenter firewall:

1. Go to **Datacenter** → **Firewall** → **Add**
2. Create rule:
   - **Direction:** out
   - **Action:** ACCEPT
   - **Protocol:** TCP
   - **Dest. port:** 5403
   - **Comment:** Corosync QNetd

### Network Topology Best Practices

1. **QNetd Placement**
   - Ideally on a separate network segment
   - NOT on the same network as cluster nodes
   - Protects against network-wide failures

2. **Network Redundancy**
   - Consider redundant network paths
   - QNetd should be on reliable network
   - Avoid single points of failure

3. **Latency Considerations**
   - Keep latency low (<50ms recommended)
   - High latency can affect cluster performance
   - Test with: `ping -c 100 <QNETD_IP>`

## Certificate Management

### Automatic Certificate Generation

Corosync QNetd uses TLS certificates for secure communication. Certificates are automatically generated during setup:

1. **QNetd Server Certificate**: Generated when add-on first starts
2. **Node Certificates**: Generated during `pvecm qdevice setup`

### Certificate Locations

**On QNetd (Home Assistant):**
```
/var/run/corosync-qnetd/
├── nssdb/           # NSS database with certificates
└── corosync-qnetd.cert
```

**On Proxmox Nodes:**
```
/etc/corosync/qdevice/net/
├── nssdb/           # NSS database
└── cert8.db         # Certificate database
```

### Certificate Renewal

Certificates are typically valid for 1 year. To renew:

```bash
# On Proxmox nodes
pvecm qdevice remove
pvecm qdevice setup <QNETD_IP>
```

### Manual Certificate Management

Advanced users can manage certificates manually:

```bash
# View certificates on QNetd
certutil -L -d /var/run/corosync-qnetd/nssdb

# View certificates on Proxmox
certutil -L -d /etc/corosync/qdevice/net/nssdb
```

## Troubleshooting

### Issue: QNetd not accessible from Proxmox

**Symptoms:**
- `pvecm qdevice setup` fails with "Connection refused" or timeout
- `corosync-qdevice-tool -s` shows no connection

**Diagnosis:**
```bash
# From Proxmox node, test connectivity
nc -zv <HOME_ASSISTANT_IP> 5403

# Check add-on logs in Home Assistant
```

**Solutions:**
1. Verify add-on is running and started
2. Check Home Assistant firewall allows port 5403
3. Verify network connectivity (ping test)
4. Check add-on configuration for correct port
5. Review add-on logs for errors

### Issue: Cluster loses quorum despite QNetd

**Symptoms:**
- Cluster shows "No quorum" in `pvecm status`
- Qdevice shows as disconnected

**Diagnosis:**
```bash
# Check qdevice status
pvecm qdevice status
corosync-qdevice-tool -s

# Check corosync logs
journalctl -u corosync -f
journalctl -u corosync-qdevice -f
```

**Solutions:**
1. Verify QNetd is running in Home Assistant
2. Check network connectivity between nodes and QNetd
3. Restart corosync-qdevice: `systemctl restart corosync-qdevice`
4. Check certificate validity
5. Review Corosync configuration: `cat /etc/corosync/corosync.conf`

### Issue: Certificate errors

**Symptoms:**
- Error messages about NSS database or certificates
- `pvecm qdevice setup` fails with certificate error

**Solutions:**
```bash
# Remove existing certificates and re-setup
pvecm qdevice remove
rm -rf /etc/corosync/qdevice/net/nssdb
pvecm qdevice setup <QNETD_IP>
```

### Issue: High latency warnings

**Symptoms:**
- Corosync logs show latency warnings
- Cluster performance degraded

**Diagnosis:**
```bash
# Test latency to QNetd
ping -c 100 <QNETD_IP>
# Latency should be consistently <50ms
```

**Solutions:**
1. Check network path between Proxmox and Home Assistant
2. Consider moving QNetd to better network location
3. Check for network congestion
4. Verify Home Assistant system performance

### Debug Mode

Enable debug logging for detailed troubleshooting:

```yaml
log_level: debug
```

This provides detailed connection information, certificate exchanges, and voting decisions in the add-on logs.

## Advanced Usage

### Multiple Clusters

One QNetd instance can serve multiple Proxmox clusters:

- Each cluster gets its own certificate
- QNetd tracks votes independently per cluster
- Scales to many clusters without issues

**Setup:**
```bash
# Cluster 1
pvecm qdevice setup <QNETD_IP>

# Cluster 2 (different cluster)
pvecm qdevice setup <QNETD_IP>
```

### Monitoring QNetd

Monitor QNetd health through Home Assistant:

1. **Add-on Logs**: Real-time operation logs
2. **Health Check**: Built-in health monitoring (30s interval)
3. **System Monitor**: CPU/memory usage in Supervisor

### Backup and Recovery

#### Backup

QNetd configuration is stored in the add-on's persistent data directory. To backup:

1. Create Home Assistant backup
2. Or manually backup: `/usr/share/hassio/addons/data/<addon>/`

#### Recovery

Restore from Home Assistant backup, or:

```bash
# On Proxmox nodes, simply reconfigure
pvecm qdevice setup <QNETD_IP>
```

### High Availability for QNetd

For critical setups, consider:

1. **Run QNetd on dedicated hardware** (not Home Assistant)
2. **Multiple QNetd instances** with Proxmox cluster updates
3. **Monitor QNetd availability** with external tools

## Version Information

This add-on uses **dual versioning**:

### Addon Version (1.0.0)

Tracks Home Assistant add-on features:
- Configuration options
- Integration improvements
- Bug fixes
- Security updates

### Corosync Core Version (3.1.7)

Tracks upstream Corosync QNetd version:
- Core QNetd functionality
- Protocol improvements
- Upstream bug fixes

Both versions are displayed:
- In add-on startup logs
- In add-on info panel
- As Docker container labels

See [VERSIONING.md](VERSIONING.md) for complete versioning strategy.

---

## Additional Resources

- **Corosync Documentation**: https://corosync.github.io/corosync/
- **Proxmox VE Cluster**: https://pve.proxmox.com/wiki/Cluster_Manager
- **Proxmox QDevice**: https://pve.proxmox.com/wiki/Cluster_Manager#_corosync_external_vote_support
- **Home Assistant Add-ons**: https://developers.home-assistant.io/docs/add-ons

## Support

For issues, questions, or contributions:

- **GitHub Issues**: https://github.com/henryhst/hassio-addons/issues
- **Documentation**: This file and [README.md](README.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
