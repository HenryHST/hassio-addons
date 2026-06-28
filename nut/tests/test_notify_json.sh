#!/bin/bash
# shellcheck shell=bash
set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
    echo "jq is required" >&2
    exit 1
fi

payload=$(jq -n \
    --arg ups_name 'myups' \
    --arg notify_type 'ONLINE' \
    --arg notify_msg 'test message' \
    '{ups_name: $ups_name, notify_type: $notify_type, notify_msg: $notify_msg}')

echo "${payload}" | jq -e '.ups_name == "myups"' >/dev/null
echo "${payload}" | jq -e '.notify_type == "ONLINE"' >/dev/null
echo "${payload}" | jq -e '.notify_msg == "test message"' >/dev/null

# Ensure special characters are escaped safely
payload2=$(jq -n \
    --arg ups_name 'ups' \
    --arg notify_type 'COMMBAD' \
    --arg notify_msg 'quote " and backslash \\ test' \
    '{ups_name: $ups_name, notify_type: $notify_type, notify_msg: $notify_msg}')

echo "${payload2}" | jq -e '.notify_msg | contains("quote")' >/dev/null

echo "notify JSON encoding: ok"
