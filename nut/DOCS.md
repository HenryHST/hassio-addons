# Home Assistant Add-on: Network UPS Tools

**Add-on Version**: 1.2.0  
**NUT Core Version**: 2.8.1-5 (Debian trixie package; see `/etc/nut-version` in the container)

> **Note**: The add-on version is independent of the NUT core version. The add-on version tracks 
> changes to the Home Assistant integration, while the core version indicates the underlying Network 
> UPS Tools version being used.

The primary goal of the Network UPS Tools (NUT) project is to provide support
for Power Devices, such as Uninterruptible Power Supplies, Power Distribution
Units, Automatic Transfer Switch, Power Supply Units and Solar Controllers.

NUT provides many control and monitoring [features][nut-features], with a
uniform control and management interface.

More than 140 different manufacturers, and several thousands models
are [compatible][nut-compatible].

The Network UPS Tools (NUT) project is the combined effort of
many [individuals and companies][nut-acknowledgements].

## Installation

The installation of this add-on is pretty straightforward and not different in
comparison to installing any other Home Assistant add-on.

1. Click the Home Assistant My button below to open the add-on on your Home
   Assistant instance.

   [![Open this add-on in your Home Assistant instance.][addon-badge]][addon]

1. Click the "Install" button to install the add-on.
1. Configure the `users` and `devices` options, as described below.
1. Start the "Network UPS Tools" add-on.
1. Check the logs of the "Network UPS Tools" add-on to see if everything went well.
1. Note the `Hostname` listed on the "Info" tab of the "Network UPS Tools" add-on.
1. Configure the [NUT Integration][nut-ha-docs] using add-on Hostname (identified
   above), Port `3493`, and the Username/Password configured in the add-on.
1. For more information on configuring the NUT Integration in Home Assistant see
   the [NUT integration documentation][nut-ha-docs].

## Configuration

The add-on can be used with the basic configuration, with other options for more
advanced users.

**Note**: _Remember to restart the add-on when the configuration is changed._

Network UPS Tools add-on configuration:

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

### Option: `log_level`

The `log_level` option controls the level of log output by the add-on and can
be changed to be more or less verbose, which might be useful when you are
dealing with an unknown issue. Possible values are:

- `trace`: Show every detail, like all called internal functions.
- `debug`: Shows detailed debug information.
- `info`: Normal (usually) interesting events.
- `warning`: Exceptional occurrences that are not errors.
- `error`: Runtime errors that do not require immediate action.
- `fatal`: Something went terribly wrong. Add-on becomes unusable.

Please note that each level automatically includes log messages from a
more severe level, e.g., `debug` also shows `info` messages. By default,
the `log_level` is set to `info`, which is the recommended setting unless
you are troubleshooting.

### Option: `users`

This option allows you to specify a list of one or more users. Each user can
have its own privileges like defined in the sub-options below.

_Refer to the [`upsd.users(5)`][upsd-users] documentation for more information._

#### Sub-option: `username`

The username the user needs to use to login to the NUT server. A valid username
contains only `a-z`, `A-Z`, `0-9` and underscore characters (`_`).

#### Sub-option: `password`

Set the password for this user.

#### Sub-option: `instcmds`

A list of instant commands that a user is allowed to initiate. Use `all` to
grant all commands automatically.

#### Sub-option: `actions`

A list of actions that a user is allowed to perform. Valid actions are:

- `set`: change the value of certain variables in the UPS.
- `fsd`: set the forced shutdown flag in the UPS. This is equivalent to an
  "on battery + low battery" situation for the purposes of monitoring.

The list of actions is expected to grow in the future.

#### Sub-option: `upsmon`

Add the necessary actions for a `upsmon` process to work. Use `primary` or
`secondary` (NUT 2.8+). The legacy values `master` and `slave` are still
accepted and mapped automatically. For a `netclient` setup, use `secondary`.

### Option: `devices`

This option allows you to specify a list of UPS devices attached to your
system.

_Refer to the [`ups.conf(5)`][ups-conf] documentation for more information._

