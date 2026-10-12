#!/bin/bash
set -e

# make our folders
mkdir -p \
  /assets \
  /config/nginx/site-confs \
  /config/log/nginx \
  /run \
  /var/lib/nginx/tmp/client_body \
  /var/tmp/nginx

# copy config files (always update default to get latest changes)
[[ ! -f /config/nginx/nginx.conf ]] && \
  cp /defaults/nginx.conf /config/nginx/nginx.conf
# Always copy default site config to ensure updates
envsubst < /defaults/default > /config/nginx/site-confs/default

# Ownership
chown -R nbxyz:nbxyz /assets
chown -R nbxyz:nbxyz /var/lib/nginx
chown -R nbxyz:nbxyz /var/log/nginx

# create local logs dir
mkdir -p \
  /config/menus/remote \
  /config/menus/local

# Resolve menu release tag (netboot.xyz releases), NOT the webapp version.
# NETBOOTXYZ_VERSION is the webapp pin (e.g. 0.7.6) and must not be used here.
MENU_VERSION=""
if [[ -f /data/options.json ]]; then
  MENU_VERSION=$(jq -r '.menu_version // empty' /data/options.json)
fi
if [[ -z "${MENU_VERSION}" && -f /config/menuversion.txt ]]; then
  MENU_VERSION=$(tr -d '[:space:]' < /config/menuversion.txt)
fi
if [[ -z "${MENU_VERSION}" ]]; then
  MENU_VERSION=$(curl -fsSL "https://api.github.com/repos/netbootxyz/netboot.xyz/releases/latest" | jq -r '.tag_name // empty')
fi
if [[ -z "${MENU_VERSION}" || "${MENU_VERSION}" == "null" ]]; then
  MENU_VERSION="3.0.3"
fi

# download menus if not found
if [[ ! -f /config/menus/remote/menu.ipxe ]]; then
  echo "[netbootxyz-init] Downloading netboot.xyz at ${MENU_VERSION}"
  MENUS_URL="https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/menus.tar.gz"
  # menu files
  curl -fsSL -o \
    /config/endpoints.yml \
    "https://raw.githubusercontent.com/netbootxyz/netboot.xyz/${MENU_VERSION}/endpoints.yml"
  curl -fsSL -o \
    /tmp/menus.tar.gz \
    "${MENUS_URL}"
  tar xf \
    /tmp/menus.tar.gz -C \
    /config/menus/remote
  # boot files
  curl -fsSL -o \
    /config/menus/remote/netboot.xyz.kpxe \
    "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/netboot.xyz.kpxe"
  curl -fsSL -o \
    /config/menus/remote/netboot.xyz-undionly.kpxe \
    "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/netboot.xyz-undionly.kpxe"
  curl -fsSL -o \
    /config/menus/remote/netboot.xyz.efi \
    "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/netboot.xyz.efi"
  curl -fsSL -o \
    /config/menus/remote/netboot.xyz-snp.efi \
    "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/netboot.xyz-snp.efi"
  curl -fsSL -o \
    /config/menus/remote/netboot.xyz-snponly.efi \
    "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/netboot.xyz-snponly.efi"
  curl -fsSL -o \
    /config/menus/remote/netboot.xyz-arm64.efi \
    "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/netboot.xyz-arm64.efi"
  curl -fsSL -o \
    /config/menus/remote/netboot.xyz-arm64-snp.efi \
    "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/netboot.xyz-arm64-snp.efi"
  curl -fsSL -o \
    /config/menus/remote/netboot.xyz-arm64-snponly.efi \
    "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/netboot.xyz-arm64-snponly.efi"
  # layer and cleanup
  echo -n "${MENU_VERSION}" > /config/menuversion.txt
  cp -r /config/menus/remote/* /config/menus
  rm -f /tmp/menus.tar.gz
fi

# Ownership
chown -R nbxyz:nbxyz /config
