"""Diagnostics support."""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    """Return diagnostic data for this entry."""
    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    return {"stop_name": entry.data.get("stop_name"),
            "stop_id": entry.data.get("stop_id"),
            "data": coordinator.data if coordinator else None}