#### Sub-option: `name`

The name of the UPS. You cannot use any space characters or the name `default`.

#### Sub-option: `driver`

This specifies which program will be monitoring this UPS. You need to specify
the one that is compatible with your hardware. See [`nutupsdrv(8)`][nutupsdrv]
for more information on drivers in general and pointers to the man pages of
specific drivers.

#### Sub-option: `port`

This is the serial port where the UPS is connected. The first serial port
usually is `/dev/ttyS0`. Use `auto` to automatically detect the port.

#### Sub-option: `powervalue`

Optionally lets you set whether this particular UPS provides power to the
device this add-on is running on. Useful if you have multiple UPS that you
wish to monitor, but you don't want low battery on some of them to shut down
this host. Acceptable values are `1` for "providing power to this host" or `0`
for "monitor only". Defaults to `1`

**Note**: _There must be a minimum of one attached device with powervalue `1`_

#### Sub-option: `config`

A list of additional [options][ups-fields] to configure for this UPS. The common
[`usbhid-ups`][usbhid-ups] driver allows you to distinguish between devices by
using a combination of the `vendor`, `product`, `serial`, `vendorid`, and
`productid` options:

```yaml
devices:
  - name: mge
    driver: usbhid-ups
    port: auto
    config:
      - vendorid = 0463
  - name: apcups
    driver: usbhid-ups
    port: auto
    config:
      - vendorid = 051d*
  - name: foocorp
    driver: usbhid-ups
    port: auto
    config:
      - vendor = "Foo.Corporation.*"
  - name: smartups
    driver: usbhid-ups
    port: auto
    config:
      - product = ".*(Smart|Back)-?UPS.*"
```

### Option: `mode`

Recognized values are `netserver` and `netclient`.

- `netserver`: Runs the components needed to manage a locally connected UPS and
  allow other clients to connect (either as slaves or for management).
- `netclient`: Only runs `upsmon` to connect to a remote system running as
  `netserver`.

#### Network listener (`upsd`)

In `netserver` mode, `upsd` listens on `0.0.0.0:3493` so Home Assistant and other
LAN clients can reach the NUT server. Restrict access at the firewall or Home
Assistant host level if needed. The add-on does not expose port 3493 to the
public internet by default.

### Option: `shutdown_host`

When this option is set to `true` on a UPS shutdown command, the host system
will be shutdown. When set to `false` only the add-on will be stopped. This is to
allow testing without impact to the system.

### Option: `list_usb_devices`

When this option is set to `true`, a list of connected USB devices will be
displayed in the add-on log when the add-on starts up. This option can be used
to help identify different UPS devices when multiple UPS devices are connected
to the system.

### Option: `remote_ups_name`

When running in `netclient` mode, the name of the remote UPS.

### Option: `remote_ups_host`

When running in `netclient` mode, the host of the remote UPS.

### Option: `remote_ups_user`

When running in `netclient` mode, the user of the remote UPS.

### Option: `remote_ups_password`

When running in `netclient` mode, the password of the remote UPS.

**Note**: _When using the remote option, the user and device options must still
be present, however they will have no effect_

### Option: `upsd_maxage`

Allows setting the MAXAGE value in upsd.conf to increase the timeout for
specific drivers, should not be changed for the majority of users.

### Option: `upsmon_deadtime`

Allows setting the DEADTIME value in upsmon.conf to adjust the stale time for
the monitor process, should not be changed for the majority of users.

### Option: `certverify`

When set to `1`, makes upsmon verify all connections with SSL certificates.
This ensures that the upsd server is authentic and greatly reduces the risk of
man-in-the-middle attacks.

**Default**: `0` (disabled)

**Note**: This requires all your upsd hosts to be configured with SSL and have
valid certificates. Without proper SSL setup, connections will fail when this
option is enabled.

### Option: `forcessl`

When set to `1`, forces upsmon to use SSL for all connections to upsd servers.
This ensures that all communication is encrypted, preventing session sniffing.

