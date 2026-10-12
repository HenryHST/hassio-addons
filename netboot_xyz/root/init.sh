#!/bin/bash
set -e

# make our folders
mkdir -p \
  /assets \
  /config/nginx/site-confs \
  /config/log/nginx \
  /config/status \
  /run \
  /var/lib/nginx/tmp/client_body \
  /var/tmp/nginx

# Default NGINX_PORT for host-network (avoid conflict with host :80)
export NGINX_PORT="${NGINX_PORT:-8080}"

# copy config files (always update default to get latest changes)
[[ ! -f /config/nginx/nginx.conf ]] && \
  cp /defaults/nginx.conf /config/nginx/nginx.conf
# Always copy default site config to ensure updates
envsubst '${NGINX_PORT}' < /defaults/default > /config/nginx/site-confs/default

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
ENABLE_SECURE_BOOT=true
IPXE_SB_VERSION="v2.0.0"
if [[ -f /data/options.json ]]; then
  configured_menu=$(jq -r '.menu_version // empty' /data/options.json)
  if [[ -n "${configured_menu}" ]]; then
    MENU_VERSION="${configured_menu}"
  fi
  enable_sb=$(jq -r '.enable_secure_boot // true' /data/options.json)
  if [[ "${enable_sb}" == "false" ]]; then
    ENABLE_SECURE_BOOT=false
  fi
  configured_sb=$(jq -r '.ipxe_sb_version // empty' /data/options.json)
  if [[ -n "${configured_sb}" ]]; then
    IPXE_SB_VERSION="${configured_sb}"
  fi
fi

stamp_last_download() {
  date -u +"%Y-%m-%dT%H:%M:%SZ" > /config/status/last_download.txt
}

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
  stamp_last_download
fi

# Secure Boot files (runs independently of menu download):
# - Signed EFI binaries from upstream iPXE (ipxeboot.tar.gz) — unmodified
# - autoexec.ipxe from the netboot.xyz menu release
# Tolerant of failures so older menu pins without autoexec.ipxe still start
if [[ "${ENABLE_SECURE_BOOT}" == "true" ]] && [[ ! -d /config/menus/remote/secureboot-x86_64 ]]; then
  echo "[netbootxyz-init] Downloading Secure Boot binaries (iPXE ${IPXE_SB_VERSION})..."
  set +e
  curl -fsSL -o /tmp/ipxeboot.tar.gz \
    "https://github.com/ipxe/ipxe/releases/download/${IPXE_SB_VERSION}/ipxeboot.tar.gz"
  curl_rc=$?
  set -e
  if [[ ${curl_rc} -eq 0 ]] && [[ -f /tmp/ipxeboot.tar.gz ]] && [[ -s /tmp/ipxeboot.tar.gz ]]; then
    if tar xf /tmp/ipxeboot.tar.gz -C /tmp; then
      mkdir -p \
        /config/menus/remote/secureboot-x86_64 \
        /config/menus/remote/secureboot-arm64
      for f in shimx64.efi ipxe-shim.efi ipxe.efi snponly.efi snponly-shim.efi; do
        if [[ -f "/tmp/ipxeboot/x86_64-sb/${f}" ]]; then
          cp "/tmp/ipxeboot/x86_64-sb/${f}" /config/menus/remote/secureboot-x86_64/
        else
          echo "[netbootxyz-init] Warning: ${f} not found in iPXE x86_64-sb archive"
        fi
      done
      for f in shimaa64.efi ipxe-shim.efi ipxe.efi snponly.efi snponly-shim.efi; do
        if [[ -f "/tmp/ipxeboot/arm64-sb/${f}" ]]; then
          cp "/tmp/ipxeboot/arm64-sb/${f}" /config/menus/remote/secureboot-arm64/
        else
          echo "[netbootxyz-init] Warning: ${f} not found in iPXE arm64-sb archive"
        fi
      done
      set +e
      curl -fsSL -o /tmp/autoexec.ipxe \
        "https://github.com/netbootxyz/netboot.xyz/releases/download/${MENU_VERSION}/autoexec.ipxe"
      autoexec_rc=$?
      set -e
      if [[ ${autoexec_rc} -eq 0 ]]; then
        cp /tmp/autoexec.ipxe /config/menus/remote/secureboot-x86_64/autoexec.ipxe
        cp /tmp/autoexec.ipxe /config/menus/remote/secureboot-arm64/autoexec.ipxe
        rm -f /tmp/autoexec.ipxe
      else
        echo "[netbootxyz-init] autoexec.ipxe not available for ${MENU_VERSION}, skipping"
      fi
      shopt -s nullglob
      for sbdir in /config/menus/remote/secureboot-*/; do
        cp -r "$sbdir" /config/menus/
      done
      shopt -u nullglob
      echo "[netbootxyz-init] Secure Boot files layered under /config/menus/secureboot-*"
      echo -n "enabled" > /config/status/secure_boot.txt
      stamp_last_download
    else
      echo "[netbootxyz-init] Failed to extract iPXE Secure Boot archive, skipping"
      echo -n "failed" > /config/status/secure_boot.txt
    fi
    rm -rf /tmp/ipxeboot /tmp/ipxeboot.tar.gz
  else
    echo "[netbootxyz-init] iPXE Secure Boot archive not available, skipping"
    echo -n "failed" > /config/status/secure_boot.txt
    rm -f /tmp/ipxeboot.tar.gz
  fi
elif [[ "${ENABLE_SECURE_BOOT}" != "true" ]]; then
  echo "[netbootxyz-init] Secure Boot download disabled (enable_secure_boot=false)"
  echo -n "disabled" > /config/status/secure_boot.txt
elif [[ -d /config/menus/remote/secureboot-x86_64 ]]; then
  echo -n "enabled" > /config/status/secure_boot.txt
fi

# Ownership
chown -R nbxyz:nbxyz /config
