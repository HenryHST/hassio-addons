#!/bin/bash
# shellcheck shell=bash

# Map legacy NUT 2.7 master/slave roles to NUT 2.8+ primary/secondary.
normalize_upsmon_role() {
    case "$1" in
        master|primary) echo "primary" ;;
        slave|secondary) echo "secondary" ;;
        *)
            echo "unsupported upsmon role: $1" >&2
            return 1
            ;;
    esac
}
