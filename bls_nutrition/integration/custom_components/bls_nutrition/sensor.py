"""Sensor platform for BLS Nährwertdatenbank."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfMass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ENTITY_BE,
    ENTITY_BLS_VERSION,
    ENTITY_CARBS,
    ENTITY_ECOSCORE,
    ENTITY_ENERGY,
    ENTITY_FAT,
    ENTITY_FAVORITES_COUNT,
    ENTITY_FOOD_COUNT,
    ENTITY_FPE,
    ENTITY_G_KH,
    ENTITY_KE,
    ENTITY_LAST_FOOD,
    ENTITY_NOVA,
    ENTITY_NUTRISCORE,
    ENTITY_PROTEIN,
    ENTITY_SEARCH_HITS,
    SIGNAL_RESULT_UPDATED,
)
from .data import BlsRuntimeData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: BlsRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BlsFoodCountSensor(runtime, entry),
            BlsFavoritesCountSensor(runtime, entry),
            BlsVersionSensor(runtime, entry),
            BlsLastFoodSensor(runtime, entry),
            BlsSearchHitsSensor(runtime, entry),
            BlsDiabetesSensor(runtime, entry, ENTITY_G_KH, "g_kh", UnitOfMass.GRAMS),
            BlsDiabetesSensor(runtime, entry, ENTITY_BE, "be", None),
            BlsDiabetesSensor(runtime, entry, ENTITY_KE, "ke", None),
            BlsDiabetesSensor(runtime, entry, ENTITY_FPE, "fpe", None),
            BlsNutrientSensor(runtime, entry, ENTITY_ENERGY, "energy_kcal", UnitOfEnergy.KILO_CALORIE),
            BlsNutrientSensor(runtime, entry, ENTITY_PROTEIN, "protein", UnitOfMass.GRAMS),
            BlsNutrientSensor(runtime, entry, ENTITY_FAT, "fat", UnitOfMass.GRAMS),
            BlsNutrientSensor(runtime, entry, ENTITY_CARBS, "carbs", UnitOfMass.GRAMS),
            BlsNutriscoreSensor(runtime, entry),
            BlsNovaSensor(runtime, entry),
            BlsEcoscoreSensor(runtime, entry),
        ]
    )


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="BLS Nährwertdatenbank",
        manufacturer="henryhst",
        model="BLS 4.0",
    )


class BlsSensorBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, runtime: BlsRuntimeData, entry: ConfigEntry) -> None:
        super().__init__(runtime.coordinator)
        self._runtime = runtime
        self._entry = entry
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RESULT_UPDATED, self._handle_result_updated
            )
        )

    @callback
    def _handle_result_updated(self, entry_id: str) -> None:
        if entry_id == self._entry.entry_id:
            self.async_write_ha_state()

    def _diabetes(self) -> dict[str, Any]:
        calc = self._runtime.last_calculation
        if not calc:
            return {}
        if "diabetes" in calc:
            return calc.get("diabetes") or {}
        if "diabetes_per_serving" in calc:
            return calc.get("diabetes_per_serving") or {}
        return {}

    def _nutrients(self) -> dict[str, Any]:
        calc = self._runtime.last_calculation
        if not calc:
            return {}
        if "nutrients_per_serving" in calc:
            return calc.get("nutrients_per_serving") or {}
        return calc.get("nutrients") or {}


class BlsFoodCountSensor(BlsSensorBase):
    _attr_translation_key = "food_count"
    _attr_icon = "mdi:food-apple"
    _attr_native_unit_of_measurement = "Lebensmittel"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{ENTITY_FOOD_COUNT}"

    @property
    def suggested_object_id(self) -> str:
        return ENTITY_FOOD_COUNT

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("food_count")


class BlsFavoritesCountSensor(BlsSensorBase):
    _attr_translation_key = "favorites_count"
    _attr_icon = "mdi:heart"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{ENTITY_FAVORITES_COUNT}"

    @property
    def suggested_object_id(self) -> str:
        return ENTITY_FAVORITES_COUNT

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("favorites_count")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "last_io": self._runtime.last_favorites_io or None,
        }


class BlsVersionSensor(BlsSensorBase):
    _attr_translation_key = "bls_version"
    _attr_icon = "mdi:database"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{ENTITY_BLS_VERSION}"

    @property
    def suggested_object_id(self) -> str:
        return ENTITY_BLS_VERSION

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("bls_version")


class BlsLastFoodSensor(BlsSensorBase):
    _attr_translation_key = "last_food"
    _attr_icon = "mdi:food"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{ENTITY_LAST_FOOD}"

    @property
    def suggested_object_id(self) -> str:
        return ENTITY_LAST_FOOD

    @property
    def native_value(self) -> str | None:
        calc = self._runtime.last_calculation
        if not calc:
            return None
        if calc.get("name"):
            return str(calc["name"])
        ingredients = calc.get("ingredients") or []
        if ingredients:
            names = [i.get("name") or i.get("id") for i in ingredients if i.get("name") or i.get("id")]
            if names:
                return ", ".join(names[:3])
        return self._runtime.last_search_query or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "calculation_type": self._runtime.last_calculation_type or None,
        }
        calc = self._runtime.last_calculation
        if calc and calc.get("source") == "off":
            if calc.get("nutriscore"):
                attrs["nutriscore"] = str(calc["nutriscore"]).upper()
            if calc.get("nova_group") is not None:
                attrs["nova_group"] = calc["nova_group"]
            if calc.get("ecoscore"):
                attrs["ecoscore"] = str(calc["ecoscore"]).upper()
        if self._runtime.last_search:
            attrs["search_results"] = self._runtime.last_search[:10]
        return attrs


class BlsSearchHitsSensor(BlsSensorBase):
    _attr_translation_key = "search_hits"
    _attr_icon = "mdi:magnify"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{ENTITY_SEARCH_HITS}"

    @property
    def suggested_object_id(self) -> str:
        return ENTITY_SEARCH_HITS

    @property
    def native_value(self) -> int | None:
        if not self._runtime.last_search:
            return None
        return len(self._runtime.last_search)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "query": self._runtime.last_search_query or None,
            "results": self._runtime.last_search[:10],
        }


class BlsDiabetesSensor(BlsSensorBase):
    def __init__(
        self,
        runtime: BlsRuntimeData,
        entry: ConfigEntry,
        object_id: str,
        translation_key: str,
        unit: str | None,
    ) -> None:
        super().__init__(runtime, entry)
        self._object_id = object_id
        self._diabetes_key = translation_key
        self._attr_translation_key = translation_key
        self._attr_icon = "mdi:diabetes"
        if unit:
            self._attr_native_unit_of_measurement = unit
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._object_id}"

    @property
    def suggested_object_id(self) -> str:
        return self._object_id

    @property
    def native_value(self) -> float | None:
        value = self._diabetes().get(self._diabetes_key)
        return float(value) if value is not None else None


class BlsNutrientSensor(BlsSensorBase):
    _ICONS = {
        "energy_kcal": "mdi:fire",
        "protein": "mdi:food-steak",
        "fat": "mdi:oil",
        "carbs": "mdi:bread-slice",
    }

    def __init__(
        self,
        runtime: BlsRuntimeData,
        entry: ConfigEntry,
        object_id: str,
        translation_key: str,
        unit: str,
    ) -> None:
        super().__init__(runtime, entry)
        self._object_id = object_id
        self._nutrient_key = {
            "energy_kcal": "ENERCC",
            "protein": "PROT625",
            "fat": "FAT",
            "carbs": "CHO",
        }[translation_key]
        self._attr_translation_key = translation_key
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = self._ICONS.get(translation_key, "mdi:chart-line")

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._object_id}"

    @property
    def suggested_object_id(self) -> str:
        return self._object_id

    @property
    def native_value(self) -> float | None:
        value = self._nutrients().get(self._nutrient_key)
        return float(value) if value is not None else None


class BlsOffScoreSensorBase(BlsSensorBase):
    _attr_state_class = None

    def _off_calculation(self) -> dict[str, Any] | None:
        calc = self._runtime.last_calculation
        if not calc or calc.get("source") != "off":
            return None
        return calc


class BlsNutriscoreSensor(BlsOffScoreSensorBase):
    _attr_translation_key = "nutriscore"
    _attr_icon = "mdi:food-apple-outline"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{ENTITY_NUTRISCORE}"

    @property
    def suggested_object_id(self) -> str:
        return ENTITY_NUTRISCORE

    @property
    def native_value(self) -> str | None:
        calc = self._off_calculation()
        if not calc:
            return None
        grade = calc.get("nutriscore")
        return str(grade).upper() if grade else None


class BlsNovaSensor(BlsOffScoreSensorBase):
    _attr_translation_key = "nova"
    _attr_icon = "mdi:food-variant"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{ENTITY_NOVA}"

    @property
    def suggested_object_id(self) -> str:
        return ENTITY_NOVA

    @property
    def native_value(self) -> int | None:
        calc = self._off_calculation()
        if not calc:
            return None
        value = calc.get("nova_group")
        return int(value) if value is not None else None


class BlsEcoscoreSensor(BlsOffScoreSensorBase):
    _attr_translation_key = "ecoscore"
    _attr_icon = "mdi:leaf"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{ENTITY_ECOSCORE}"

    @property
    def suggested_object_id(self) -> str:
        return ENTITY_ECOSCORE

    @property
    def native_value(self) -> str | None:
        calc = self._off_calculation()
        if not calc:
            return None
        grade = calc.get("ecoscore")
        return str(grade).upper() if grade else None
