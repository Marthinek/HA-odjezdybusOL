"""Client for the observed CestujOK web API.

This API is reverse-engineered from browser traffic and may change.
"""
from __future__ import annotations
from typing import Any
from urllib.parse import quote
import aiohttp
from .const import BASE_URL


class CestujOKApi:
    """Async API client."""
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _get_json(self, url: str) -> Any:
        async with self._session.get(
            url,
            headers={"Accept": "application/json, text/plain, */*",
                     "Referer": "https://www.cestujok.cz/",
                     "User-Agent": "Home Assistant CestujOK integration"},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as response:
            response.raise_for_status()
            return await response.json(content_type=None)

    async def async_search_stops(self, query: str) -> list[dict[str, Any]]:
        """Try possible stop-search endpoints.

        Search route is not yet confirmed from captured browser traffic. This is
        intentionally best-effort and should be replaced by the actual route.
        """
        encoded = quote(query.strip())
        candidates = [
            f"{BASE_URL}/station/search?query={encoded}",
            f"{BASE_URL}/station/search/{encoded}",
            f"{BASE_URL}/station?search={encoded}",
        ]
        for url in candidates:
            try:
                payload = await self._get_json(url)
            except (aiohttp.ClientError, ValueError):
                continue
            stops = self._normalise_stop_results(payload)
            if stops:
                return stops
        return []

    @staticmethod
    def _normalise_stop_results(payload: Any) -> list[dict[str, Any]]:
        """Extract station-like records from common JSON response shapes."""
        if isinstance(payload, dict):
            for key in ("stations", "stops", "items", "results", "data", "content"):
                if key in payload:
                    found = CestujOKApi._normalise_stop_results(payload[key])
                    if found:
                        return found
            payload = [payload]
        if not isinstance(payload, list):
            return []
        found = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            stop_id = (item.get("id") or item.get("stationId") or item.get("code")
                       or item.get("station_id"))
            name = item.get("name") or item.get("stationName") or item.get("label") or item.get("title")
            if stop_id and name:
                found.append({"id": str(stop_id), "name": str(name), "raw": item})
        return found

    async def async_get_departures(self, stop_id: str, stop_name: str) -> dict[str, Any]:
        """Fetch departures and best-effort live delay data."""
        payload = await self._get_json(f"{BASE_URL}/station/{quote(stop_id, safe='')}/nextservices")
        try:
            positions_payload = await self._get_json(f"{BASE_URL}/service/position")
        except (aiohttp.ClientError, ValueError):
            positions_payload = None
        departures = self._normalise_departures(payload)
        positions = self._normalise_positions(positions_payload)
        by_service = {p["service_id"]: p for p in positions if p.get("service_id")}
        for departure in departures:
            live = by_service.get(departure.get("service_id"))
            if live:
                departure["delay_minutes"] = live.get("delay_minutes")
                departure["vehicle_position"] = live.get("vehicle_position")
        return {"stop_id": stop_id, "stop_name": stop_name, "departures": departures}

    @staticmethod
    def _normalise_departures(payload: Any) -> list[dict[str, Any]]:
        """Normalise common departure JSON shapes."""
        if isinstance(payload, dict):
            for key in ("services", "departures", "items", "results", "data", "content"):
                if key in payload:
                    found = CestujOKApi._normalise_departures(payload[key])
                    if found:
                        return found
            payload = [payload]
        if not isinstance(payload, list):
            return []
        result = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            line = row.get("line") or row.get("lineNumber") or row.get("number") or row.get("line_name")
            destination = row.get("destination") or row.get("direction") or row.get("to") or row.get("targetName") or ""
            time = row.get("departureTime") or row.get("time") or row.get("departure") or row.get("plannedTime") or ""
            service_id = row.get("serviceId") or row.get("service_id") or row.get("id")
            result.append({"line": str(line) if line is not None else "—",
                           "destination": str(destination), "time": str(time),
                           "service_id": str(service_id) if service_id is not None else None,
                           "delay_minutes": None, "vehicle_position": None})
        return result

    @staticmethod
    def _normalise_positions(payload: Any) -> list[dict[str, Any]]:
        """Normalise common vehicle-position JSON shapes."""
        if isinstance(payload, dict):
            for key in ("positions", "vehicles", "services", "items", "data", "content"):
                if key in payload:
                    found = CestujOKApi._normalise_positions(payload[key])
                    if found:
                        return found
            payload = [payload]
        if not isinstance(payload, list):
            return []
        result = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            service_id = row.get("serviceId") or row.get("service_id") or row.get("id")
            delay = row.get("delayMinutes")
            if delay is None:
                delay = row.get("delay") if row.get("delay") is not None else row.get("delay_minutes")
            try:
                delay = int(delay) if delay is not None else None
            except (TypeError, ValueError):
                delay = None
            result.append({"service_id": str(service_id) if service_id is not None else None,
                           "delay_minutes": delay,
                           "vehicle_position": row.get("position") or row.get("coordinates")})
        return result
