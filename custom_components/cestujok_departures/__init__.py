"""CestujOK bus departure integration."""
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CestujOKApi
from .const import DOMAIN, PLATFORMS, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured stop."""
    api = CestujOKApi(async_get_clientsession(hass))

    async def async_update_data():
        try:
            return await api.async_get_departures(entry.data["stop_id"], entry.data["stop_name"])
        except Exception as err:
            raise UpdateFailed(f"Chyba při načítání CestujOK: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=f"CestujOK {entry.data['stop_name']}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a configured stop."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
