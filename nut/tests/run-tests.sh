#!/bin/bash
# shellcheck shell=bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "${script_dir}/test_upsmon_role.sh"
bash "${script_dir}/test_ups_status_map.sh"
bash "${script_dir}/test_mqtt_topic.sh"

echo "All NUT tests passed."
