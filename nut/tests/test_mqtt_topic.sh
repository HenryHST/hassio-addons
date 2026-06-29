#!/bin/bash
# shellcheck shell=bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${script_dir}/../rootfs/usr/bin/nut-config-helpers.sh"

result=$(mqtt_topic_path "nut/ups" "myups" "status")
[[ "${result}" == "nut/ups/myups/status" ]] || {
    echo "expected nut/ups/myups/status, got ${result}" >&2
    exit 1
}

result=$(mqtt_topic_path "/home/ups/" "up2a" "battery_charge")
[[ "${result}" == "home/ups/up2a/battery_charge" ]] || {
    echo "expected home/ups/up2a/battery_charge, got ${result}" >&2
    exit 1
}

result=$(mqtt_topic_path "///bad//" "x" "status")
[[ "${result}" == "bad/x/status" ]] || {
    echo "expected bad/x/status, got ${result}" >&2
    exit 1
}

echo "mqtt topic path: ok"
