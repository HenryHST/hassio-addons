#!/bin/bash
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Community Add-on: Network UPS Tools
# Push UPS status and numeric variables to Home Assistant States API
# ==============================================================================
set -euo pipefail

# shellcheck source=/usr/bin/nut-config-helpers.sh
source /usr/bin/nut-config-helpers.sh

readonly MONITOR_ENV="/data/nut/monitor.env"
readonly HA_API_BASE="${SUPERVISOR:-http://supervisor}/core/api/states"
readonly EVENT_TYPES="ONLINE ONBATT LOWBATT FSD"

sensors_enabled() {
    if [[ -f /data/options.json ]] \
        && jq -e '.enable_home_assistant_sensors == true' /data/options.json >/dev/null 2>&1; then
        return 0
    fi
    return 1
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

ha_set_state() {
    local entity_id=$1
    local state=$2
    local attributes=${3:-"{}"}

    if [[ -z "${SUPERVISOR_TOKEN:-}" ]]; then
        echo "SUPERVISOR_TOKEN not set" >&2
        return 1
    fi

    local payload
    payload=$(jq -n \
        --arg state "${state}" \
        --argjson attributes "${attributes}" \
        '{state: $state, attributes: $attributes}')

    curl -sS -f -X POST \
        -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        -H "Content-Type: application/json" \
        --data-binary "${payload}" \
        "${HA_API_BASE}/${entity_id}" >/dev/null
}

upsc_var() {
    local ups_name=$1
    local var_name=$2
    upsc -u "${UPSUSER}" -p "${UPSPASS}" "${ups_name}@localhost" "${var_name}" 2>/dev/null || true
}

sync_device_status() {
    local ups_name=$1
    local status_override=${2:-}
    local entity_id="sensor.nut_addon_${ups_name}_status"
    local raw_status
    local status
    local attributes

    if [[ -n "${status_override}" ]]; then
        status="${status_override}"
        raw_status=$(upsc_var "${ups_name}" ups.status)
    else
        raw_status=$(upsc_var "${ups_name}" ups.status)
        status=$(map_ups_status "${raw_status}")
    fi

    attributes=$(jq -n \
        --arg friendly_name "${ups_name} UPS Status" \
        --arg raw_status "${raw_status}" \
        --arg device_class "enum" \
        --argjson options '["ONLINE","ONBATT","LOWBATT","FSD","UNKNOWN"]' \
        '{
            friendly_name: $friendly_name,
            raw_status: $raw_status,
            device_class: $device_class,
            options: $options
        }')

    ha_set_state "${entity_id}" "${status}" "${attributes}"
}

sync_device_numeric() {
    local ups_name=$1
    local var_name=$2
    local entity_suffix=$3
    local unit=$4
    local friendly=$5
    local value

    value=$(upsc_var "${ups_name}" "${var_name}")
    if [[ -z "${value}" ]]; then
        return 0
    fi

    local attributes
    attributes=$(jq -n \
        --arg friendly_name "${friendly}" \
        --arg unit "${unit}" \
        --arg var_name "${var_name}" \
        '{
            friendly_name: $friendly_name,
            unit_of_measurement: $unit,
            nut_variable: $var_name
        }')

    ha_set_state "sensor.nut_addon_${ups_name}_${entity_suffix}" "${value}" "${attributes}"
}

sync_device() {
    local ups_name=$1
    local status_override=${2:-}

    sync_device_status "${ups_name}" "${status_override}"
    sync_device_numeric "${ups_name}" "battery.charge" "battery_charge" "%" "${ups_name} Battery Charge"
    sync_device_numeric "${ups_name}" "input.voltage" "input_voltage" "V" "${ups_name} Input Voltage"
    sync_device_numeric "${ups_name}" "ups.load" "load" "%" "${ups_name} UPS Load"
    sync_device_numeric "${ups_name}" "battery.runtime" "battery_runtime" "s" "${ups_name} Battery Runtime"
}

sync_event() {
    local ups_name=$1
    local notify_type=$2

    if ! sensors_enabled; then
        return 0
    fi

    if [[ " ${EVENT_TYPES} " != *" ${notify_type} "* ]]; then
        return 0
    fi

    load_monitor_env || return 0

    sync_device_status "${ups_name}" "${notify_type}"

    if [[ "${3:-}" == "--quick" ]]; then
        sync_device_numeric "${ups_name}" "battery.charge" "battery_charge" "%" "${ups_name} Battery Charge"
        sync_device_numeric "${ups_name}" "input.voltage" "input_voltage" "V" "${ups_name} Input Voltage"
        sync_device_numeric "${ups_name}" "ups.load" "load" "%" "${ups_name} UPS Load"
        sync_device_numeric "${ups_name}" "battery.runtime" "battery_runtime" "s" "${ups_name} Battery Runtime"
    fi
}

sync_all() {
    local ups_name

    if ! sensors_enabled; then
        return 0
    fi

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
