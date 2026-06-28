#!/bin/bash
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Add-on: Corosync QNetd
# Entrypoint script for Corosync QNetd service
# ==============================================================================
set -e

readonly CONFIG_PATH=/data/options.json
readonly QNETD_PORT=5403
readonly DATA_NSSDB=/data/corosync-qnetd/nssdb
readonly ETC_NSSDB=/etc/corosync/qnetd/nssdb

setup_persistent_nssdb() {
    mkdir -p /data/corosync-qnetd
    mkdir -p /etc/corosync/qnetd

    if [[ ! -e "${DATA_NSSDB}/cert9.db" ]] && [[ ! -e "${DATA_NSSDB}/cert8.db" ]]; then
        if [[ -d "${ETC_NSSDB}" ]] && [[ ! -L "${ETC_NSSDB}" ]] \
            && [[ -n "$(ls -A "${ETC_NSSDB}" 2>/dev/null || true)" ]]; then
            echo "[corosync-qnetd] Migrating NSS database to persistent storage..."
            mkdir -p "${DATA_NSSDB}"
            cp -a "${ETC_NSSDB}/." "${DATA_NSSDB}/"
            rm -rf "${ETC_NSSDB}"
        else
            mkdir -p "${DATA_NSSDB}"
        fi
    fi

    if [[ -e "${ETC_NSSDB}" ]] && [[ ! -L "${ETC_NSSDB}" ]]; then
        rm -rf "${ETC_NSSDB}"
    fi
    ln -sfn "${DATA_NSSDB}" "${ETC_NSSDB}"
}

if [[ -f "${COROSYNC_VERSION_FILE:-/etc/corosync-qnetd-version}" ]]; then
    COROSYNC_VERSION=$(< "${COROSYNC_VERSION_FILE}")
elif COROSYNC_VERSION=$(dpkg-query -W -f='${Version}' corosync-qnetd 2>/dev/null); then
    :
else
    COROSYNC_VERSION="unknown"
fi
export COROSYNC_VERSION

echo "-----------------------------------------------------------"
echo " Corosync QNetd Add-on"
echo " Add-on Version: ${ADDON_VERSION}"
echo " Corosync Version: ${COROSYNC_VERSION}"
echo "-----------------------------------------------------------"

if [[ -f "${CONFIG_PATH}" ]]; then
    LOG_LEVEL=$(jq -r '.log_level // "info"' "${CONFIG_PATH}")
else
    echo "WARNING: Configuration file not found, using defaults"
    LOG_LEVEL="info"
fi

echo "[corosync-qnetd] Configuration:"
echo "  - Port: ${QNETD_PORT} (fixed)"
echo "  - Log Level: ${LOG_LEVEL}"

setup_persistent_nssdb
echo "  - NSS database: ${DATA_NSSDB}"

QNETD_ARGS="-f"

case "${LOG_LEVEL}" in
    trace|debug)
        QNETD_ARGS="${QNETD_ARGS} -d"
        echo "[corosync-qnetd] Debug logging enabled"
        ;;
esac

echo "[corosync-qnetd] Starting Corosync QNetd daemon..."
echo "[corosync-qnetd] Command: corosync-qnetd ${QNETD_ARGS}"

exec corosync-qnetd ${QNETD_ARGS}
