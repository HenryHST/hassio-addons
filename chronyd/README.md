# Home Assistant Add-on: Chrony NTP

**Add-on Version**: 1.0.0

## About

This add-on runs [Chrony](https://chrony-project.org/) as an NTP server inside Home Assistant. It synchronizes time from upstream NTP servers and can serve time to devices on your LAN (UDP port 123).

Originally developed as [ha-chronyd](https://github.com/HenryHST/ha-chronyd); now maintained as a Home Assistant add-on in this repository.

## Installation

1. Add this repository to the Home Assistant add-on store
2. Install **Chrony NTP**
3. Configure NTP servers (or keep defaults)
4. Start the add-on

## Configuration

```yaml
ntp_servers: "0.pool.ntp.org,1.pool.ntp.org,2.pool.ntp.org,3.pool.ntp.org"
enable_nts: false
enable_sysclk: false
noclientlog: false
log_level: 0
timezone: UTC
enable_ptp: false
```

See [DOCS.md](DOCS.md) for all options.

## Testing

From a client on your LAN:

```bash
ntpdate -q <HOME_ASSISTANT_IP>
```

## ESP32 Reference Clocks

Firmware sketches for GPS/PPS reference clocks live in [`ESP32/`](ESP32/). They are not built into the add-on image.

## Support

- **Documentation**: [DOCS.md](DOCS.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/henryhst/hassio-addons/issues)

## License

MIT License
