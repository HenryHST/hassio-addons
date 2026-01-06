#!/bin/bash
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Add-on: Corosync QNetd
# Entrypoint script for Corosync QNetd service
# ==============================================================================
set -e

# Configuration file path
readonly CONFIG_PATH=/data/options.json

echo "-----------------------------------------------------------"
echo " Corosync QNetd Add-on"
echo " Add-on Version: ${ADDON_VERSION}"
echo " Corosync Version: ${COROSYNC_VERSION}"
echo "-----------------------------------------------------------"

# Parse configuration
if [[ -f "${CONFIG_PATH}" ]]; then
    QNETD_PORT=$(jq -r '.qnetd_port // 5403' ${CONFIG_PATH})
    LOG_LEVEL=$(jq -r '.log_level // "info"' ${CONFIG_PATH})
    TLS_ENABLED=$(jq -r '.tls_enabled // false' ${CONFIG_PATH})
else
    echo "WARNING: Configuration file not found, using defaults"
    QNETD_PORT=5403
    LOG_LEVEL="info"
    TLS_ENABLED=false
fi

echo "[corosync-qnetd] Configuration:"
echo "  - Port: ${QNETD_PORT}"
echo "  - Log Level: ${LOG_LEVEL}"
echo "  - TLS Enabled: ${TLS_ENABLED}"

# Build corosync-qnetd command arguments
QNETD_ARGS="-f"  # Foreground mode

# Add debug flag based on log level
case "${LOG_LEVEL}" in
    trace|debug)
        QNETD_ARGS="${QNETD_ARGS} -d"
        echo "[corosync-qnetd] Debug logging enabled"
        ;;
esac

# Note: Port configuration requires corosync-qnetd config file support
# Currently using default port 5403 as it's compiled into the binary
if [[ "${QNETD_PORT}" != "5403" ]]; then
    echo "WARNING: Custom port ${QNETD_PORT} requested, but corosync-qnetd uses compiled default 5403"
    echo "         Port configuration requires manual corosync-qnetd.conf setup"
fi

echo "[corosync-qnetd] Starting Corosync QNetd daemon..."
echo "[corosync-qnetd] Command: corosync-qnetd ${QNETD_ARGS}"

# Start corosync-qnetd
if ! exec corosync-qnetd ${QNETD_ARGS}; then
    echo "ERROR: Failed to start corosync-qnetd" >&2
    exit 1
fi
