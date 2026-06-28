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

# Map ups.status tokens to Home Assistant status labels (FSD > LB > OB > OL).
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
