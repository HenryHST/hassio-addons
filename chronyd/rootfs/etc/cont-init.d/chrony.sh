#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Add-on: Chrony NTP
# Configures chrony (based on hassio-addons/addon-chrony init-chrony)
# ==============================================================================
set -e

readonly CHRONY_CONF='/etc/chrony/chrony.conf'
readonly DATA_LIB='/data/chronyd/lib'
declare mode
declare -a serverlist
declare nts_suffix=""

if [[ -f "${CHRONY_VERSION_FILE:-/etc/chrony-version}" ]]; then
    CHRONY_VERSION=$(< "${CHRONY_VERSION_FILE}")
else
    CHRONY_VERSION="unknown"
fi

bashio::log.info "-----------------------------------------------------------"
bashio::log.info " Chrony NTP Add-on"
bashio::log.info " Add-on Version: ${ADDON_VERSION:-unknown}"
bashio::log.info " Chrony Version: ${CHRONY_VERSION}"
bashio::log.info "-----------------------------------------------------------"

if bashio::config.has_value 'log_level'; then
    bashio::log.level "$(bashio::config 'log_level')"
fi

mkdir -p /data/chronyd "${DATA_LIB}" /run/chrony

if [[ -e /var/lib/chrony ]] && [[ ! -L /var/lib/chrony ]]; then
    if [[ -n "$(ls -A /var/lib/chrony 2>/dev/null || true)" ]] \
        && [[ ! -e "${DATA_LIB}/chrony.drift" ]]; then
        bashio::log.info "Migrating drift data to persistent storage..."
        cp -a /var/lib/chrony/. "${DATA_LIB}/"
    fi
    rm -rf /var/lib/chrony
fi
ln -sfn "${DATA_LIB}" /var/lib/chrony

chown -R _chrony:_chrony /data/chronyd /run/chrony "${DATA_LIB}" 2>/dev/null || true
chmod 1750 /run/chrony 2>/dev/null || true

if bashio::config.equals 'mode' 'pool' \
    && bashio::config.is_empty 'ntp_pool'; then
    bashio::log.fatal 'pool mode is configured but ntp_pool is empty'
    bashio::exit.nok
fi

if bashio::config.equals 'mode' 'server' \
    && bashio::config.is_empty 'ntp_server'; then
    bashio::log.fatal 'server mode is configured but ntp_server is empty'
    bashio::exit.nok
fi

if bashio::config.true 'enable_nts'; then
    nts_suffix=" nts"
fi

mode=$(bashio::config 'mode')
bashio::log.info "Running in NTP mode: ${mode}"

for server in $(bashio::config "ntp_${mode}"); do
    bashio::log.info "Adding ${mode} ${server}"
    echo "${mode} ${server} iburst${nts_suffix}" >> "${CHRONY_CONF}"
    serverlist+=("${server}")
done

echo "initstepslew 10 ${serverlist[*]}" >> "${CHRONY_CONF}"
echo "driftfile /var/lib/chrony/chrony.drift" >> "${CHRONY_CONF}"

if bashio::config.true 'enable_ptp'; then
    if [[ -e /dev/ptp0 ]]; then
        bashio::log.info "Enabling PTP hardware clock refclock on /dev/ptp0"
        echo "refclock PHC /dev/ptp0 poll 3 dpoll -2 stratum 2" >> "${CHRONY_CONF}"
    else
        bashio::log.warning "enable_ptp is true but /dev/ptp0 is not available"
    fi
fi

bashio::log.info "Drift file: ${DATA_LIB}/chrony.drift"
