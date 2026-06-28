# Home Assistant Add-on: Chrony NTP

An NTP server accessible by devices on your local network. The add-on synchronizes time from upstream NTP pools and/or servers and can update the Home Assistant host system clock.

Based on the [Home Assistant Community Add-on: chrony](https://github.com/hassio-addons/addon-chrony), extended with simultaneous pool+server configuration ([PR #215](https://github.com/hassio-addons/addon-chrony/pull/215)), NTS, optional PTP, persistent drift storage, and ESP32 firmware projects.

## Installation

1. Add this repository to the Home Assistant add-on store
2. Install **Chrony NTP**
3. Configure `ntp_pool` and/or `ntp_server` (see below)
4. Start the add-on

## Configuration

Pool and explicit servers can be used **at the same time** (e.g. public pool plus a local server):

```yaml
set_system_clock: true
ntp_pool: pool.ntp.org
ntp_server:
  - briareus.schulte.org
  - de.pool.ntp.org
pool_maxsources: 4
enable_nts: false
enable_ptp: false
log_level: info
```

Pool only:

```yaml
set_system_clock: true
ntp_pool: de.pool.ntp.org
ntp_server: []
```

Servers only:

```yaml
set_system_clock: true
ntp_pool: ""
ntp_server:
  - de.pool.ntp.org
```

### Option: `log_level`

Controls bashio log verbosity: `trace`, `debug`, `info`, `notice`, `warning`, `error`, `fatal`. Default: `info`.

### Option: `set_system_clock`

When `true`, chronyd may step the host system clock. When `false`, chronyd runs with `-x` (no clock control). Requires `privileged: SYS_TIME` (enabled by default).

### Option: `mode`

Deprecated and ignored since 2.1.0. Configure `ntp_pool` and/or `ntp_server` directly.

### Option: `ntp_pool`

DNS name of an NTP pool (e.g. `pool.ntp.org`, `de.pool.ntp.org`). Set to empty string to disable:

```yaml
ntp_pool: ""
```

### Option: `ntp_server`

List of upstream server hostnames or IPs. Set to empty list to disable:

```yaml
ntp_server: []
```

At least one of `ntp_pool` or `ntp_server` must be configured.

### Option: `pool_maxsources`

Number of servers to select from the pool DNS record (1–16). Default: `4`.

### Option: `enable_nts`

Append `nts` to upstream `pool` and `server` lines. All upstream sources must support NTS.

### Option: `enable_ptp`

Add `refclock PHC /dev/ptp0` only when explicitly enabled. Map the device in the add-on configuration:

```yaml
enable_ptp: true
devices:
  - /dev/ptp0
```

### Option: `enable_prometheus`

When `true`, starts [chrony_exporter](https://github.com/SuperQ/chrony_exporter) alongside chronyd and exposes Prometheus metrics on `prometheus_port` (default `9123`). Default: `false`.

```yaml
enable_prometheus: true
prometheus_port: 9123
```

The endpoint (`/metrics`) has no authentication by default — only enable on trusted networks or place Prometheus in the same LAN.

### Option: `prometheus_port`

TCP port for the metrics HTTP server (1024–65535). Default: `9123`. The add-on maps this port to the host; note the assigned port under **Info** after start.

## Prometheus and Grafana

1. Set `enable_prometheus: true` and restart the add-on.
2. Note the host port for `9123/tcp` under add-on **Info**.
3. Add a scrape job to Prometheus (HA Prometheus add-on or external):

```yaml
scrape_configs:
  - job_name: chronyd
    static_configs:
      - targets: ['<HA-HOST>:<PORT>']
```

Useful metrics for dashboards and alerts:

| Metric | Meaning |
|--------|---------|
| `chrony_tracking_last_offset_seconds` | Last clock offset |
| `chrony_tracking_rms_offset_seconds` | RMS offset (stability) |
| `chrony_tracking_stratum` | Stratum (16 = not synchronized) |
| `chrony_sources_state` | Upstream source reachability |
| `chrony_serverstats_*` | NTP requests from LAN clients |

Community Grafana dashboards for `chrony_exporter` work out of the box. See the [chrony_exporter README](https://github.com/SuperQ/chrony_exporter) for recording rules (e.g. clock error bounds).

## Migration

### From 2.0.x

Remove `mode`. Use both fields as needed:

| 2.0.x | 2.1.0 |
|-------|-------|
| `mode: pool` + `ntp_pool: x` | `ntp_pool: x` (optional `ntp_server: []`) |
| `mode: server` + `ntp_server: [...]` | `ntp_server: [...]` (optional `ntp_pool: ""`) |
| Pool + local server (not possible) | `ntp_pool` + `ntp_server` together |

### From 1.x

| 1.x | 2.1.0 |
|-----|-------|
| `ntp_servers: "a;b"` | `ntp_server: [a, b]` (and optional `ntp_pool`) |
| `enable_sysclk: true` | `set_system_clock: true` |

## Testing

```bash
ntpdate -q <HOME_ASSISTANT_IP>
chronyc -h <HOME_ASSISTANT_IP> tracking
```

## ESP32 Reference Clocks

Firmware sketches live in [`ESP32/`](ESP32/).

## Support

- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/henryhst/hassio-addons/issues)

## License

MIT License
