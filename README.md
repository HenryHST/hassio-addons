# Home Assistant Add-ons by henryhst

![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE)

## About

Home Assistant allows anyone to create add-on repositories to share their
add-ons for Home Assistant easily. This repository is one of those repositories,
providing extra Home Assistant add-ons for your installation.

The primary goal of this project is to provide you (as a Home Assistant user)
with additional, high quality, add-ons that allow you to take your automated
home to the next level.

## Installation

Adding this add-ons repository to your Home Assistant instance is pretty straightforward. Follow the instructions provided on the [Home Assistant website](https://home-assistant.io/hassio/installing_third_party_addons).

Use the following URL to add this repository:

```txt
https://github.com/henryhst/hassio-addons
```

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fhenryhst%2Fhassio-addons)

## Available Add-ons

This repository contains the following add-ons:

### ✓ [netboot.xyz][addon-netboot]

![Version][netboot-version-shield]
![Supports aarch64 Architecture][netboot-aarch64-shield]
![Supports amd64 Architecture][netboot-amd64-shield]
![Supports armv7 Architecture][netboot-armv7-shield]

_Network boot manager for operating systems and utilities_

A convenient place to boot into any type of operating system or utility disk without the need of retrieving the ISO. Includes web interface, TFTP server, and asset hosting.

**Features:**
- Web management interface with Ingress support
- TFTP server for network booting (port 69/UDP)
- HTTP asset hosting server (port 8080)
- Local asset mirroring for faster boot times
- Support for Legacy BIOS and UEFI boot modes
- Multi-architecture support

[:books: Read the full add-on documentation][addon-doc-netboot]

### ✓ [Network UPS Tools (NUT)][addon-nut]

![Version][nut-version-shield]
![Supports aarch64 Architecture][nut-aarch64-shield]
![Supports amd64 Architecture][nut-amd64-shield]
![Supports armv7 Architecture][nut-armv7-shield]

_Manage battery backup (UPS) devices_

Network UPS Tools (NUT) provides support for monitoring and managing Uninterruptible Power Supplies (UPS), Power Distribution Units (PDU), and related power devices.

**Features:**
- Monitor local and remote UPS devices
- SSL/TLS support with certificate verification
- Forced SSL connections for enhanced security
- Home Assistant event integration
- Support for 140+ manufacturers and thousands of models
- UART, USB, and UDEV support

[:books: Read the full add-on documentation][addon-doc-nut]

## Support

Got questions?

You have several options to get them answered:

- The [Home Assistant Community Forum][forum]
- [Open an issue on GitHub][issue]

In case you've found a bug, please [open an issue on GitHub][issue].

## CI/CD & Automation

This repository uses GitHub Actions for continuous integration and deployment:

- **🏗️ Automated Builds**: Docker images are automatically built for all architectures
- **🔏 Image Signing**: All images are signed with Cosign for security
- **✅ Quality Checks**: Automated linting (YAML, Shell, Dockerfile)
- **📦 Multi-Arch Support**: Images for aarch64, amd64, and armv7

### Available Workflows

| Workflow | Description | Trigger |
|----------|-------------|---------|
| Build netboot.xyz | Builds netboot.xyz addon | Push, PR, Release |
| Build NUT | Builds NUT addon | Push, PR, Release |
| Lint | Code quality checks | Push, PR |
| Release | Version management | Release, Manual |

See [.github/workflows/README.md](.github/workflows/README.md) for details.

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

Thank you for being involved! :heart:

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

[addon-doc-netboot]: https://github.com/henryhst/hassio-addons/blob/master/netboot_xyz/DOCS.md
[addon-doc-nut]: https://github.com/henryhst/hassio-addons/blob/master/nut/DOCS.md
[addon-netboot]: https://github.com/henryhst/hassio-addons/tree/master/netboot_xyz
[addon-nut]: https://github.com/henryhst/hassio-addons/tree/master/nut
[forum]: https://community.home-assistant.io
[issue]: https://github.com/henryhst/hassio-addons/issues
[license-shield]: https://img.shields.io/github/license/henryhst/hassio-addons.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2025.svg
[netboot-aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[netboot-amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[netboot-armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[netboot-version-shield]: https://img.shields.io/badge/version-v1.0.0-blue.svg
[nut-aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[nut-amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[nut-armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[nut-version-shield]: https://img.shields.io/badge/version-v1.0.0-blue.svg