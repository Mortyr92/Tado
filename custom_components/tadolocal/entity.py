"""Base entities for TadoLocal."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import TadoLocalCoordinator


def bridge_identifier(coordinator: TadoLocalCoordinator) -> tuple[str, str]:
    return (DOMAIN, f"bridge_{coordinator.config_entry.entry_id}")


def bridge_device_info(coordinator: TadoLocalCoordinator) -> DeviceInfo:
    status = coordinator.data.status if coordinator.data else {}
    return DeviceInfo(
        identifiers={bridge_identifier(coordinator)},
        name="TadoLocal Bridge",
        manufacturer=MANUFACTURER,
        model="TadoLocal",
        sw_version=status.get("version"),
        configuration_url=coordinator.api.base_url,
    )


class TadoLocalBridgeEntity(CoordinatorEntity[TadoLocalCoordinator]):
    """Entity attached to the TadoLocal bridge itself."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TadoLocalCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_bridge_{key}"
        self._attr_device_info = bridge_device_info(coordinator)


class TadoLocalZoneEntity(CoordinatorEntity[TadoLocalCoordinator]):
    """Entity representing a TadoLocal zone."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TadoLocalCoordinator, zone_id: int, key: str) -> None:
        super().__init__(coordinator)
        self.zone_id = zone_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_zone_{zone_id}_{key}"
        zone = self.zone
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"zone_{coordinator.config_entry.entry_id}_{zone_id}")},
            name=zone.get("name") or f"Zone {zone_id}",
            manufacturer=MANUFACTURER,
            model=zone.get("zone_type") or "Zone",
            via_device=bridge_identifier(coordinator),
        )

    @property
    def zone(self) -> dict[str, Any]:
        return self.coordinator.data.zones.get(self.zone_id, {})

    @property
    def zone_state(self) -> dict[str, Any]:
        return self.zone.get("state") or {}

    @property
    def available(self) -> bool:
        return super().available and self.zone_id in self.coordinator.data.zones


class TadoLocalDeviceEntity(CoordinatorEntity[TadoLocalCoordinator]):
    """Entity representing a physical Tado device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TadoLocalCoordinator, device_id: int, key: str) -> None:
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_device_{device_id}_{key}"
        device = self.device
        serial = device.get("serial_number")
        identifiers = {(DOMAIN, f"device_{coordinator.config_entry.entry_id}_{device_id}")}
        if serial:
            identifiers.add((DOMAIN, serial))
        self._attr_device_info = DeviceInfo(
            identifiers=identifiers,
            name=device.get("name") or serial or f"Device {device_id}",
            manufacturer=MANUFACTURER,
            model=device.get("model") or device.get("device_type"),
            serial_number=serial,
            sw_version=device.get("firmware_version"),
            suggested_area=device.get("zone_name"),
            via_device=bridge_identifier(coordinator),
        )

    @property
    def device(self) -> dict[str, Any]:
        return self.coordinator.data.devices.get(self.device_id, {})

    @property
    def device_state(self) -> dict[str, Any]:
        return self.device.get("state") or {}

    @property
    def available(self) -> bool:
        return super().available and self.device_id in self.coordinator.data.devices
