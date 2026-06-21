"""Sensor platform for BLS Nährwertdatenbank."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            BlsFoodCountSensor(coordinator, entry),
            BlsVersionSensor(coordinator, entry),
        ]
    )


class BlsSensorBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry


class BlsFoodCountSensor(BlsSensorBase):
    _attr_name = "Lebensmittel Anzahl"
    _attr_icon = "mdi:food-apple"
    _attr_native_unit_of_measurement = "Lebensmittel"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_food_count"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("food_count")


class BlsVersionSensor(BlsSensorBase):
    _attr_name = "BLS Version"
    _attr_icon = "mdi:database"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_bls_version"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("bls_version")
