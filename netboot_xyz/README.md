# netboot.xyz Home Assistant Add-on

[![Discord](https://img.shields.io/discord/425186187368595466)](https://discord.gg/An6PA2a)

## Overview

This Home Assistant add-on provides a local instance of [netboot.xyz](https://netboot.xyz), allowing you to easily set up network-based OS installations and utility disks. The add-on includes a web interface for managing boot menus and mirroring downloadable assets locally for faster booting.

![netboot.xyz webapp](https://netboot.xyz/images/netboot.xyz-webapp.jpg)

This add-on is ideal for:
- Network-based OS installations without optical drives or USB media
- Testing and developing custom iPXE menus
- Local asset mirroring for faster boot times
- Managing multiple network boot configurations

## Features

- **Web Interface**: Easy-to-use management interface on port 3000
- **Asset Hosting**: Nginx server for local asset mirroring (port 80)
- **TFTP Server**: Network boot file serving (port 69/UDP)
- **Multi-Architecture**: Supports x86-64, ARM64, and ARMv6 platforms
- **Ingress Support**: Integrated with Home Assistant UI

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "netboot.xyz" add-on
3. Configure your network (see DHCP Configuration below)
4. Start the add-on
5. Access the web interface through Home Assistant Ingress or directly at `http://[HOST]:3000`

## Configuration

### Add-on Options

The add-on supports the following configuration options:

- **MENU_VERSION**: Specify a specific version of boot files (optional, defaults to latest)

### Port Configuration

- **3000/tcp**: Web management interface (default)
- **69/udp**: TFTP server for network booting (required)
- **8080/tcp**: HTTP server for hosting boot assets (optional)

### Network Requirements

This add-on requires an existing DHCP server configured to direct network boot requests to the add-on. You will need to configure your DHCP server's `next-server` and `boot-file-name` parameters. See the DHCP Configuration section below for examples.

### Local Asset Mirroring

To use local asset mirroring for faster boot times:

1. Configure your boot.cfg to use your local endpoint (e.g., `http://192.168.0.50:8080`) instead of `https://github.com/netbootxyz`
2. Download assets through the web interface
3. Assets will be served from the local HTTP server on port 8080

## Add-on Data Storage

The add-on uses the following directories for data persistence:

- `/config`: Boot menu files and web application configuration
- `/assets`: Downloaded bootable assets (ISO files, kernels, etc.)
- `/ssl`: SSL certificates (if using HTTPS)

## DHCP Configuration

**Important**: This add-on requires a DHCP server to function. The add-on does not include a DHCP server.

To use this add-on, you must configure your existing DHCP server to forward network boot requests to the add-on. This typically involves setting:
- `next-server`: IP address of your Home Assistant host
- `boot-file-name`: The appropriate boot file for your clients (see boot file table below)

Your DHCP server should have a static IP address for reliable operation.

### DHCP Server Examples

The following examples show how to configure common DHCP servers. Replace `192.168.0.33` with your Home Assistant host IP address.

For more detailed information, see the [official netboot.xyz TFTP documentation](https://netboot.xyz/docs/booting/tftp/).

#### isc-dhcp-server

To install the DHCP server under Debian and Ubuntu run:

```shell
sudo apt install isc-dhcp-server
```

You must edit two files to configure `isc-dhcp-server`. Edit `/etc/default/isc-dhcp-server` and configure at least one of the INTERFACES variables with the name of the interface you want to run the DHCP server on:

```shell
INTERFACESv4="eth0"
```

You'll also need a `/etc/dhcp/dhcpd.conf` looking something like this:


```shell
option arch code 93 = unsigned integer 16;

subnet 192.168.0.0 netmask 255.255.255.0 {
  range 192.168.0.34 192.168.0.254;       # Change this range as appropriate for your network
  next-server 192.168.0.33;               # Change this to the address of your DHCP server
  option subnet-mask 255.255.255.0;
  option routers 192.168.0.1;             # Change this to the address of your router
  option broadcast-address 192.168.0.255;
  option domain-name "mynetwork.lan";     # This is optional
  option domain-name-servers 1.1.1.1;
  if exists user-class and ( option user-class = "iPXE" ) {
    filename "http://boot.netboot.xyz/menu.ipxe";
  } elsif option arch = encode-int ( 16, 16 ) {
    filename "http://boot.netboot.xyz/ipxe/netboot.xyz.efi";
    option vendor-class-identifier "HTTPClient";
  } elsif option arch = 00:07 {
    filename "netboot.xyz.efi";
  } else {
    filename "netboot.xyz.kpxe";
  }
}
```

Now you can try starting the DHCP server:

```shell
sudo systemctl start isc-dhcp-server
```

To make the dhcp server start automatically on boot:

```shell
sudo systemctl enable isc-dhcp-server
```

The following boot files are available and can be configured in your DHCP server:

| Boot File Name | Architecture | Description |
| -------------- | ------------ | ----------- |
| `netboot.xyz.kpxe` | x86/x64 Legacy | Standard legacy BIOS boot (recommended for most legacy systems) |
| `netboot.xyz-undionly.kpxe` | x86/x64 Legacy | Legacy BIOS boot (use if you have NIC driver issues) |
| `netboot.xyz.efi` | x86/x64 UEFI | Standard UEFI boot with built-in drivers (recommended for UEFI) |
| `netboot.xyz-snp.efi` | x86/x64 UEFI | UEFI with Simple Network Protocol (boots all network devices) |
| `netboot.xyz-snponly.efi` | x86/x64 UEFI | UEFI with SNP (only chainloaded device) |
| `netboot.xyz-arm64.efi` | ARM64 | ARM64 UEFI boot with built-in drivers |
| `netboot.xyz-arm64-snp.efi` | ARM64 | ARM64 UEFI with SNP (all devices) |
| `netboot.xyz-arm64-snponly.efi` | ARM64 | ARM64 UEFI with SNP (chainloaded only) |
| `netboot.xyz-rpi4-snp.efi` | Raspberry Pi 4 | Raspberry Pi 4 specific UEFI boot |

## Support & Documentation

- [Official netboot.xyz Documentation](https://netboot.xyz/docs/)
- [Discord Community](https://discord.gg/An6PA2a)
- [GitHub Issues](https://github.com/netbootxyz/netboot.xyz/issues)
