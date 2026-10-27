"""Config flow for CestujOK stops."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import CestujOKApi
from .const import DOMAIN


class CestujOKConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one CestujOK stop."""
    VERSION = 1

    def __init__(self) -> None:
        self._matches: list[dict] = []
        self._query = ""

    async def async_step_user(self, user_input=None):
        """Search for a stop."""
        errors = {}
        if user_input is not None:
            self._query = user_input["query"].strip()
            if len(self._query) < 2:
                errors["base"] = "query_too_short"
            else:
                api = CestujOKApi(async_get_clientsession(self.hass))
                try:
                    self._matches = await api.async_search_stops(self._query)
                except Exception:
                    errors["base"] = "cannot_connect"
                else:
                    if self._matches:
                        return await self.async_step_pick_stop()
                    errors["base"] = "no_stops"
        return self.async_show_form(step_id="user",
            data_schema=vol.Schema({vol.Required("query", default=self._query): str}),
            errors=errors)

    async def async_step_pick_stop(self, user_input=None):
        """Select a stop returned by search."""
        if user_input is not None:
            selected = self._matches[int(user_input["stop"])]
            await self.async_set_unique_id(selected["id"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=selected["name"],
                data={"stop_id": selected["id"], "stop_name": selected["name"]})
        choices = {str(i): f'{stop["name"]} (ID: {stop["id"]})'
                   for i, stop in enumerate(self._matches)}
        return self.async_show_form(step_id="pick_stop",
            data_schema=vol.Schema({vol.Required("stop"): vol.In(choices)}))
