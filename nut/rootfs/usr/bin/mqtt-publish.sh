#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Community Add-on: Network UPS Tools
# Poll upsc and publish UPS status and numeric variables via MQTT
# ==============================================================================
set -euo pipefail

# shellcheck source=/usr/bin/nut-config-helpers.sh
source /usr/bin/nut-config-helpers.sh

readonly MONITOR_ENV="/data/nut/monitor.env"
readonly OPTIONS_FILE="/data/options.json"
readonly EVENT_TYPES="ONLINE ONBATT LOWBATT FSD"

MQTT_HOST=""
MQTT_PORT=""
MQTT_USER=""
MQTT_PASS=""
MQTT_TOPIC=""
MQTT_USE_TLS="false"

mqtt_enabled() {
    if [[ -f "${OPTIONS_FILE}" ]] \
        && jq -e '.enable_mqtt == true' "${OPTIONS_FILE}" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

load_mqtt_config() {
    local config_host config_port config_user config_pass config_topic config_tls

    config_host=$(jq -r '.mqtt_host // ""' "${OPTIONS_FILE}")
    config_port=$(jq -r '.mqtt_port // 1883' "${OPTIONS_FILE}")
    config_user=$(jq -r '.mqtt_username // ""' "${OPTIONS_FILE}")
    config_pass=$(jq -r '.mqtt_password // ""' "${OPTIONS_FILE}")
    config_topic=$(jq -r '.mqtt_topic // "nut/ups"' "${OPTIONS_FILE}")
    config_tls=$(jq -r '.mqtt_use_tls // false' "${OPTIONS_FILE}")

    if [[ -z "${config_host}" ]]; then
        MQTT_HOST=$(bashio::services mqtt host 2>/dev/null || true)
        if [[ -z "${MQTT_HOST}" ]]; then
            echo "MQTT broker not configured and Mosquitto add-on not available" >&2
            return 1
        fi
        MQTT_PORT=$(bashio::services mqtt port)
        MQTT_USER=$(bashio::services mqtt username)
        MQTT_PASS=$(bashio::services mqtt password)
    else
        MQTT_HOST="${config_host}"
        MQTT_PORT="${config_port}"
        MQTT_USER="${config_user}"
        MQTT_PASS="${config_pass}"
    fi

    MQTT_TOPIC="${config_topic}"
    MQTT_USE_TLS="${config_tls}"

    if [[ -z "${MQTT_HOST}" ]]; then
        echo "MQTT host is empty" >&2
        return 1
    fi
}

load_monitor_env() {
    if [[ ! -f "${MONITOR_ENV}" ]]; then
        echo "monitor.env not found" >&2
        return 1
    fi
    # shellcheck source=/dev/null
    source "${MONITOR_ENV}"
    if [[ -z "${UPSUSER:-}" ]] || [[ -z "${UPSPASS:-}" ]]; then
        echo "UPSUSER or UPSPASS missing in monitor.env" >&2
        return 1
    fi
}

mqtt_publish() {
    local topic=$1
    local message=$2
    local -a args=(
        -h "${MQTT_HOST}"
        -p "${MQTT_PORT}"
        -t "${topic}"
        -m "${message}"
        -r
    )

    if [[ -n "${MQTT_USER}" ]]; then
        args+=(-u "${MQTT_USER}" -P "${MQTT_PASS}")
    fi

    if [[ "${MQTT_USE_TLS}" == "true" ]]; then
        args+=(--cafile /etc/ssl/certs/ca-certificates.crt)
    fi

    mosquitto_pub "${args[@]}"
}

upsc_var() {
    local ups_name=$1
    local var_name=$2
    local ups_host="${UPS_HOST:-localhost}"

    upsc -u "${UPSUSER}" -p "${UPSPASS}" "${ups_name}@${ups_host}" "${var_name}" 2>/dev/null || true
}

sync_device_status() {
    local ups_name=$1
    local status_override=${2:-}
    local raw_status
    local status
    local topic

    if [[ -n "${status_override}" ]]; then
        status="${status_override}"
        raw_status=$(upsc_var "${ups_name}" ups.status)
    else
        raw_status=$(upsc_var "${ups_name}" ups.status)
        status=$(map_ups_status "${raw_status}")
    fi

    topic=$(mqtt_topic_path "${MQTT_TOPIC}" "${ups_name}" "status")
    mqtt_publish "${topic}" "${status}"

    if [[ -n "${raw_status}" ]]; then
        topic=$(mqtt_topic_path "${MQTT_TOPIC}" "${ups_name}" "raw_status")
        mqtt_publish "${topic}" "${raw_status}"
    fi
}

sync_device_numeric() {
    local ups_name=$1
    local var_name=$2
    local topic_suffix=$3
    local value
    local topic

    value=$(upsc_var "${ups_name}" "${var_name}")
    if [[ -z "${value}" ]]; then
        return 0
    fi

    topic=$(mqtt_topic_path "${MQTT_TOPIC}" "${ups_name}" "${topic_suffix}")
    mqtt_publish "${topic}" "${value}"
}

sync_device() {
    local ups_name=$1
    local status_override=${2:-}

    sync_device_status "${ups_name}" "${status_override}"
    sync_device_numeric "${ups_name}" "battery.charge" "battery_charge"
    sync_device_numeric "${ups_name}" "input.voltage" "input_voltage"
    sync_device_numeric "${ups_name}" "ups.load" "load"
    sync_device_numeric "${ups_name}" "battery.runtime" "battery_runtime"
}

sync_event() {
    local ups_name=$1
    local notify_type=$2

    if ! mqtt_enabled; then
        return 0
    fi

    if [[ " ${EVENT_TYPES} " != *" ${notify_type} "* ]]; then
        return 0
    fi

    load_mqtt_config || return 0
    load_monitor_env || return 0

    sync_device_status "${ups_name}" "${notify_type}"

    if [[ "${3:-}" == "--quick" ]]; then
        sync_device_numeric "${ups_name}" "battery.charge" "battery_charge"
        sync_device_numeric "${ups_name}" "input.voltage" "input_voltage"
        sync_device_numeric "${ups_name}" "ups.load" "load"
        sync_device_numeric "${ups_name}" "battery.runtime" "battery_runtime"
    fi
}

sync_all() {
    local ups_name

    if ! mqtt_enabled; then
        return 0
    fi

    load_mqtt_config || return 0
    load_monitor_env || return 0

    if [[ -z "${UPS_DEVICES:-}" ]]; then
        return 0
    fi

    for ups_name in ${UPS_DEVICES}; do
        sync_device "${ups_name}"
    done
}

main() {
    case "${1:-}" in
        --event)
            sync_event "${2:-}" "${3:-}" "${4:-}"
            ;;
        *)
            sync_all
            ;;
    esac
}

main "$@"
