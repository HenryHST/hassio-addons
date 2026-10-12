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

# Resolve desired menu release tag (netboot.xyz releases), NOT the webapp version.
# NETBOOTXYZ_VERSION is the webapp pin (e.g. 0.7.6) and must not be used here.
DEFAULT_MENU_VERSION="3.0.3"
MENU_VERSION="${DEFAULT_MENU_VERSION}"
if [[ -f /data/options.json ]]; then
  configured_menu=$(jq -r '.menu_version // empty' /data/options.json)
  if [[ -n "${configured_menu}" ]]; then
    MENU_VERSION="${configured_menu}"
  fi
fi

INSTALLED_MENU_VERSION=""
if [[ -f /config/menuversion.txt ]]; then
  INSTALLED_MENU_VERSION=$(tr -d '[:space:]' < /config/menuversion.txt)
fi

# Download when menus are missing or the stored version differs from the desired pin
if [[ ! -f /config/menus/remote/menu.ipxe ]] || [[ "${INSTALLED_MENU_VERSION}" != "${MENU_VERSION}" ]]; then
  echo "[netbootxyz-init] Downloading netboot.xyz at ${MENU_VERSION}"
  # Clear previous remote menus when upgrading between versions
  rm -rf /config/menus/remote
  mkdir -p /config/menus/remote

  # menu files
  curl -fsSL -o \
    /config/endpoints.yml \
    "https://raw.githubusercontent.com/netbootxyz/netboot.xyz/${MENU_VERSION}/endpoints.yml"
  curl -fsSL -o \
    /tmp/menus.tar.gz \
    "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/menus.tar.gz"
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
  # legacy boot files (3.x+; no USB NIC drivers — preserve USB keyboard on some firmware)
  for legacy_file in netboot.xyz-legacy.kpxe netboot.xyz-legacy.efi; do
    if curl -fsSL -o "/config/menus/remote/${legacy_file}" \
      "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/${legacy_file}"; then
      echo "[netbootxyz-init] Downloaded ${legacy_file}"
    else
      echo "[netbootxyz-init] ${legacy_file} not available for ${MENU_VERSION}, skipping"
      rm -f "/config/menus/remote/${legacy_file}"
    fi
  done
  # layer and cleanup
  echo -n "${MENU_VERSION}" > /config/menuversion.txt
  cp -r /config/menus/remote/* /config/menus
  rm -f /tmp/menus.tar.gz
fi

# Ownership
chown -R nbxyz:nbxyz /config
