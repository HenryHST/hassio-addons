# Home Assistant Add-on: Chrony NTP

**Add-on Version**: 2.2.0

## About

This add-on runs [Chrony](https://chrony-project.org/) as an NTP server inside Home Assistant. It synchronizes time from upstream NTP pools and/or servers and serves time to devices on your LAN (UDP port 123).

Architecture follows the [Home Assistant Community Add-on: chrony](https://github.com/hassio-addons/addon-chrony) (Debian, bashio, s6-overlay), with extensions from the former [ha-chronyd](https://github.com/HenryHST/ha-chronyd) project.

## Installation

1. Add this repository to the Home Assistant add-on store
2. Install **Chrony NTP**
3. Configure upstream pool and/or servers
4. Start the add-on

## Configuration

```yaml
set_system_clock: true
ntp_pool: pool.ntp.org
ntp_server:
  - briareus.schulte.org
pool_maxsources: 4
enable_nts: false
enable_ptp: false
enable_prometheus: false
log_level: info
```

See [DOCS.md](DOCS.md) for all options and migration notes.

## ESP32 Reference Clocks

Firmware sketches live in [`ESP32/`](ESP32/).

## Support

- **Documentation**: [DOCS.md](DOCS.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/henryhst/hassio-addons/issues)

## License

MIT License