**Default**: `0` (disabled)

**Note**: This will make upsmon drop connections if the remote upsd doesn't
support SSL. Only enable this if all your upsd servers have SSL configured.

**Security Recommendation**: For maximum security, enable both `certverify` and
`forcessl` together, but ensure all upsd servers are properly configured with
SSL certificates first.

Example configuration with SSL enabled:

```yaml
mode: netclient
remote_ups_host: 192.168.1.100
remote_ups_name: myups
remote_ups_user: monuser
remote_ups_password: secret
certverify: 1
forcessl: 1
```

### Option: `i_like_to_be_pwned`

Adding this option to the add-on configuration allows to you bypass the
HaveIBeenPwned password requirement by setting it to `true`.

**Note**: _We STRONGLY suggest picking a stronger/safer password instead of
using this option! USE AT YOUR OWN RISK!_

### Option: `enable_mqtt`

When `true` (default), the add-on polls `upsc` and publishes UPS status and
numeric values to an MQTT broker. Works in **netserver** and **netclient** mode.

```yaml
enable_mqtt: true
mqtt_host: ""
mqtt_port: 1883
mqtt_username: ""
mqtt_password: ""
mqtt_topic: nut/ups
mqtt_poll_interval: 30
mqtt_use_tls: false
```

### Option: `mqtt_host`

MQTT broker hostname or IP. Leave empty to use the Home Assistant **Mosquitto
broker** add-on automatically (`services: mqtt:want`).

### Option: `mqtt_port`

MQTT broker port. Default: `1883` (use `8883` with `mqtt_use_tls: true` for
typical TLS setups).

### Option: `mqtt_username` / `mqtt_password`

Credentials for the MQTT broker. Leave empty when using the Mosquitto add-on
(auto-configured credentials).

### Option: `mqtt_topic`

Base MQTT topic path (no trailing slash). Per-UPS topics are appended below this
base. Default: `nut/ups`.

Example with `mqtt_topic: home/ups` and UPS name `myups`:

| Topic | Payload |
|-------|---------|
| `home/ups/myups/status` | `ONLINE`, `ONBATT`, `LOWBATT`, `FSD`, or `UNKNOWN` |
| `home/ups/myups/raw_status` | Raw NUT `ups.status` tokens (e.g. `OL OL`) |
| `home/ups/myups/battery_charge` | Battery charge (%) |
| `home/ups/myups/input_voltage` | Input voltage (V) |
| `home/ups/myups/load` | UPS load (%) |
| `home/ups/myups/battery_runtime` | Battery runtime (s) |

All messages are published **retained** so new subscribers receive the last known
value. Numeric topics are only published when the UPS driver exposes the variable.

### Option: `mqtt_poll_interval`

Seconds between `upsc` polls for MQTT publishing (10–300). Default: `30`.

Immediate updates on status changes (`ONLINE`, `ONBATT`, `LOWBATT`, `FSD`) are
also sent via the `upsmon` notify handler.

### Option: `mqtt_use_tls`

Enable TLS for MQTT connections (`mosquitto_pub --cafile`). Default: `false`.

## MQTT

### Status values

| MQTT status | Meaning | NUT `ups.status` token |
|-------------|---------|--------------------------|
| `ONLINE` | Utility power present | `OL` |
| `ONBATT` | Running on battery | `OB` |
| `LOWBATT` | Battery low | `LB` |
| `FSD` | Forced shutdown in progress | `FSD` |

Priority when multiple tokens are present: FSD > LOWBATT > ONBATT > ONLINE.

### Mosquitto add-on vs. external broker

| Setup | `mqtt_host` | Notes |
|-------|-------------|-------|
| Mosquitto add-on | `""` (empty) | Install Mosquitto broker; credentials auto-discovered |
| External broker | e.g. `192.168.0.10` | Set host, port, username, password manually |

### netclient mode

In **netclient** mode, `upsc` queries the remote `upsd` using your
`remote_ups_*` settings. MQTT topics use the configured `remote_ups_name` as the
UPS segment in the topic path.

