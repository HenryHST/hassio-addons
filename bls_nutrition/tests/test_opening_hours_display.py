"""Tests for opening hours display logic (no network)."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.opening_hours_display import (
    LocationContext,
    _holiday_info,
    build_opening_hours_display,
    enrich_map_items,
    is_open_now,
)


def _ctx(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    *,
    is_holiday: bool = False,
    holiday_name: str | None = None,
    is_sunday: bool | None = None,
) -> LocationContext:
    tz = ZoneInfo("Europe/Berlin")
    now = datetime(year, month, day, hour, 0, tzinfo=tz)
    if is_sunday is None:
        is_sunday = now.weekday() == 6
    return LocationContext(
        now=now,
        is_holiday=is_holiday,
        holiday_name=holiday_name,
        is_sunday=is_sunday,
    )


def test_holiday_closed_with_name() -> None:
    ctx = _ctx(2025, 12, 25, is_holiday=True, holiday_name="Weihnachten")
    assert (
        build_opening_hours_display("Mo-Fr 09:00-18:00", ctx)
        == "Geschlossen (Feiertag: Weihnachten)"
    )


def test_missing_opening_hours() -> None:
    ctx = _ctx(2025, 6, 23)
    assert build_opening_hours_display(None, ctx) == "Keine Angabe in OpenStreetMap"


def test_today_open() -> None:
    # 2025-06-23 is a Monday
    ctx = _ctx(2025, 6, 23, 14)
    display = build_opening_hours_display("Mo-Fr 09:00-18:00", ctx)
    assert display.startswith("Heute (Mo):")
    assert "09:00" in display


def test_sunday_shows_week() -> None:
    # 2025-06-22 is a Sunday
    ctx = _ctx(2025, 6, 22, is_sunday=True)
    display = build_opening_hours_display("Mo-Fr 09:00-18:00", ctx)
    assert "Mo:" in display
    assert "So:" in display


def test_is_open_now_true() -> None:
    ctx = _ctx(2025, 6, 23, 14)
    assert is_open_now("Mo-Fr 09:00-18:00", ctx) is True


def test_is_open_now_false_on_holiday() -> None:
    ctx = _ctx(2025, 12, 25, is_holiday=True)
    assert is_open_now("Mo-Su 00:00-24:00", ctx) is False


def test_is_open_now_unknown_hours() -> None:
    ctx = _ctx(2025, 6, 23)
    assert is_open_now(None, ctx) is None


def test_enrich_map_items() -> None:
    ctx = _ctx(2025, 6, 23, 14)
    items = [{"name": "REWE", "opening_hours": "Mo-Fr 09:00-18:00"}]
    enriched = enrich_map_items(items, ctx)
    assert len(enriched) == 1
    assert enriched[0]["is_open_now"] is True
    assert "opening_hours_display" in enriched[0]


def test_holiday_info_christmas_de() -> None:
    is_holiday, name = _holiday_info(datetime(2025, 12, 25).date(), "de", "BY")
    assert is_holiday is True
    assert name is not None
