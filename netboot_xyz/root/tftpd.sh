#!/bin/bash
# Launch in.tftpd with optional flags from add-on option tftpd_opts.
set -euo pipefail

OPTS_STR=""
if [[ -f /data/options.json ]]; then
  OPTS_STR=$(jq -r '.tftpd_opts // empty' /data/options.json)
fi

# Build argument array from whitespace-separated opts (e.g. --tftp-single-port)
extra_args=()
if [[ -n "${OPTS_STR}" ]]; then
  # shellcheck disable=SC2206
  extra_args=(${OPTS_STR})
  echo "[tftpd] Extra options: ${OPTS_STR}"
fi

exec /usr/sbin/in.tftpd -Lvvv --user nbxyz --secure /config/menus "${extra_args[@]}"