### Home Assistant MQTT sensor example

```yaml
mqtt:
  sensor:
    - name: "UPS Status"
      state_topic: "nut/ups/myups/status"
      unique_id: nut_myups_status
```

### Example automation (critical alert)

```yaml
automation:
  - alias: "UPS low battery or shutdown"
    trigger:
      - platform: mqtt
        topic: nut/ups/myups/status
    condition:
      - condition: template
        value_template: "{{ trigger.payload in ['LOWBATT', 'FSD'] }}"
    action:
      - service: notify.persistent_notification
        data:
          title: "UPS critical"
          message: "UPS status is {{ trigger.payload }}"
```

### Breaking changes in 1.2.0

- Removed: `enable_home_assistant_sensors`, `homeassistant_poll_interval`
- Removed: `sensor.nut_addon_*` States API push
- Removed: `nut.ups_event` Home Assistant event
- Removed: `nut_hassio` custom integration from this repository

Use MQTT (this add-on), the official [NUT integration](https://www.home-assistant.io/integrations/nut/), or subscribe to MQTT topics in automations.

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality.

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## Support

Got questions?

You have several options to get them answered:

- The [Home Assistant Community Add-ons Discord chat server][discord] for add-on
  support and feature requests.
- The [Home Assistant Discord chat server][discord-ha] for general Home
  Assistant discussions and questions.
- The Home Assistant [Community Forum][forum].
- Join the [Reddit subreddit][reddit] in [/r/homeassistant][reddit]

You could also [open an issue here][issue] GitHub.

## Authors & contributors

The original setup of this repository is by [Dale Higgs][dale3h].

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2018-2025 Dale Higgs

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

[addon-badge]: https://my.home-assistant.io/badges/supervisor_addon.svg
[addon]: https://my.home-assistant.io/redirect/supervisor_addon/?addon=local_nut&repository_url=https%3A%2F%2Fgithub.com%2Fhenryhst%2Fhassio-addons
[contributors]: https://github.com/henryhst/hassio-addons/graphs/contributors
[critical-notif]: https://companion.home-assistant.io/docs/notifications/critical-notifications
[dale3h]: https://github.com/dale3h
[discord-ha]: https://discord.gg/c5DvZ4e
[discord]: https://discord.me/hassioaddons
[fake-usb]: https://github.com/henryhst/hassio-addons/issues
[forum]: https://community.home-assistant.io/t/community-hass-io-add-on-network-ups-tools/68516
[issue]: https://github.com/henryhst/hassio-addons/issues
[nut-acknowledgements]: https://networkupstools.org/acknowledgements.html
[nut-compatible]: https://networkupstools.org/stable-hcl.html
[nut-conf]: https://networkupstools.org/docs/man/nut.conf.html
[nut-features]: https://networkupstools.org/features.html
[nut-ha-docs]: https://www.home-assistant.io/integrations/nut/
[nut-notif-doc-1]: https://networkupstools.org/docs/user-manual.chunked/ar01s07.html
[nut-notif-doc-2]: https://networkupstools.org/docs/man/upsmon.conf.html
[nutupsdrv]: https://networkupstools.org/docs/man/nutupsdrv.html
[reddit]: https://reddit.com/r/homeassistant
[releases]: https://github.com/henryhst/hassio-addons/releases
[semver]: https://semver.org/spec/v2.0.0
[sleep]: https://linux.die.net/man/1/sleep
[ups-conf]: https://networkupstools.org/docs/man/ups.conf.html
[ups-fields]: https://networkupstools.org/docs/man/ups.conf.html#_ups_fields
[upsd-conf]: https://networkupstools.org/docs/man/upsd.conf.html
[upsd-users]: https://networkupstools.org/docs/man/upsd.users.html
[upsd]: https://networkupstools.org/docs/man/upsd.html
[upsmon]: https://networkupstools.org/docs/man/upsmon.html
[usbhid-ups]: https://networkupstools.org/docs/man/usbhid-ups.html
