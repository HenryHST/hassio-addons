"""Tests for pure nutrient scaling helpers."""

from app.calculator import scale_nutrients, sum_nutrients


def test_scale_nutrients() -> None:
    scaled = scale_nutrients({"CHO": 10.0, "FAT": None}, 150.0)
    assert scaled["CHO"] == 15.0
    assert scaled["FAT"] is None


def test_scale_nutrients_100g() -> None:
    scaled = scale_nutrients({"CHO": 12.5}, 100.0)
    assert scaled["CHO"] == 12.5


def test_sum_nutrients() -> None:
    total = sum_nutrients(
        [
            {"CHO": 10.0, "FAT": 2.0},
            {"CHO": 5.0, "PROT625": 3.0},
        ]
    )
    assert total["CHO"] == 15.0
    assert total["FAT"] == 2.0
    assert total["PROT625"] == 3.0


def test_sum_nutrients_skips_none() -> None:
    total = sum_nutrients([{"CHO": 10.0, "FAT": None}, {"CHO": None, "FAT": 1.0}])
    assert total == {"CHO": 10.0, "FAT": 1.0}
