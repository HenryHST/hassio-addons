#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Community Add-on: Network UPS Tools
# Configures Network UPS Tools
# ==============================================================================
set -e

# shellcheck source=/usr/bin/nut-config-helpers.sh
source /usr/bin/nut-config-helpers.sh

readonly USERS_CONF=/etc/nut/upsd.users
readonly UPSD_CONF=/etc/nut/upsd.conf
declare nutmode
declare password
declare shutdowncmd
declare upsmonpwd
declare username

# Display version information
if [[ -f "${NUT_VERSION_FILE:-/etc/nut-version}" ]]; then
    NUT_VERSION=$(< "${NUT_VERSION_FILE}")
fi

bashio::log.info "-----------------------------------------------------------"
bashio::log.info " Network UPS Tools Add-on"
bashio::log.info " Add-on Version: ${ADDON_VERSION:-unknown}"
bashio::log.info " NUT Core Version: ${NUT_VERSION:-unknown}"
bashio::log.info "-----------------------------------------------------------"

if bashio::config.has_value 'log_level'; then
    bashio::log.level "$(bashio::config 'log_level')"
fi

# Create /run/nut directory if it doesn't exist (symlinked to /var/run/nut)
mkdir -p /var/run/nut
mkdir -p /run/nut

chown root:root /var/run/nut
chmod 0770 /var/run/nut

chown -R root:root /etc/nut
find /etc/nut -not -perm 0660 -type f -exec chmod 0660 {} \;
find /etc/nut -not -perm 0770 -type d -exec chmod 0770 {} \;

nutmode=$(bashio::config 'mode')
bashio::log.info "Setting mode to ${nutmode}..."
sed -i "s#%%nutmode%%#${nutmode}#g" /etc/nut/nut.conf

if bashio::config.true 'list_usb_devices' ;then
    bashio::log.info "Connected USB devices:"
    lsusb
fi

if bashio::config.equals 'mode' 'netserver' ;then
    bashio::log.info "Generating ${USERS_CONF}..."
    
    # Debug: Log device count
    device_count=$(bashio::config 'devices|length')
    bashio::log.debug "Device count from config: ${device_count}"

    declare -a ups_device_names=()

    # Create Monitor User
    upsmonpwd=$(shuf -ze -n20  {A..Z} {a..z} {0..9}|tr -d '\0')
    if [[ -z "${upsmonpwd}" ]]; then
        bashio::exit.nok "Failed to generate secure password for upsmon user"
    fi
    {
        echo
        echo "[upsmonprimary]"
        echo "  password = ${upsmonpwd}"
        echo "  upsmon primary"
    } >> "${USERS_CONF}"

    for user in $(bashio::config "users|keys"); do
        bashio::config.require.username "users[${user}].username"
        username=$(bashio::config "users[${user}].username")

        bashio::log.info "Configuring user: ${username}"
        if ! bashio::config.true 'i_like_to_be_pwned'; then
            bashio::config.require.safe_password "users[${user}].password"
        else
            bashio::config.require.password "users[${user}].password"
        fi
        password=$(bashio::config "users[${user}].password")

        {
            echo
            echo "[${username}]"
            echo "  password = ${password}"
        } >> "${USERS_CONF}"

        for instcmd in $(bashio::config "users[${user}].instcmds"); do
            echo "  instcmds = ${instcmd}" >> "${USERS_CONF}"
        done

        for action in $(bashio::config "users[${user}].actions"); do
            echo "  actions = ${action}" >> "${USERS_CONF}"
        done

        if bashio::config.has_value "users[${user}].upsmon"; then
            upsmon=$(bashio::config "users[${user}].upsmon")
            upsmon=$(normalize_upsmon_role "${upsmon}")
            echo "  upsmon ${upsmon}" >> "${USERS_CONF}"
        fi
    done

    if bashio::config.has_value "upsd_maxage"; then
        maxage=$(bashio::config "upsd_maxage")
        echo "MAXAGE ${maxage}" >> "${UPSD_CONF}"
    fi

    for device in $(bashio::config "devices|keys"); do
        upsname=$(bashio::config "devices[${device}].name")
        upsdriver=$(bashio::config "devices[${device}].driver")
        upsport=$(bashio::config "devices[${device}].port")
        if bashio::config.has_value "devices[${device}].powervalue"; then
            upspowervalue=$(bashio::config "devices[${device}].powervalue")
            bashio::log.debug "Device ${upsname}: powervalue from config = ${upspowervalue}"
        else
            upspowervalue="1"
            bashio::log.debug "Device ${upsname}: using default powervalue = 1"
        fi

        bashio::log.info "Configuring Device named ${upsname}..."
        {
            echo
            echo "[${upsname}]"
            echo "  driver = ${upsdriver}"
            echo "  port = ${upsport}"
        } >> /etc/nut/ups.conf

        OIFS=$IFS
        IFS=$'\n'
        for configitem in $(bashio::config "devices[${device}].config"); do
            echo "  ${configitem}" >> /etc/nut/ups.conf
        done
        IFS="$OIFS"

        bashio::log.debug "Writing MONITOR line for ${upsname}@localhost"
        echo "MONITOR ${upsname}@localhost ${upspowervalue} upsmonprimary ${upsmonpwd} primary" \
            >> /etc/nut/upsmon.conf
        ups_device_names+=("${upsname}")
    done

    mkdir -p /data/nut
    {
        echo "UPSUSER=upsmonprimary"
        echo "UPSPASS=${upsmonpwd}"
        echo "UPS_HOST=localhost"
        echo "UPS_DEVICES=${ups_device_names[*]}"
    } > /data/nut/monitor.env
    chmod 600 /data/nut/monitor.env
    bashio::log.debug "Wrote /data/nut/monitor.env for MQTT upsc polling"

    monitor_count=$(grep -c "^MONITOR" /etc/nut/upsmon.conf 2>/dev/null || echo 0)
    bashio::log.debug "Total MONITOR lines in upsmon.conf: ${monitor_count}"

    bashio::log.info "Starting the UPS drivers..."
    # Run upsdrvctl
    if bashio::debug; then
        if ! upsdrvctl -u root -D start; then
            bashio::exit.nok "Failed to start UPS drivers"
        fi
    else
        if ! upsdrvctl -u root start; then
            bashio::exit.nok "Failed to start UPS drivers"
        fi
    fi
fi

shutdowncmd="/run/s6/basedir/bin/halt"
if bashio::config.true 'shutdown_host'; then
    bashio::log.warning "UPS Shutdown will shutdown the host"
    shutdowncmd="/usr/bin/shutdownhost"
fi

bashio::log.debug "Writing SHUTDOWNCMD: ${shutdowncmd}"
echo "SHUTDOWNCMD  ${shutdowncmd}" >> /etc/nut/upsmon.conf

final_monitor_count=$(grep -c "^MONITOR" /etc/nut/upsmon.conf 2>/dev/null || echo 0)
bashio::log.debug "Final MONITOR line count: ${final_monitor_count}"
