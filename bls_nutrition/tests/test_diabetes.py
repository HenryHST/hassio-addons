"""Tests for diabetes unit calculations."""

from app.diabetes import compute_diabetes_units


def test_compute_from_cho() -> None:
    result = compute_diabetes_units({"CHO": 24.0})
    assert result["g_kh"] == 24.0
    assert result["be"] == 2.0
    assert result["ke"] == 2.4


def test_compute_from_carbohydrates_alias() -> None:
    result = compute_diabetes_units({"carbohydrates": 10.0})
    assert result["g_kh"] == 10.0
    assert result["be"] == round(10 / 12, 2)


def test_fpe_from_fat_and_protein() -> None:
    result = compute_diabetes_units({"CHO": 10.0, "FAT": 20.0, "PROT625": 5.0})
    assert result["fpe"] == 2.0


def test_fpe_from_energy_fallback() -> None:
    result = compute_diabetes_units({"CHO": 10.0, "ENERCC": 200.0})
    # remaining = 200 - 40 = 160 -> fpe = 1.6
    assert result["fpe"] == 1.6


def test_empty_nutrients() -> None:
    result = compute_diabetes_units({})
    assert result == {"g_kh": None, "be": None, "ke": None, "fpe": None}
