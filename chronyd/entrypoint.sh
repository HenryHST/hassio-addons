#!/bin/bash
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Add-on: Chrony NTP
# ==============================================================================
set -e

readonly CONFIG_PATH=/data/options.json
readonly DATA_LIB=/data/chronyd/lib
readonly ETC_CHRONY=/etc/chrony
readonly RUN_CHRONY=/run/chrony
readonly VAR_LIB_CHRONY=/var/lib/chrony

if [[ -f "${CHRONY_VERSION_FILE:-/etc/chrony-version}" ]]; then
    CHRONY_VERSION=$(< "${CHRONY_VERSION_FILE}")
else
    CHRONY_VERSION="unknown"
fi
export CHRONY_VERSION

setup_persistent_storage() {
    mkdir -p /data/chronyd "${DATA_LIB}" "${ETC_CHRONY}" "${RUN_CHRONY}"

    if [[ -e "${VAR_LIB_CHRONY}" ]] && [[ ! -L "${VAR_LIB_CHRONY}" ]]; then
        if [[ -n "$(ls -A "${VAR_LIB_CHRONY}" 2>/dev/null || true)" ]] \
            && [[ ! -e "${DATA_LIB}/chrony.drift" ]]; then
            echo "[chronyd] Migrating drift data to persistent storage..."
            cp -a "${VAR_LIB_CHRONY}/." "${DATA_LIB}/"
        fi
        rm -rf "${VAR_LIB_CHRONY}"
    fi
    ln -sfn "${DATA_LIB}" "${VAR_LIB_CHRONY}"

    chown -R chrony:chrony "${DATA_LIB}" "${ETC_CHRONY}" "${RUN_CHRONY}" 2>/dev/null || true
    chmod 1750 "${ETC_CHRONY}" "${RUN_CHRONY}" 2>/dev/null || true
}

load_options() {
    if [[ ! -f "${CONFIG_PATH}" ]]; then
        echo "WARNING: Configuration file not found, using defaults"
        export NTP_SERVERS="0.pool.ntp.org,1.pool.ntp.org,2.pool.ntp.org,3.pool.ntp.org"
        export ENABLE_NTS=false
        export ENABLE_SYSCLK=false
        export NOCLIENTLOG=false
        export LOG_LEVEL=0
        export TZ=UTC
        return
    fi

    NTP_SERVERS=$(jq -r '.ntp_servers // "0.pool.ntp.org,1.pool.ntp.org,2.pool.ntp.org,3.pool.ntp.org"' "${CONFIG_PATH}")
    ENABLE_NTS=$(jq -r '.enable_nts // false' "${CONFIG_PATH}")
    ENABLE_SYSCLK=$(jq -r '.enable_sysclk // false' "${CONFIG_PATH}")
    NOCLIENTLOG=$(jq -r '.noclientlog // false' "${CONFIG_PATH}")
    LOG_LEVEL=$(jq -r '.log_level // 0' "${CONFIG_PATH}")
    TZ=$(jq -r '.timezone // "UTC"' "${CONFIG_PATH}")
    ENABLE_PTP=$(jq -r '.enable_ptp // false' "${CONFIG_PATH}")

    export NTP_SERVERS ENABLE_NTS ENABLE_SYSCLK NOCLIENTLOG LOG_LEVEL TZ

    if [[ "${ENABLE_PTP}" == "true" ]] && [[ ! -e /dev/ptp0 ]]; then
        echo "[chronyd] WARNING: enable_ptp is true but /dev/ptp0 is not available"
    fi

    if [[ "${ENABLE_SYSCLK}" == "true" ]]; then
        echo "[chronyd] WARNING: enable_sysclk requires privileged/full_access in add-on config"
    fi
}

echo "-----------------------------------------------------------"
echo " Chrony NTP Add-on"
echo " Add-on Version: ${ADDON_VERSION:-unknown}"
echo " Chrony Version: ${CHRONY_VERSION}"
echo "-----------------------------------------------------------"

load_options
setup_persistent_storage

echo "[chronyd] Configuration:"
echo "  - NTP servers: ${NTP_SERVERS}"
echo "  - NTS: ${ENABLE_NTS}"
echo "  - System clock sync: ${ENABLE_SYSCLK}"
echo "  - Timezone: ${TZ}"
echo "  - Drift file: ${DATA_LIB}/chrony.drift"

if [[ "${ENABLE_SYSCLK}" == "true" ]]; then
    exec /bin/startup
fi

exec su-exec chrony:chrony /bin/startup
