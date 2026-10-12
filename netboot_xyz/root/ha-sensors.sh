#!/bin/bash
# Push netboot.xyz status to Home Assistant via Supervisor Core API.
set -euo pipefail

ENABLE_HA_SENSORS=true
POLL_INTERVAL=60

if [[ -f /data/options.json ]]; then
  # jq's // treats JSON false as missing — use explicit null check
  enable=$(jq -r 'if .enable_ha_sensors == null then true else .enable_ha_sensors end' /data/options.json)
  if [[ "${enable}" == "false" ]]; then
    ENABLE_HA_SENSORS=false
  fi
  interval=$(jq -r '.sensor_poll_interval // 60' /data/options.json)
  if [[ "${interval}" =~ ^[0-9]+$ ]] && [[ "${interval}" -ge 30 ]] && [[ "${interval}" -le 300 ]]; then
    POLL_INTERVAL="${interval}"
  fi
fi

if [[ "${ENABLE_HA_SENSORS}" != "true" ]]; then
  echo "[ha-sensors] Disabled (enable_ha_sensors=false); sleeping"
  while true; do sleep 3600; done
fi

if [[ -z "${SUPERVISOR_TOKEN:-}" ]]; then
  echo "[ha-sensors] SUPERVISOR_TOKEN missing; cannot publish states"
  while true; do sleep 3600; done
fi

publish_state() {
  local entity_id="$1"
  local state="$2"
  # ${3:-{}} appends a literal "}" when $3 is set; use quoted "{}"
  local attributes_json="${3:-"{}"}"
  local payload

  payload=$(jq -n \
    --arg state "${state}" \
    --argjson attributes "${attributes_json}" \
    '{state: $state, attributes: $attributes}')

  if ! curl -fsS -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${payload}" \
    "http://supervisor/core/api/states/${entity_id}" >/dev/null; then
    echo "[ha-sensors] Warning: failed to publish ${entity_id}"
  fi
}

echo "[ha-sensors] Publishing every ${POLL_INTERVAL}s"

while true; do
  menu_version="unknown"
  if [[ -f /config/menuversion.txt ]]; then
    menu_version=$(tr -d '[:space:]' < /config/menuversion.txt)
    [[ -z "${menu_version}" ]] && menu_version="unknown"
  fi

  last_download="unknown"
  if [[ -f /config/status/last_download.txt ]]; then
    last_download=$(tr -d '[:space:]' < /config/status/last_download.txt)
    [[ -z "${last_download}" ]] && last_download="unknown"
  fi

  secure_boot="unknown"
  if [[ -f /config/status/secure_boot.txt ]]; then
    secure_boot=$(tr -d '[:space:]' < /config/status/secure_boot.txt)
    [[ -z "${secure_boot}" ]] && secure_boot="unknown"
  fi

  tftp_state="off"
  tftpd_status=$(supervisorctl -c /etc/supervisor.conf status in.tftpd 2>/dev/null || true)
  if echo "${tftpd_status}" | grep -q RUNNING; then
    tftp_state="on"
  fi

  menus_present="false"
  if [[ -f /config/menus/menu.ipxe ]]; then
    menus_present="true"
  fi

  publish_state "sensor.netboot_xyz_menu_version" "${menu_version}" \
    "$(jq -n --arg fn "netboot.xyz Menu Version" '{friendly_name: $fn, icon: "mdi:file-tree"}')"

  publish_state "sensor.netboot_xyz_last_download" "${last_download}" \
    "$(jq -n --arg fn "netboot.xyz Last Download" --arg sb "${secure_boot}" \
      '{friendly_name: $fn, icon: "mdi:download", secure_boot: $sb}')"

  publish_state "binary_sensor.netboot_xyz_tftp" "${tftp_state}" \
    "$(jq -n --arg fn "netboot.xyz TFTP" --arg mp "${menus_present}" \
      '{friendly_name: $fn, icon: "mdi:lan-connect", device_class: "connectivity", menus_present: ($mp == "true")}')"

  sleep "${POLL_INTERVAL}"
done
