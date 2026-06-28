# Home Assistant Add-on: Chrony NTP

An NTP server accessible by devices on your local network. The add-on synchronizes time from upstream NTP pools or servers and can update the Home Assistant host system clock.

Based on the [Home Assistant Community Add-on: chrony](https://github.com/hassio-addons/addon-chrony), extended with NTS, optional PTP, persistent drift storage, and ESP32 reference-clock firmware projects.

## Installation

1. Add this repository to the Home Assistant add-on store
2. Install **Chrony NTP**
3. Configure mode and upstream servers (see below)
4. Start the add-on

## Configuration

Example (server mode):

```yaml
set_system_clock: true
mode: server
ntp_server:
  - de.pool.ntp.org
  - briareus.schulte.org
enable_nts: false
enable_ptp: false
log_level: info
```

Example (pool mode):

```yaml
set_system_clock: true
mode: pool
ntp_pool: pool.ntp.org
```

### Option: `log_level`

Controls bashio log verbosity: `trace`, `debug`, `info`, `notice`, `warning`, `error`, `fatal`. Default: `info`.

### Option: `set_system_clock`

When `true`, chronyd may step the host system clock. When `false`, chronyd runs with `-x` (no clock control). Requires `privileged: SYS_TIME` (enabled by default).

### Option: `mode`

- `pool` — use `ntp_pool` (DNS pool, recommended)
- `server` — use `ntp_server` list (specific hostnames or IPs)

### Option: `ntp_pool`

Pool DNS name when `mode: pool` (e.g. `pool.ntp.org`, `de.pool.ntp.org`).

### Option: `ntp_server`

List of upstream servers when `mode: server`. Example:

```yaml
ntp_server:
  - briareus.schulte.org
  - de.pool.ntp.org
```

### Option: `enable_nts`

Append `nts` to upstream `pool`/`server` lines. All upstream servers must support NTS.

### Option: `enable_ptp`

Add `refclock PHC /dev/ptp0` only when explicitly enabled. Map the device in the add-on configuration:

```yaml
enable_ptp: true
devices:
  - /dev/ptp0
```

## Migration from 1.x

Version 2.0 replaces the `ntp_servers` string with community-style options:

| 1.x | 2.0 |
|-----|-----|
| `ntp_servers: "a;b"` or `"a,b"` | `mode: server` and `ntp_server: [a, b]` |
| `enable_sysclk: true` | `set_system_clock: true` |
| `noclientlog`, `timezone`, `log_level: 0` | use `log_level: info` (bashio levels) |

## Testing

From a client on your LAN:

```bash
ntpdate -q <HOME_ASSISTANT_IP>
```

Or:

```bash
chronyc -h <HOME_ASSISTANT_IP> tracking
```

## ESP32 Reference Clocks

Firmware sketches for GPS/PPS reference clocks live in [`ESP32/`](ESP32/). They are not built into the add-on image.

## Support

- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/henryhst/hassio-addons/issues)

## License

MIT License
