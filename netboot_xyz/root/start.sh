#!/bin/bash
set -e

# Perform the initial configuration
echo "[netbootxyz] Starting initialization..."
if ! /bin/bash /init.sh; then
  echo "[netbootxyz] ERROR: Initialization failed"
  exit 1
fi
echo "[netbootxyz] Initialization completed successfully"
# #region agent log
MENU_FILE_STATE="missing"
[[ -f /config/menus/remote/menu.ipxe ]] && MENU_FILE_STATE="present"
STORED_MENU_VERSION="unset"
[[ -f /config/menuversion.txt ]] && STORED_MENU_VERSION=$(tr -d '[:space:]' < /config/menuversion.txt)
echo "[netbootxyz] DEBUG post-init menu.ipxe=${MENU_FILE_STATE} menuversion=${STORED_MENU_VERSION}"
# #endregion

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
