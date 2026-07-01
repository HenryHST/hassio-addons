#!/bin/bash
# shellcheck shell=bash
set -e

readonly CONFIG_PATH=/data/options.json
readonly DATA_DIR=/data

echo "-----------------------------------------------------------"
echo " BLS Nährwertdatenbank Add-on"
echo " Add-on Version: ${ADDON_VERSION:-unknown}"
echo " BLS Version: ${BLS_VERSION:-4.0}"
echo "-----------------------------------------------------------"

mkdir -p "${DATA_DIR}/downloads" "${DATA_DIR}/cache"

if [[ -f "${CONFIG_PATH}" ]]; then
    BLS_AUTO_UPDATE=$(jq -r '.auto_update // true' "${CONFIG_PATH}")
    BLS_UPDATE_INTERVAL_DAYS=$(jq -r '.update_interval_days // 30' "${CONFIG_PATH}")
    BLS_LANGUAGE=$(jq -r '.language // "de"' "${CONFIG_PATH}")
    BLS_ENABLE_OFF=$(jq -r '.enable_open_food_facts // true' "${CONFIG_PATH}")
    BLS_OFF_CACHE_TTL_DAYS=$(jq -r '.off_cache_ttl_days // 90' "${CONFIG_PATH}")
    BLS_OFF_SEARCH_CACHE_TTL_DAYS=$(jq -r '.off_search_cache_ttl_days // 7' "${CONFIG_PATH}")
    BLS_SEARCH_LAYOUT=$(jq -r '.search_layout // "stacked"' "${CONFIG_PATH}")
    BLS_SEARCH_RECENTS_ENABLED=$(jq -r '.search_recents_enabled // true' "${CONFIG_PATH}")
    BLS_TODO_LIST_ENABLED=$(jq -r '.todo_list_enabled // true' "${CONFIG_PATH}")
    BLS_TODO_LIST_ENTITY_ID=$(jq -r '.todo_list_entity_id // "todo.shopping_list"' "${CONFIG_PATH}")
    BLS_MAP_ENABLED=$(jq -r '.map_enabled // false' "${CONFIG_PATH}")
    BLS_MAP_RADIUS_KM=$(jq -r '.map_radius_km // 20' "${CONFIG_PATH}")
    BLS_FAVORITES_ENABLED=$(jq -r '.favorites_enabled // true' "${CONFIG_PATH}")
else
    BLS_AUTO_UPDATE=true
    BLS_UPDATE_INTERVAL_DAYS=30
    BLS_LANGUAGE=de
    BLS_ENABLE_OFF=true
    BLS_OFF_CACHE_TTL_DAYS=90
    BLS_OFF_SEARCH_CACHE_TTL_DAYS=7
    BLS_SEARCH_LAYOUT=stacked
    BLS_SEARCH_RECENTS_ENABLED=true
    BLS_TODO_LIST_ENABLED=true
    BLS_TODO_LIST_ENTITY_ID=todo.shopping_list
    BLS_MAP_ENABLED=false
    BLS_MAP_RADIUS_KM=20
    BLS_FAVORITES_ENABLED=true
fi

export BLS_AUTO_UPDATE
export BLS_UPDATE_INTERVAL_DAYS
export BLS_LANGUAGE
export BLS_ENABLE_OFF
export BLS_OFF_CACHE_TTL_DAYS
export BLS_OFF_SEARCH_CACHE_TTL_DAYS
export BLS_SEARCH_LAYOUT
export BLS_SEARCH_RECENTS_ENABLED
export BLS_TODO_LIST_ENABLED
export BLS_TODO_LIST_ENTITY_ID
export BLS_MAP_ENABLED
export BLS_MAP_RADIUS_KM
export BLS_FAVORITES_ENABLED

echo "[bls_nutrition] Configuration:"
echo "  - auto_update: ${BLS_AUTO_UPDATE}"
echo "  - update_interval_days: ${BLS_UPDATE_INTERVAL_DAYS}"
echo "  - language: ${BLS_LANGUAGE}"
echo "  - enable_open_food_facts: ${BLS_ENABLE_OFF}"
echo "  - off_cache_ttl_days: ${BLS_OFF_CACHE_TTL_DAYS}"
echo "  - off_search_cache_ttl_days: ${BLS_OFF_SEARCH_CACHE_TTL_DAYS}"
echo "  - search_layout: ${BLS_SEARCH_LAYOUT}"
echo "  - search_recents_enabled: ${BLS_SEARCH_RECENTS_ENABLED}"
echo "  - todo_list_enabled: ${BLS_TODO_LIST_ENABLED}"
echo "  - todo_list_entity_id: ${BLS_TODO_LIST_ENTITY_ID}"
echo "  - map_enabled: ${BLS_MAP_ENABLED}"
echo "  - map_radius_km: ${BLS_MAP_RADIUS_KM}"
echo "  - favorites_enabled: ${BLS_FAVORITES_ENABLED}"

echo "[bls_nutrition] Starting API on port 8090..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8090
