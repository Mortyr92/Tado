"""The TadoLocal integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TadoLocalApi
from .const import CONF_API_KEY, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, PLATFORMS
from .coordinator import TadoLocalCoordinator

type TadoLocalConfigEntry = ConfigEntry[TadoLocalCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TadoLocalConfigEntry) -> bool:
    """Set up TadoLocal from a config entry."""
    api = TadoLocalApi(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data.get(CONF_API_KEY),
    )
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    coordinator = TadoLocalCoordinator(hass, entry, api, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: TadoLocalConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: TadoLocalConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
