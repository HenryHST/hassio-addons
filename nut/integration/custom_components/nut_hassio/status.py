"""Map NUT ups.status tokens to Home Assistant status labels."""

from __future__ import annotations

from .const import (
    STATUS_FSD,
    STATUS_LOWBATT,
    STATUS_ONBATT,
    STATUS_ONLINE,
    STATUS_UNKNOWN,
)


def map_ups_status(raw: str | None) -> str:
    """Return primary status with priority FSD > LB > OB > OL."""
    if not raw:
        return STATUS_UNKNOWN
    tokens = f" {raw.upper()} "
    if " FSD " in tokens:
        return STATUS_FSD
    if " LB " in tokens:
        return STATUS_LOWBATT
    if " OB " in tokens:
        return STATUS_ONBATT
    if " OL " in tokens:
        return STATUS_ONLINE
    return STATUS_UNKNOWN
