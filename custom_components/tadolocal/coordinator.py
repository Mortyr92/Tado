"""Data update coordinator for TadoLocal."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TadoLocalApi, TadoLocalAuthError, TadoLocalError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class TadoLocalData:
    """Snapshot of the TadoLocal bridge state."""

    status: dict[str, Any] = field(default_factory=dict)
    zones: dict[int, dict[str, Any]] = field(default_factory=dict)
    devices: dict[int, dict[str, Any]] = field(default_factory=dict)


class TadoLocalCoordinator(DataUpdateCoordinator[TadoLocalData]):
    """Polls zones, devices and status from the TadoLocal bridge."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: TadoLocalApi,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({api.base_url})",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.config_entry = entry
        self.api = api

    async def _async_update_data(self) -> TadoLocalData:
        try:
            status, zones, devices = await asyncio.gather(
                self.api.get_status(),
                self.api.get_zones(),
                self.api.get_devices(),
            )
        except TadoLocalAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except TadoLocalError as err:
            raise UpdateFailed(str(err)) from err

        return TadoLocalData(
            status=status or {},
            zones={z["zone_id"]: z for z in zones if "zone_id" in z},
            devices={d["device_id"]: d for d in devices if "device_id" in d},
        )
