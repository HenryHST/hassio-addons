# Home Assistant Add-on: Network UPS Tools

[![Release](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/henryhst/hassio-addons/tree/v1.0.0) ![Project Maintenance](https://img.shields.io/maintenance/yes/2025.svg)

[![Discord](https://img.shields.io/discord/478094546522079232.svg)](https://discord.me/hassioaddons) [![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/community-hass-io-add-on-network-ups-tools/68516)

A Network UPS Tools daemon to allow you to easily manage battery backup (UPS)
devices connected to your Home Assistant machine.

**Version Information:**
- Add-on Version: 1.0.0 (Home Assistant integration)
- NUT Core: 2.8.1-5

> **Note**: The add-on version is independent of the NUT core version. The add-on version tracks 
> changes to the Home Assistant integration, while the core version indicates the underlying Network 
> UPS Tools version being used.

## About

The primary goal of the Network UPS Tools (NUT) project is to provide support
for Power Devices, such as Uninterruptible Power Supplies, Power Distribution
Units, Automatic Transfer Switch, Power Supply Units and Solar Controllers.

NUT provides many control and monitoring [features](https://networkupstools.org/features.html), with a
uniform control and management interface.

More than 140 different manufacturers, and several thousands models
are [compatible](https://networkupstools.org/stable-hcl.html).

The Network UPS Tools (NUT) project is the combined effort of
many [individuals and companies](https://networkupstools.org/acknowledgements.html).

Be sure to add the NUT integration after starting the add-on.

For more information on how to configure the NUT Sensor in Home Assistant
see the [NUT integration documentation](https://www.home-assistant.io/integrations/nut/).

## Features

- **Monitor UPS Devices**: Monitor local and remote UPS devices
- **SSL/TLS Support**: New SSL certificate verification and forced encryption
- **Home Assistant Integration**: Automatic event notifications to Home Assistant
- **Multi-mode Operation**: Support for both netserver and netclient modes
- **Wide Device Support**: 140+ manufacturers, thousands of models
- **Hardware Support**: UART, USB, and UDEV support

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Network UPS Tools" add-on
3. Configure your UPS devices and users (see documentation)
4. Start the add-on
5. Add the NUT integration in Home Assistant

## Configuration

**Note**: _Remember to restart the add-on when the configuration is changed._

Example configuration:

```yaml
users:
  - username: nutty
    password: changeme
    instcmds:
      - all
    actions: []
devices:
  - name: myups
    driver: usbhid-ups
    port: auto
    config: []
mode: netserver
shutdown_host: "false"
certverify: 0
forcessl: 0
```

**Note**: _This is just an example, don't copy and paste it! Create your own!_

For detailed configuration options, see the [full documentation](https://github.com/henryhst/hassio-addons/blob/master/nut/DOCS.md).

## SSL/TLS Support (New in 1.0.0)

This add-on now supports SSL/TLS for secure UPS monitoring:

### CERTVERIFY
Enable certificate verification for all upsd connections:
```yaml
certverify: 1
```

### FORCESSL
Force SSL-encrypted connections to upsd servers:
```yaml
forcessl: 1
```

**Important**: Both parameters require upsd servers to have SSL properly configured.

## Support

Got questions?

You have several options to get them answered:

- The [netboot.xyz Discord](https://discord.me/hassioaddons)
- The [Home Assistant Community Forum](https://community.home-assistant.io/t/community-hass-io-add-on-network-ups-tools/68516)
- [Open an issue on GitHub](https://github.com/henryhst/hassio-addons/issues)

## Authors & Contributors

This add-on is maintained by henryhst.

The original setup was by Dale Higgs.

For a full list of all authors and contributors,
check [the contributor's page](https://github.com/henryhst/hassio-addons/graphs/contributors).

## License

MIT License

Copyright (c) 2025 henryhst

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[discord]: https://discord.me/hassioaddons
[forum]: https://community.home-assistant.io/t/community-hass-io-add-on-network-ups-tools/68516



