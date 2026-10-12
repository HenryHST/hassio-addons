#!/bin/bash
# Push netboot.xyz status to Home Assistant via Supervisor Core API.
set -euo pipefail

ENABLE_HA_SENSORS=true
POLL_INTERVAL=60

if [[ -f /data/options.json ]]; then
  enable=$(jq -r '.enable_ha_sensors // true' /data/options.json)
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

# #region agent log
_dbg() {
  local hyp="$1" msg="$2" data="$3"
  local line
  line=$(jq -nc --arg sid "92f7bb" --arg hyp "${hyp}" --arg msg "${msg}" --argjson data "${data}" \
    --arg loc "ha-sensors.sh" --arg run "post-fix" \
    '{sessionId:$sid,runId:$run,hypothesisId:$hyp,location:$loc,message:$msg,data:$data,timestamp:(now*1000|floor)}' 2>/dev/null || true)
  [[ -n "${line}" ]] && echo "[ha-sensors-debug] ${line}"
  mkdir -p /config/status 2>/dev/null || true
  [[ -n "${line}" ]] && echo "${line}" >> /config/status/debug-ha-sensors.ndjson 2>/dev/null || true
  curl -fsS -m 1 -X POST \
    -H 'Content-Type: application/json' \
    -H 'X-Debug-Session-Id: 92f7bb' \
    -d "${line}" \
    'http://127.0.0.1:7737/ingest/27302f83-b01b-4083-886f-80acfc734226' >/dev/null 2>&1 || true
}
# #endregion

publish_state() {
  local entity_id="$1"
  local state="$2"
  # Fix: ${3:-{}} appends a literal "}" when $3 is set → invalid JSON for --argjson
  local attributes_json="${3:-"{}"}"
  local payload
  local tail2

  # #region agent log
  tail2=$(printf '%s' "${attributes_json}" | tail -c 2)
  _dbg "A" "publish_state attrs" \
    "$(jq -nc --arg e "${entity_id}" --argjson len "${#attributes_json}" --arg tail "${tail2}" \
      '{entity:$e,attr_len:$len,attr_tail:$tail}')"
  # #endregion

  payload=$(jq -n \
    --arg state "${state}" \
    --argjson attributes "${attributes_json}" \
    '{state: $state, attributes: $attributes}')

  # #region agent log
  _dbg "A" "publish_state payload_ok" \
    "$(jq -nc --arg e "${entity_id}" --argjson plen "${#payload}" '{entity:$e,payload_len:$plen}')"
  # #endregion

  if ! curl -fsS -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${payload}" \
    "http://supervisor/core/api/states/${entity_id}" >/dev/null; then
    echo "[ha-sensors] Warning: failed to publish ${entity_id}"
    # #region agent log
    _dbg "B" "curl publish failed" "$(jq -nc --arg e "${entity_id}" '{entity:$e}')"
    # #endregion
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

  # #region agent log
  _dbg "C" "loop_ok" "$(jq -nc --arg mv "${menu_version}" --arg tftp "${tftp_state}" '{menu:$mv,tftp:$tftp}')"
  # #endregion

  sleep "${POLL_INTERVAL}"
done
