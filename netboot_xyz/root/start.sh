#!/bin/bash
set -e

# Perform the initial configuration
echo "[netbootxyz] Starting initialization..."
if ! /bin/bash /init.sh; then
  echo "[netbootxyz] ERROR: Initialization failed"
  exit 1
fi
echo "[netbootxyz] Initialization completed successfully"

echo "            _   _                 _                      "
echo " _ __   ___| |_| |__   ___   ___ | |_  __  ___   _ ____  "
echo "| '_ \ / _ \ __| '_ \ / _ \ / _ \| __| \ \/ / | | |_  /  "
echo "| | | |  __/ |_| |_) | (_) | (_) | |_ _ >  <| |_| |/ /   "
echo "|_| |_|\___|\__|_.__/ \___/ \___/ \__(_)_/\_\\__,  /___| "
echo "                                             |___/       "
echo ""
echo "-----------------------------------------------------------"
echo " Home Assistant Add-on Version: ${ADDON_VERSION:-unknown}"
echo " netboot.xyz Core Version: ${NETBOOTXYZ_VERSION:-unknown}"
echo "-----------------------------------------------------------"
echo ""

supervisord -c /etc/supervisor.conf
