"""Context-aware opening hours display for map supermarkets."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import holidays
import httpx
from osm_time import ParseException
from osm_time.opening_hours import OpeningHours

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
CACHE_FILENAME = "map_location_cache.json"
MISSING_OS = "Keine Angabe in OpenStreetMap"
DAY_KEYS = ("mo", "tu", "we", "th", "fr", "sa", "su")
DAY_LABELS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")


@dataclass(frozen=True)
class LocationContext:
    now: datetime
    is_holiday: bool
    holiday_name: str | None
    is_sunday: bool


def _request_headers() -> dict[str, str]:
    version = os.environ.get("ADDON_VERSION", "dev")
    return {
        "User-Agent": f"bls-nutrition-addon/{version} (Home Assistant; +https://github.com/henryhst/hassio-addons)",
        "Accept": "application/json",
    }


def _cache_path(data_dir: Path) -> Path:
    return data_dir / CACHE_FILENAME


def _coords_changed(lat: float, lon: float, cached: dict[str, Any]) -> bool:
    try:
        cached_lat = float(cached["lat"])
        cached_lon = float(cached["lon"])
    except (KeyError, TypeError, ValueError):
        return True
    return abs(cached_lat - lat) > 0.01 or abs(cached_lon - lon) > 0.01


def _load_cache(data_dir: Path) -> dict[str, Any] | None:
    path = _cache_path(data_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _save_cache(data_dir: Path, payload: dict[str, Any]) -> None:
    path = _cache_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _reverse_geocode(lat: float, lon: float) -> dict[str, str]:
    params = {
        "lat": str(lat),
        "lon": str(lon),
        "format": "json",
        "addressdetails": "1",
        "zoom": "10",
    }
    with httpx.Client(timeout=15.0) as client:
        response = client.get(NOMINATIM_URL, params=params, headers=_request_headers())
    if response.status_code >= 400:
        raise RuntimeError(f"Nominatim Fehler ({response.status_code})")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Nominatim lieferte keine gueltigen Daten.")
    address = payload.get("address")
    if not isinstance(address, dict):
        address = {}
    country_code = str(address.get("country_code") or "").lower()
    state = str(address.get("state") or "").strip()
    iso = str(address.get("ISO3166-2-lvl4") or "")
    subdiv = ""
    if iso.startswith("DE-"):
        subdiv = iso[3:]
    return {
        "country_code": country_code,
        "state": state,
        "subdiv": subdiv,
    }


def _resolve_region(lat: float, lon: float, data_dir: Path) -> dict[str, str]:
    cached = _load_cache(data_dir)
    if cached and not _coords_changed(lat, lon, cached):
        return {
            "country_code": str(cached.get("country_code") or "").lower(),
            "subdiv": str(cached.get("subdiv") or ""),
            "state": str(cached.get("state") or ""),
        }
    try:
        region = _reverse_geocode(lat, lon)
    except (httpx.RequestError, RuntimeError):
        if cached:
            return {
                "country_code": str(cached.get("country_code") or "de").lower(),
                "subdiv": str(cached.get("subdiv") or ""),
                "state": str(cached.get("state") or ""),
            }
        return {"country_code": "de", "subdiv": "", "state": ""}
    _save_cache(
        data_dir,
        {
            "lat": lat,
            "lon": lon,
            "country_code": region["country_code"],
            "subdiv": region["subdiv"],
            "state": region["state"],
        },
    )
    return region


def _holiday_info(
    on_date: date, country_code: str, subdiv: str
) -> tuple[bool, str | None]:
    country = (country_code or "de").upper()
    kwargs: dict[str, Any] = {"years": on_date.year}
    if country == "DE" and subdiv:
        kwargs["subdiv"] = subdiv
    try:
        calendar = holidays.country_holidays(country, **kwargs)
    except NotImplementedError:
        calendar = holidays.country_holidays("DE", years=on_date.year)
    name = calendar.get(on_date)
    if name:
        return True, str(name)
    return False, None


def get_location_context(
    latitude: float,
    longitude: float,
    time_zone: str,
    data_dir: Path,
) -> LocationContext:
    tz_name = time_zone or "UTC"
    try:
        now = datetime.now(ZoneInfo(tz_name))
    except Exception:
        now = datetime.now(ZoneInfo("UTC"))
    region = _resolve_region(latitude, longitude, data_dir)
    is_holiday, holiday_name = _holiday_info(
        now.date(), region["country_code"], region["subdiv"]
    )
    return LocationContext(
        now=now,
        is_holiday=is_holiday,
        holiday_name=holiday_name,
        is_sunday=now.weekday() == 6,
    )


def _minutes_to_time(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def _format_ranges(ranges: list[tuple[int, int]]) -> str:
    if not ranges:
        return "geschlossen"
    parts: list[str] = []
    for start, end in ranges:
        parts.append(f"{_minutes_to_time(start)}–{_minutes_to_time(end)}")
    return ", ".join(parts)


def _format_today(raw: str, now: datetime) -> str:
    try:
        parsed = OpeningHours(raw)
    except ParseException:
        return raw.strip()
    if parsed.is_always_open:
        return "Rund um die Uhr"
    day_key = DAY_KEYS[now.weekday()]
    label = DAY_LABELS[now.weekday()]
    ranges = parsed.get_as_dictionnary().get(day_key, [])
    hours = _format_ranges(ranges)
    if hours == "geschlossen":
        return f"Heute ({label}): geschlossen"
    return f"Heute ({label}): {hours}"


def _format_week(raw: str) -> str:
    try:
        parsed = OpeningHours(raw)
    except ParseException:
        return raw.strip()
    if parsed.is_always_open:
        return "Rund um die Uhr"
    schedule = parsed.get_as_dictionnary()
    lines: list[str] = []
    for key, label in zip(DAY_KEYS, DAY_LABELS, strict=True):
        hours = _format_ranges(schedule.get(key, []))
        lines.append(f"{label}: {hours}")
    return "\n".join(lines)


def build_opening_hours_display(raw: str | None, ctx: LocationContext) -> str:
    if ctx.is_holiday:
        if ctx.holiday_name:
            return f"Geschlossen (Feiertag: {ctx.holiday_name})"
        return "Geschlossen (Feiertag)"
    if not raw or not raw.strip():
        return MISSING_OS
    value = raw.strip()
    if ctx.is_sunday:
        return _format_week(value)
    return _format_today(value, ctx.now)


def enrich_map_items(
    items: list[dict[str, Any]], ctx: LocationContext
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for item in items:
        copy = dict(item)
        raw = copy.get("opening_hours")
        raw_str = str(raw).strip() if raw else None
        copy["opening_hours"] = raw_str
        copy["opening_hours_display"] = build_opening_hours_display(raw_str, ctx)
        enriched.append(copy)
    return enriched
