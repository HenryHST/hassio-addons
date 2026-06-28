#!/bin/bash
# shellcheck shell=bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${script_dir}/../rootfs/usr/bin/nut-config-helpers.sh"

assert_status() {
    local input=$1
    local expected=$2
    local actual
    actual=$(map_ups_status "${input}")
    if [[ "${actual}" != "${expected}" ]]; then
        echo "map_ups_status '${input}': expected ${expected}, got ${actual}" >&2
        exit 1
    fi
}

assert_status "OL" "ONLINE"
assert_status "OB" "ONBATT"
assert_status "OB LB" "LOWBATT"
assert_status "OL FSD" "FSD"
assert_status "LB" "LOWBATT"
assert_status "" "UNKNOWN"
assert_status "CAL" "UNKNOWN"

echo "ups status mapping: ok"
