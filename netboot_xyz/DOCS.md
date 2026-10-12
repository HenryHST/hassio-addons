# Home Assistant Add-on: netboot.xyz

**Add-on Version**: 1.1.0  
**netboot.xyz Webapp Version**: 0.7.6  
**netboot.xyz Menus Version**: 3.0.3  
**iPXE Secure Boot**: v2.0.0 (default)

> **Note**: The add-on version tracks Home Assistant integration changes. The **webapp** version is the
> Node UI (`netbootxyz/webapp`). The **menus** version is the boot menus and iPXE binaries from
> [`netboot.xyz` releases](https://github.com/netbootxyz/netboot.xyz/releases) (currently pinned to 3.0.3).

## Quick start (Ingress)

1. Install and start the add-on.
2. Open **Settings → Add-ons → netboot.xyz → Open Web UI** (Ingress on port 3000).
3. Configure DHCP `next-server` to your Home Assistant host IP and pick a boot file from the table below.
4. Optionally set `menu_version` in the add-on configuration to pin boot menu downloads.

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "netboot.xyz" add-on
3. Configure your network (see Network Configuration below)
4. Start the add-on
5. Access the web interface through Home Assistant Ingress or directly at `http://[HOST]:3000`

## Configuration

Configuration options below. All other setup is done through the web interface after installation.

### `menu_version` (optional)

Tag of the netboot.xyz boot menus / boot binaries to download (e.g. `3.0.3`). Leave empty to use the
add-on pin (**3.0.3**). On start, menus are re-downloaded if `/config/menuversion.txt` differs from the
desired version (upgrade path for existing installs).

### `enable_secure_boot` (default: `true`)

When enabled, downloads UEFI Secure Boot binaries (Microsoft-signed shim + signed iPXE) and
`autoexec.ipxe` into TFTP paths under `secureboot-x86_64/` and `secureboot-arm64/`. Independent of
the menu download; existing installs pick up Secure Boot files on the next start.

### `ipxe_sb_version` (optional)

iPXE release tag for `ipxeboot.tar.gz` (e.g. `v2.0.0`). Leave empty to use **v2.0.0**.

**Note**: _Remember to restart the add-on when making configuration changes._

## Network Configuration

### Requirements

This add-on requires a DHCP server configured to direct network boot requests to the add-on. The add-on itself does not include a DHCP server.

**Important**: You must configure your existing DHCP server to use this add-on for network booting.

### DHCP Server Setup

To use this add-on, configure your DHCP server with:
- **next-server**: IP address of your Home Assistant host
- **boot-file-name**: The appropriate boot file for your clients (see Boot Files table below)

Your DHCP server should have a static IP address for reliable operation.

## Ports

The add-on exposes the following ports:

| Port | Protocol | Purpose |
|------|----------|---------|
| 3000 | TCP | Web management interface (accessible via Ingress) |
| 69 | UDP | TFTP server for network booting |
| 8080 | TCP | HTTP server for hosting boot assets |

### Port Configuration

- **3000/tcp**: Access the web interface to manage menus and download assets. This port is accessible through Home Assistant Ingress.
- **69/udp**: **Required** for network booting. Your DHCP server will direct clients to this port.
- **8080/tcp**: Optional, for hosting local asset mirrors for faster boot times.

## Boot Files

The following boot files are available for different boot scenarios:

| Boot File Name | Architecture | Description |
|----------------|--------------|-------------|
| `netboot.xyz.kpxe` | x86/x64 Legacy | Standard legacy BIOS boot (recommended for most legacy systems) |
| `netboot.xyz-undionly.kpxe` | x86/x64 Legacy | Legacy BIOS boot (use if you have NIC driver issues) |
| `netboot.xyz.efi` | x86/x64 UEFI | Standard UEFI boot with built-in drivers (recommended for UEFI) |
| `netboot.xyz-snp.efi` | x86/x64 UEFI | UEFI with Simple Network Protocol (boots all network devices) |
| `netboot.xyz-snponly.efi` | x86/x64 UEFI | UEFI with SNP (only chainloaded device) |
| `netboot.xyz-arm64.efi` | ARM64 | ARM64 UEFI boot with built-in drivers |
| `netboot.xyz-arm64-snp.efi` | ARM64 | ARM64 UEFI with SNP (all devices) |
| `netboot.xyz-arm64-snponly.efi` | ARM64 | ARM64 UEFI with SNP (chainloaded only) |
| `netboot.xyz-legacy.kpxe` | x86/x64 Legacy | Legacy BIOS without USB NIC drivers (USB keyboard on some firmware) |
| `netboot.xyz-legacy.efi` | x86/x64 UEFI | UEFI without USB NIC drivers (USB keyboard on some firmware) |
| `netboot.xyz-rpi4-snp.efi` | Raspberry Pi 4 | Raspberry Pi 4 specific UEFI boot |

### UEFI Secure Boot

Point DHCP `boot-file-name` at the Microsoft-signed shim. Keep all files in that Secure Boot
directory together (shim expects iPXE and `autoexec.ipxe` alongside it).

| Boot File Name | Architecture | Description |
|----------------|--------------|-------------|
| `secureboot-x86_64/shimx64.efi` | x86/x64 UEFI SB | Microsoft-signed shim (entry point) |
| `secureboot-arm64/shimaa64.efi` | ARM64 UEFI SB | Microsoft-signed shim (entry point) |

Also present in each Secure Boot directory (do not relocate): `ipxe.efi`, `ipxe-shim.efi`,
`snponly.efi`, `snponly-shim.efi`, `autoexec.ipxe`.

Boot flow: firmware → shim → signed iPXE → `autoexec.ipxe` → netboot.xyz menu.

DHCP example (x86_64 Secure Boot):

```
filename "secureboot-x86_64/shimx64.efi";
```

## DHCP Configuration Examples

### isc-dhcp-server

To configure isc-dhcp-server on Debian/Ubuntu:

1. Install the DHCP server:
```bash
sudo apt install isc-dhcp-server
```

2. Edit `/etc/default/isc-dhcp-server` and configure the interface:
```bash
INTERFACESv4="eth0"
```

3. Edit `/etc/dhcp/dhcpd.conf`:
```
option arch code 93 = unsigned integer 16;

subnet 192.168.0.0 netmask 255.255.255.0 {
  range 192.168.0.34 192.168.0.254;       # Change this range as appropriate
  next-server 192.168.0.33;               # Change to your Home Assistant IP
  option subnet-mask 255.255.255.0;
  option routers 192.168.0.1;             # Your router IP
  option broadcast-address 192.168.0.255;
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

4. Start the DHCP server:
```bash
sudo systemctl start isc-dhcp-server
sudo systemctl enable isc-dhcp-server
```

## Local Asset Mirroring

To speed up boot times, you can mirror assets locally:

1. Access the web interface at `http://[HOST]:3000` or via Ingress
2. Navigate to the "Local Assets" section
3. Download the assets you need
4. Configure your boot.cfg to use your local endpoint:
   - Change `live_endpoint` from `https://github.com/netbootxyz`
   - To your Home Assistant IP: `http://192.168.0.33:8080` (replace with your IP)

Assets will then be served from your local server, resulting in much faster boot and load times.

## Troubleshooting

### Cannot boot from network

1. **Verify DHCP Configuration**: Ensure your DHCP server is configured with the correct `next-server` (your Home Assistant IP)
2. **Check TFTP Port**: Verify port 69/UDP is accessible and not blocked by firewall
3. **Test TFTP**: Use `tftp` command to test connection: `tftp <your-ha-ip> -c get netboot.xyz.kpxe`
4. **Check Logs**: Review add-on logs in Home Assistant for any errors

### Web interface not accessible

1. **Check Add-on Status**: Ensure the add-on is running
2. **Try Ingress**: Access via Home Assistant Ingress instead of direct port
3. **Verify Port**: If using direct access, ensure port 3000 is not in use by another service

### Slow boot times

1. **Enable Local Asset Mirroring**: Download assets to your local server
2. **Configure boot.cfg**: Point `live_endpoint` to your local HTTP server (port 8080)
3. **Check Network Speed**: Ensure good network connectivity between client and Home Assistant

### Assets won't download

1. **Check Internet Connection**: Asset downloads require internet access
2. **Verify Storage**: Ensure sufficient disk space in Home Assistant
3. **Check Logs**: Review add-on logs for download errors

## Support

For more information:
- [Official netboot.xyz Documentation](https://netboot.xyz/docs/)
- [netboot.xyz Discord Community](https://discord.gg/An6PA2a)
- [netboot.xyz GitHub](https://github.com/netbootxyz/netboot.xyz)

## Credits

This add-on is based on the official [netboot.xyz Docker image](https://github.com/netbootxyz/docker-netbootxyz).

