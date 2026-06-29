#!/bin/bash
# shellcheck shell=bash

# Map legacy NUT 2.7 master/slave roles to NUT 2.8+ primary/secondary.
normalize_upsmon_role() {
    case "$1" in
        master|primary) echo "primary" ;;
        slave|secondary) echo "secondary" ;;
        *)
            echo "unsupported upsmon role: $1" >&2
            return 1
            ;;
    esac
}

# Map ups.status tokens to MQTT status labels (FSD > LB > OB > OL).
map_ups_status() {
    local raw="${1:-}"
    local upper
    local tokens

    upper=$(printf '%s' "${raw}" | tr '[:lower:]' '[:upper:]')
    tokens=" ${upper} "

    if [[ "${tokens}" == *" FSD "* ]]; then
        echo "FSD"
    elif [[ "${tokens}" == *" LB "* ]]; then
        echo "LOWBATT"
    elif [[ "${tokens}" == *" OB "* ]]; then
        echo "ONBATT"
    elif [[ "${tokens}" == *" OL "* ]]; then
        echo "ONLINE"
    else
        echo "UNKNOWN"
    fi
}

# Build MQTT topic path: base + UPS name + suffix (no leading/trailing slashes on base).
mqtt_topic_path() {
    local base="${1:-}"
    local ups_name="${2:-}"
    local suffix="${3:-}"
    local path

    base="${base#/}"
    base="${base%/}"
    path="${base}/${ups_name}/${suffix}"
    path=$(printf '%s' "${path}" | tr -s '/')
    path="${path#/}"
    printf '%s' "${path}"
}
