# Home Assistant Add-on: Chrony NTP

**Add-on Version**: 1.0.0

## About

[Chrony](https://chrony-project.org/) is a versatile NTP implementation. This add-on:

- Synchronizes the container clock from upstream NTP servers
- Serves time to LAN clients on **UDP port 123** (`allow all`)
- Persists the frequency drift file under `/data/chronyd/lib`

Migrated from the standalone project [ha-chronyd](https://github.com/HenryHST/ha-chronyd).

## Installation

1. Add repository `https://github.com/henryhst/hassio-addons`
2. Install **Chrony NTP**
3. Adjust configuration if needed
4. Start the add-on

Ensure no other service on the host already binds UDP 123, or map a different host port in the add-on network settings.

## Configuration Options

### `ntp_servers`

Comma- or semicolon-separated list of upstream NTP servers. Default: global NTP pool.

Examples:

```yaml
ntp_servers: "time.cloudflare.com"
ntp_servers: "de.pool.ntp.org,ch.pool.ntp.org"
ntp_servers: "briareus.schulte.org;de.pool.ntp.org"
ntp_servers: "127.127.1.1"   # local clock, stratum 10
```

### `enable_nts`

Enable Network Time Security (NTS) for upstream servers. All configured servers must support NTS.

### `enable_sysclk`

Allow chronyd to adjust the **system** clock (not only track offset). Default: `false`.

**Important:** On Home Assistant this requires elevated privileges. If enabled, you may need to set `privileged: true` or `full_access: true` in the add-on's advanced configuration. The add-on logs a warning when this option is enabled.

### `noclientlog`

When `true`, client accesses are not logged (disables `chronyc clients` statistics).

### `log_level`

Chrony log verbosity: `0` (info) through `3` (fatal only).

### `timezone`

Container timezone (`TZ`), e.g. `Europe/Berlin`. Default: `UTC`.

### `enable_ptp`

When `true`, the add-on expects `/dev/ptp0` for a PTP hardware clock reference. If the device is missing, a warning is logged. PTP often requires `privileged: true` on Home Assistant OS.

## Network

| Port | Protocol | Purpose |
|------|----------|---------|
| 123 | UDP | NTP server for LAN clients |

By default `host_network` is **false**; port mapping is used. For some advanced setups (broadcast clients), `host_network: true` may be required — change only if you understand the impact on port conflicts with the host NTP service.

## Testing

From another machine:

```bash
ntpdate -q <HOME_ASSISTANT_IP>
```

Inside the add-on terminal (Supervisor):

```bash
chronyc tracking
chronyc sources
```

## ESP32 Reference Clock

Firmware for GPS/PPS-based reference clocks is included for hardware projects:

| Path | Description |
|------|-------------|
| `ESP32/ESP32-C3/` | ESP32-C3 sketches (NMEA, tiny NTP server) |
| `ESP32/ESP32-Ethernet/` | Ethernet PPS approach |
| `ESP32/readme.md` | Brief overview |

These sketches are **not** flashed or built by the add-on. Use [PlatformIO](https://platformio.org/) or Arduino IDE separately.

## Security Notes

- `allow all` permits any client to query this NTP server — restrict at the firewall if needed
- Prefer NTS upstream servers when using `enable_nts: true`
- Keep `enable_sysclk: false` unless you explicitly need host clock discipline

## Backup

Drift data is stored under `/data/chronyd/` (`backup: cold`). Include in Home Assistant backups.

## Version Information

- **Add-on Version**: 1.0.0
- **Chrony Version**: shown in startup logs (`CHRONY_VERSION`)

See [VERSIONING.md](VERSIONING.md).
