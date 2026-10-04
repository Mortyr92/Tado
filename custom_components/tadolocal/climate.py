"""Climate platform for TadoLocal zones."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_TENTHS, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TadoLocalConfigEntry
from .api import TadoLocalError
from .const import (
    HEATING_COOLING,
    HEATING_HEATING,
    MAX_TEMP,
    MIN_TEMP,
    MODE_AUTO,
    MODE_COOL,
    MODE_HEAT,
    MODE_OFF,
    TEMP_STEP,
)
from .coordinator import TadoLocalCoordinator
from .entity import TadoLocalZoneEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TadoLocalConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    known: set[int] = set()

    def _add_new_zones() -> None:
        new = [
            TadoLocalZoneClimate(coordinator, zone_id)
            for zone_id in coordinator.data.zones
            if zone_id not in known
        ]
        known.update(e.zone_id for e in new)
        if new:
            async_add_entities(new)

    _add_new_zones()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_zones))


class TadoLocalZoneClimate(TadoLocalZoneEntity, ClimateEntity):
    """Climate entity controlling a TadoLocal zone via its leader device."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = PRECISION_TENTHS
    _attr_target_temperature_step = TEMP_STEP
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: TadoLocalCoordinator, zone_id: int) -> None:
        super().__init__(coordinator, zone_id, "climate")

    @property
    def current_temperature(self) -> float | None:
        return self.zone_state.get("cur_temp_c")

    @property
    def current_humidity(self) -> float | None:
        return self.zone_state.get("hum_perc")

    @property
    def target_temperature(self) -> float | None:
        return self.zone_state.get("target_temp_c")

    @property
    def hvac_mode(self) -> HVACMode:
        mode = self.zone_state.get("mode", MODE_OFF)
        if mode in (MODE_HEAT, MODE_AUTO):
            return HVACMode.HEAT
        if mode == MODE_COOL:
            return HVACMode.COOL
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        cur = self.zone_state.get("cur_heating")
        if cur == HEATING_HEATING:
            return HVACAction.HEATING
        if cur == HEATING_COOLING:
            return HVACAction.COOLING
        return HVACAction.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        zone = self.zone
        return {
            "zone_id": self.zone_id,
            "zone_type": zone.get("zone_type"),
            "leader_serial": zone.get("leader_serial"),
            "leader_type": zone.get("leader_type"),
            "device_count": zone.get("device_count"),
            "window_open": self.zone_state.get("window_open"),
            "is_circuit_driver": zone.get("is_circuit_driver"),
        }

    async def _call(self, **kwargs: Any) -> None:
        try:
            await self.coordinator.api.set_zone(self.zone_id, **kwargs)
        except TadoLocalError as err:
            raise HomeAssistantError(
                f"Failed to control zone {self.zone_id}: {err}"
            ) from err
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self._call(temperature=float(temperature), heating_enabled=True)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._call(heating_enabled=False)
        else:
            # -1 keeps the stored setpoint while switching heating on
            await self._call(temperature=-1, heating_enabled=True)

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)
