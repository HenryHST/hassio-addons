"""Sensor platform for NUT Hass.io."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_UPS_NAME, DOMAIN, NUMERIC_SENSORS, NOTIFY_STATUSES
from .coordinator import NutHassioCoordinator

UNIT_MAP = {
    "%": PERCENTAGE,
    "V": UnitOfElectricPotential.VOLT,
    "s": UnitOfTime.SECONDS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NutHassioCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        NutStatusSensor(coordinator, entry),
    ]
    for var_name, suffix, unit in NUMERIC_SENSORS:
        entities.append(NutNumericSensor(coordinator, entry, var_name, suffix, unit))
    async_add_entities(entities)


class NutDeviceEntity(CoordinatorEntity[NutHassioCoordinator], SensorEntity):
    """Base entity for a UPS device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NutHassioCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._ups_name = entry.data[CONF_UPS_NAME]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._ups_name)},
            name=f"UPS {self._ups_name}",
            manufacturer="Network UPS Tools",
            model=self._ups_name,
        )


class NutStatusSensor(NutDeviceEntity):
    """UPS status sensor (ONLINE / ONBATT / LOWBATT / FSD)."""

    def __init__(self, coordinator: NutHassioCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._ups_name}_status"
        self._attr_name = "Status"
        self._attr_options = list(NOTIFY_STATUSES) + ["UNKNOWN"]

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("status")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "raw_status": self.coordinator.data.get("raw_status"),
        }


class NutNumericSensor(NutDeviceEntity):
    """Numeric UPS variable sensor."""

    def __init__(
        self,
        coordinator: NutHassioCoordinator,
        entry: ConfigEntry,
        var_name: str,
        suffix: str,
        unit: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._var_name = var_name
        self._attr_unique_id = f"{self._ups_name}_{suffix}"
        self._attr_name = suffix.replace("_", " ").title()
        self._attr_native_unit_of_measurement = UNIT_MAP.get(unit, unit)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("variables", {}).get(self._var_name)

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._var_name not in self.coordinator.data.get("variables", {}):
            self._attr_available = False
        else:
            self._attr_available = True
        super()._handle_coordinator_update()
