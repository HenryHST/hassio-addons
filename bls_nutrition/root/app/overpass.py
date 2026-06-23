"""OpenStreetMap Overpass helpers for nearby supermarkets."""

from __future__ import annotations

import math
from typing import Any

import httpx


class OverpassError(Exception):
    """Raised when Overpass query fails."""


OVERPASS_URL = "https://overpass-api.de/api/interpreter"
EARTH_RADIUS_KM = 6371.0


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1r = math.radians(lat1)
    lon1r = math.radians(lon1)
    lat2r = math.radians(lat2)
    lon2r = math.radians(lon2)
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def _overpass_query(lat: float, lon: float, radius_m: int) -> str:
    return f"""
[out:json][timeout:20];
(
  node["shop"~"supermarket|convenience"](around:{radius_m},{lat},{lon});
  way["shop"~"supermarket|convenience"](around:{radius_m},{lat},{lon});
);
out center tags;
""".strip()


def find_supermarkets(lat: float, lon: float, radius_km: int) -> list[dict[str, Any]]:
    radius_m = max(100, min(50000, int(radius_km * 1000)))
    query = _overpass_query(lat, lon, radius_m)
    try:
        with httpx.Client(timeout=25.0) as client:
            response = client.post(OVERPASS_URL, data={"data": query})
    except httpx.RequestError as exc:
        raise OverpassError(f"Overpass nicht erreichbar: {exc}") from exc
    if response.status_code >= 400:
        detail = response.text.strip() or response.reason_phrase
        raise OverpassError(f"Overpass Fehler ({response.status_code}): {detail}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise OverpassError("Overpass hat ungueltige Daten geliefert.") from exc
    elements = payload.get("elements") if isinstance(payload, dict) else None
    if not isinstance(elements, list):
        raise OverpassError("Overpass-Antwort enthaelt keine Elementliste.")

    results: list[dict[str, Any]] = []
    for el in elements:
        if not isinstance(el, dict):
            continue
        tags = el.get("tags") or {}
        if not isinstance(tags, dict):
            tags = {}
        lat_value = el.get("lat")
        lon_value = el.get("lon")
        center = el.get("center") if isinstance(el.get("center"), dict) else None
        if lat_value is None and center:
            lat_value = center.get("lat")
        if lon_value is None and center:
            lon_value = center.get("lon")
        try:
            poi_lat = float(lat_value)
            poi_lon = float(lon_value)
        except (TypeError, ValueError):
            continue
        name = str(tags.get("name") or "Unbenannter Markt").strip()
        house = str(tags.get("addr:housenumber") or "").strip()
        street = str(tags.get("addr:street") or "").strip()
        city = str(tags.get("addr:city") or "").strip()
        address_parts = [part for part in [street, house, city] if part]
        distance = _distance_km(lat, lon, poi_lat, poi_lon)
        results.append(
            {
                "id": f"{el.get('type', 'poi')}-{el.get('id', 'unknown')}",
                "name": name,
                "lat": poi_lat,
                "lon": poi_lon,
                "type": str(tags.get("shop") or "supermarket"),
                "address": ", ".join(address_parts) if address_parts else None,
                "distance_km": round(distance, 2),
            }
        )

    results.sort(key=lambda item: item["distance_km"])
    return results
