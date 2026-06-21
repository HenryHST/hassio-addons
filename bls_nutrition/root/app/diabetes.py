"""Diabetes unit calculations (WETID-inspired)."""

from __future__ import annotations

from typing import Any


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_diabetes_units(
    nutrients: dict[str, float | None],
) -> dict[str, float | None]:
    """Compute gKH, BE, KE and FPE from scaled nutrient values."""
    carbs = _num(nutrients.get("CHO")) or _num(nutrients.get("carbohydrates"))
    fat = _num(nutrients.get("FAT")) or _num(nutrients.get("fat"))
    protein = _num(nutrients.get("PROT625")) or _num(nutrients.get("proteins"))
    energy = _num(nutrients.get("ENERCC")) or _num(nutrients.get("energy_kcal"))

    g_kh = carbs
    be = round(g_kh / 12, 2) if g_kh is not None else None
    ke = round(g_kh / 10, 2) if g_kh is not None else None

    fpe: float | None = None
    if fat is not None and protein is not None:
        fpe = round((fat * 9 + protein * 4) / 100, 2)
    elif energy is not None and g_kh is not None:
        remaining = energy - g_kh * 4
        if remaining > 0:
            fpe = round(remaining / 100, 2)

    return {
        "g_kh": round(g_kh, 2) if g_kh is not None else None,
        "be": be,
        "ke": ke,
        "fpe": fpe,
    }
