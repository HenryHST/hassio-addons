#!/bin/bash
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Add-on: Corosync QNetd
# Entrypoint script for Corosync QNetd service
# ==============================================================================
set -e

readonly CONFIG_PATH=/data/options.json
readonly QNETD_PORT=5403

echo "-----------------------------------------------------------"
echo " Corosync QNetd Add-on"
echo " Add-on Version: ${ADDON_VERSION}"
echo " Corosync Version: $(corosync-qnetd -v 2>&1 | head -n1 || echo 'unknown')"
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
