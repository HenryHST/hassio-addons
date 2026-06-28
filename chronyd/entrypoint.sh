#!/bin/bash
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Add-on: Chrony NTP
# ==============================================================================
set -e

readonly CONFIG_PATH=/data/options.json
readonly DATA_LIB=/data/chronyd/lib
readonly DEBUG_LOG=/data/chronyd/debug-92f7bb.ndjson

# #region agent log
debug_log() {
    local hypothesis_id="$1" location="$2" message="$3" data="$4"
    local payload
    payload=$(jq -nc \
        --arg sid "92f7bb" \
        --arg hid "${hypothesis_id}" \
        --arg loc "${location}" \
        --arg msg "${message}" \
        --argjson dat "${data}" \
        --argjson ts "$(date +%s)000" \
        '{sessionId:$sid,hypothesisId:$hid,location:$loc,message:$msg,data:$dat,timestamp:$ts,runId:"pre-fix"}' \
        2>/dev/null) || return 0
    echo "[DEBUG-92f7bb] ${payload}" >&2
    mkdir -p /data/chronyd 2>/dev/null || return 0
    echo "${payload}" >> "${DEBUG_LOG}" 2>/dev/null || true
}
# #endregion
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

    chown -R chrony:chrony /data/chronyd "${ETC_CHRONY}" "${RUN_CHRONY}" 2>/dev/null || true
    chmod 1750 "${ETC_CHRONY}" "${RUN_CHRONY}" 2>/dev/null || true
}

canonicalize_ntp_server_list() {
    printf '%s' "$1" | tr ',;' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | awk 'NF' | paste -sd, -
}

normalize_ntp_servers() {
    local config="$1"
    local ntp_type

    ntp_type=$(jq -r '.ntp_servers | type' "${config}")
    case "${ntp_type}" in
        array)
            local servers
            servers=$(jq -r '.ntp_servers[] | select(length > 0)' "${config}" | paste -sd, -)
            if [[ -z "${servers}" ]]; then
                echo "0.pool.ntp.org,1.pool.ntp.org,2.pool.ntp.org,3.pool.ntp.org"
            else
                echo "${servers}"
            fi
            ;;
        string)
            jq -r '.ntp_servers' "${config}"
            ;;
        *)
            echo "0.pool.ntp.org,1.pool.ntp.org,2.pool.ntp.org,3.pool.ntp.org"
            ;;
    esac
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

    NTP_SERVERS=$(canonicalize_ntp_server_list "$(normalize_ntp_servers "${CONFIG_PATH}")")
    ENABLE_NTS=$(jq -r '.enable_nts // false' "${CONFIG_PATH}")
    ENABLE_SYSCLK=$(jq -r '.enable_sysclk // false' "${CONFIG_PATH}")
    NOCLIENTLOG=$(jq -r '.noclientlog // false' "${CONFIG_PATH}")
    LOG_LEVEL=$(jq -r '.log_level // 0' "${CONFIG_PATH}")
    TZ=$(jq -r '.timezone // "UTC"' "${CONFIG_PATH}")
    ENABLE_PTP=$(jq -r '.enable_ptp // false' "${CONFIG_PATH}")

    # #region agent log
    debug_log "H1" "entrypoint.sh:load_options" "options.json parsed" "$(jq -nc \
        --arg ntp "${NTP_SERVERS}" \
        --arg ntp_type "$(jq -r '.ntp_servers | type' "${CONFIG_PATH}")" \
        --arg nts "${ENABLE_NTS}" \
        --arg raw "$(jq -c '.ntp_servers' "${CONFIG_PATH}")" \
        '{ntp_servers:$ntp,ntp_servers_type:$ntp_type,enable_nts:$nts,ntp_servers_raw:$raw}')"
    # #endregion

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
