"""Sensor platform for TadoLocal."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TadoLocalConfigEntry
from .const import MODE_AUTO, MODE_COOL, MODE_HEAT, MODE_OFF
from .coordinator import TadoLocalCoordinator
from .entity import TadoLocalBridgeEntity, TadoLocalDeviceEntity, TadoLocalZoneEntity

MODE_NAMES = {MODE_OFF: "off", MODE_HEAT: "heat", MODE_COOL: "cool", MODE_AUTO: "auto"}


@dataclass(frozen=True, kw_only=True)
class TadoLocalSensorDescription(SensorEntityDescription):
    """Describes a TadoLocal sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    exists_fn: Callable[[dict[str, Any]], bool] = lambda _: True


def _state(key: str) -> Callable[[dict[str, Any]], Any]:
    return lambda obj: (obj.get("state") or {}).get(key)


def _has_state(key: str) -> Callable[[dict[str, Any]], bool]:
    return lambda obj: (obj.get("state") or {}).get(key) is not None


def _mode_name(obj: dict[str, Any]) -> str | None:
    mode = (obj.get("state") or {}).get("mode")
    return MODE_NAMES.get(mode) if mode is not None else None


ZONE_SENSORS: tuple[TadoLocalSensorDescription, ...] = (
    TadoLocalSensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_state("cur_temp_c"),
    ),
    TadoLocalSensorDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=_state("hum_perc"),
        exists_fn=_has_state("hum_perc"),
    ),
    TadoLocalSensorDescription(
        key="target_temperature",
        translation_key="target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_state("target_temp_c"),
    ),
    TadoLocalSensorDescription(
        key="mode",
        translation_key="mode",
        device_class=SensorDeviceClass.ENUM,
        options=list(MODE_NAMES.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_mode_name,
    ),
)

DEVICE_SENSORS: tuple[TadoLocalSensorDescription, ...] = (
    TadoLocalSensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_state("cur_temp_c"),
        exists_fn=_has_state("cur_temp_c"),
    ),
    TadoLocalSensorDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=_state("hum_perc"),
        exists_fn=_has_state("hum_perc"),
    ),
    TadoLocalSensorDescription(
        key="target_temperature",
        translation_key="target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_state("target_temp_c"),
        exists_fn=_has_state("target_temp_c"),
    ),
    TadoLocalSensorDescription(
        key="valve_position",
        translation_key="valve_position",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:valve",
        value_fn=_state("valve_position"),
        exists_fn=_has_state("valve_position"),
    ),
    TadoLocalSensorDescription(
        key="mode",
        translation_key="mode",
        device_class=SensorDeviceClass.ENUM,
        options=list(MODE_NAMES.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_mode_name,
    ),
)

BRIDGE_SENSORS: tuple[TadoLocalSensorDescription, ...] = (
    TadoLocalSensorDescription(
        key="tracked_devices",
        translation_key="tracked_devices",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermostat",
        value_fn=lambda s: s.get("tracked_devices"),
    ),
    TadoLocalSensorDescription(
        key="events_received",
        translation_key="events_received",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:counter",
        value_fn=lambda s: s.get("events_received"),
    ),
    TadoLocalSensorDescription(
        key="version",
        translation_key="version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:information-outline",
        value_fn=lambda s: s.get("version"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TadoLocalConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    known: set[str] = set()

    def _add_new() -> None:
        new: list[SensorEntity] = []
        for zone_id, zone in coordinator.data.zones.items():
            for desc in ZONE_SENSORS:
                uid = f"zone_{zone_id}_{desc.key}"
                if uid not in known and desc.exists_fn(zone):
                    known.add(uid)
                    new.append(TadoLocalZoneSensor(coordinator, zone_id, desc))
        for device_id, device in coordinator.data.devices.items():
            for desc in DEVICE_SENSORS:
                uid = f"device_{device_id}_{desc.key}"
                if uid not in known and desc.exists_fn(device):
                    known.add(uid)
                    new.append(TadoLocalDeviceSensor(coordinator, device_id, desc))
        for desc in BRIDGE_SENSORS:
            uid = f"bridge_{desc.key}"
            if uid not in known:
                known.add(uid)
                new.append(TadoLocalBridgeSensor(coordinator, desc))
        if new:
            async_add_entities(new)

    _add_new()
    entry.async_on_unload(coordinator.async_add_listener(_add_new))


class TadoLocalZoneSensor(TadoLocalZoneEntity, SensorEntity):
    entity_description: TadoLocalSensorDescription

    def __init__(
        self,
        coordinator: TadoLocalCoordinator,
        zone_id: int,
        description: TadoLocalSensorDescription,
    ) -> None:
        super().__init__(coordinator, zone_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.zone)


class TadoLocalDeviceSensor(TadoLocalDeviceEntity, SensorEntity):
    entity_description: TadoLocalSensorDescription

    def __init__(
        self,
        coordinator: TadoLocalCoordinator,
        device_id: int,
        description: TadoLocalSensorDescription,
    ) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.device)


class TadoLocalBridgeSensor(TadoLocalBridgeEntity, SensorEntity):
    entity_description: TadoLocalSensorDescription

    def __init__(
        self,
        coordinator: TadoLocalCoordinator,
        description: TadoLocalSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data.status)
