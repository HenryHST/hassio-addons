#!/bin/bash
# shellcheck shell=bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../rootfs/usr/bin/nut-config-helpers.sh
source "${script_dir}/../rootfs/usr/bin/nut-config-helpers.sh"

if [[ "$(normalize_upsmon_role master)" != "primary" ]]; then
    echo "master should map to primary" >&2
    exit 1
fi

if [[ "$(normalize_upsmon_role slave)" != "secondary" ]]; then
    echo "slave should map to secondary" >&2
    exit 1
fi

if [[ "$(normalize_upsmon_role primary)" != "primary" ]]; then
    echo "primary should stay primary" >&2
    exit 1
fi

echo "upsmon role normalization: ok"
