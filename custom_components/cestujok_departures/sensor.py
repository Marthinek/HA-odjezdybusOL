"""Departure sensor."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_STOP_NAME


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    """Create a sensor for the configured stop."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CestujOKDepartureSensor(coordinator, entry)])


class CestujOKDepartureSensor(CoordinatorEntity, SensorEntity):
    """Sensor with upcoming departures in attributes."""
    _attr_icon = "mdi:bus-clock"
    _attr_should_poll = False

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.data[CONF_STOP_NAME]} – odjezdy"
        self._attr_unique_id = f"{entry.data['stop_id']}_departures"

    @property
    def native_value(self):
        """Return number of upcoming departures."""
        return len((self.coordinator.data or {}).get("departures", []))

    @property
    def extra_state_attributes(self):
        """Expose departure list and stop metadata."""
        return self.coordinator.data or {}
