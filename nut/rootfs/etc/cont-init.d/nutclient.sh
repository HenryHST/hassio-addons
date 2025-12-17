#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Community Add-on: Network UPS Tools
# Configures Network UPS Tools for Client Mode only
# ==============================================================================
declare deadtime=15
declare -a CONF_ENTRIES=("name" "host" "password" "user")

if bashio::config.equals 'mode' 'netclient' ;then
    for entry in "${CONF_ENTRIES[@]}"; do
        if ! bashio::config.exists "remote_ups_${entry}";then
        bashio::exit.nok \
            "Netclient mode specified but no ${entry} is configured"
        fi
    done

    rname=$(bashio::config "remote_ups_name")
    rhost=$(bashio::config "remote_ups_host")
    ruser=$(bashio::config "remote_ups_user")
    rpwd=$(bashio::config "remote_ups_password")
    echo "MONITOR ${rname}@${rhost} 1 ${ruser} ${rpwd} slave" \
        >> /etc/nut/upsmon.conf
fi

if bashio::config.has_value "upsmon_deadtime"; then
    deadtime=$(bashio::config "upsmon_deadtime")
fi

echo "DEADTIME ${deadtime}" >> /etc/nut/upsmon.conf

# SSL Configuration
if bashio::config.has_value "certverify"; then
    certverify=$(bashio::config "certverify")
    if [[ "${certverify}" == "1" ]]; then
        bashio::log.info "Enabling SSL certificate verification..."
        echo "CERTVERIFY 1" >> /etc/nut/upsmon.conf
    fi
fi

if bashio::config.has_value "forcessl"; then
    forcessl=$(bashio::config "forcessl")
    if [[ "${forcessl}" == "1" ]]; then
        bashio::log.info "Forcing SSL connections..."
        echo "FORCESSL 1" >> /etc/nut/upsmon.conf
    fi
fi

# SSL Configuration
if bashio::config.has_value "certverify"; then
    certverify=$(bashio::config "certverify")
    if [[ "${certverify}" == "1" ]]; then
        bashio::log.info "Enabling certificate verification for UPS connections"
        echo "CERTVERIFY 1" >> /etc/nut/upsmon.conf
    fi
fi

if bashio::config.has_value "forcessl"; then
    forcessl=$(bashio::config "forcessl")
    if [[ "${forcessl}" == "1" ]]; then
        bashio::log.info "Enforcing SSL for all UPS connections"
        echo "FORCESSL 1" >> /etc/nut/upsmon.conf
    fi
fi