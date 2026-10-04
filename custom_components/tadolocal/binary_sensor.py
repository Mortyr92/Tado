"""Binary sensor platform for TadoLocal."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TadoLocalConfigEntry
from .const import HEATING_COOLING, HEATING_HEATING
from .coordinator import TadoLocalCoordinator
from .entity import TadoLocalBridgeEntity, TadoLocalDeviceEntity, TadoLocalZoneEntity


@dataclass(frozen=True, kw_only=True)
class TadoLocalBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a TadoLocal binary sensor."""

    is_on_fn: Callable[[dict[str, Any]], bool | None]
    exists_fn: Callable[[dict[str, Any]], bool] = lambda _: True


def _state(key: str) -> Callable[[dict[str, Any]], Any]:
    return lambda obj: (obj.get("state") or {}).get(key)


def _has_state(key: str) -> Callable[[dict[str, Any]], bool]:
    return lambda obj: (obj.get("state") or {}).get(key) is not None


def _is_heating(obj: dict[str, Any]) -> bool | None:
    cur = (obj.get("state") or {}).get("cur_heating")
    if cur is None:
        return None
    return cur in (HEATING_HEATING, HEATING_COOLING)


ZONE_BINARY_SENSORS: tuple[TadoLocalBinarySensorDescription, ...] = (
    TadoLocalBinarySensorDescription(
        key="heating",
        translation_key="heating",
        device_class=BinarySensorDeviceClass.HEAT,
        is_on_fn=_is_heating,
    ),
    TadoLocalBinarySensorDescription(
        key="window_open",
        translation_key="window_open",
        device_class=BinarySensorDeviceClass.WINDOW,
        is_on_fn=_state("window_open"),
        exists_fn=_has_state("window_open"),
    ),
)

DEVICE_BINARY_SENSORS: tuple[TadoLocalBinarySensorDescription, ...] = (
    TadoLocalBinarySensorDescription(
        key="heating",
        translation_key="heating",
        device_class=BinarySensorDeviceClass.HEAT,
        is_on_fn=_is_heating,
        exists_fn=_has_state("cur_heating"),
    ),
    TadoLocalBinarySensorDescription(
        key="battery_low",
        translation_key="battery_low",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_state("battery_low"),
    ),
    TadoLocalBinarySensorDescription(
        key="zone_leader",
        translation_key="zone_leader",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:crown",
        is_on_fn=lambda d: bool(d.get("is_zone_leader")),
    ),
)

BRIDGE_BINARY_SENSORS: tuple[TadoLocalBinarySensorDescription, ...] = (
    TadoLocalBinarySensorDescription(
        key="bridge_connected",
        translation_key="bridge_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda s: bool(s.get("bridge_connected")),
    ),
    TadoLocalBinarySensorDescription(
        key="cloud_authenticated",
        translation_key="cloud_authenticated",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda s: bool((s.get("cloud_api") or {}).get("authenticated")),
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
        new: list[BinarySensorEntity] = []
        for zone_id, zone in coordinator.data.zones.items():
            for desc in ZONE_BINARY_SENSORS:
                uid = f"zone_{zone_id}_{desc.key}"
                if uid not in known and desc.exists_fn(zone):
                    known.add(uid)
                    new.append(TadoLocalZoneBinarySensor(coordinator, zone_id, desc))
        for device_id, device in coordinator.data.devices.items():
            for desc in DEVICE_BINARY_SENSORS:
                uid = f"device_{device_id}_{desc.key}"
                if uid not in known and desc.exists_fn(device):
                    known.add(uid)
                    new.append(
                        TadoLocalDeviceBinarySensor(coordinator, device_id, desc)
                    )
        for desc in BRIDGE_BINARY_SENSORS:
            uid = f"bridge_{desc.key}"
            if uid not in known:
                known.add(uid)
                new.append(TadoLocalBridgeBinarySensor(coordinator, desc))
        if new:
            async_add_entities(new)

    _add_new()
    entry.async_on_unload(coordinator.async_add_listener(_add_new))


class TadoLocalZoneBinarySensor(TadoLocalZoneEntity, BinarySensorEntity):
    entity_description: TadoLocalBinarySensorDescription

    def __init__(
        self,
        coordinator: TadoLocalCoordinator,
        zone_id: int,
        description: TadoLocalBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, zone_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on_fn(self.zone)


class TadoLocalDeviceBinarySensor(TadoLocalDeviceEntity, BinarySensorEntity):
    entity_description: TadoLocalBinarySensorDescription

    def __init__(
        self,
        coordinator: TadoLocalCoordinator,
        device_id: int,
        description: TadoLocalBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on_fn(self.device)


class TadoLocalBridgeBinarySensor(TadoLocalBridgeEntity, BinarySensorEntity):
    entity_description: TadoLocalBinarySensorDescription

    def __init__(
        self,
        coordinator: TadoLocalCoordinator,
        description: TadoLocalBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on_fn(self.coordinator.data.status)
