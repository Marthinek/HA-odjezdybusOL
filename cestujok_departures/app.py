#!/usr/bin/env python3
"""Poll CestujOK station departures and publish Home Assistant MQTT Discovery entities."""

import json
import logging
import os
import re
import signal
import time
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt
import requests

API_BASE = "https://www.cestujok.cz/idspublicservices/api"
LOG = logging.getLogger("cestujok")
RUNNING = True


def option(name: str, default: Any) -> Any:
    """Read add-on option from the Home Assistant add-on options file."""
    try:
        with open("/data/options.json", "r", encoding="utf-8") as handle:
            options = json.load(handle)
        return options.get(name, default)
    except (OSError, json.JSONDecodeError):
        return default


def stop_handler(_signum: int, _frame: Any) -> None:
    global RUNNING
    RUNNING = False


def clean_id(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    return value.strip("_") or "station"


class CestujOKPublisher:
    def __init__(self) -> None:
        raw_ids = str(option("station_ids", "S-13053,S-13064"))
        raw_names = str(option("station_names", "Jeseník, Lipovská|Jeseník, žel.st."))
        ids = [value.strip() for value in raw_ids.split(",") if value.strip()]
        names = [value.strip() for value in raw_names.split("|")]
        if not ids:
            ids = [str(option("station_id", "S-13053"))]
            names = [str(option("station_name", "Jeseník, Lipovská"))]
        self.stations = [
            {"id": station_id, "name": names[index] if index < len(names) and names[index] else station_id,
             "slug": clean_id(station_id)}
            for index, station_id in enumerate(ids)
        ]
        self.interval = int(option("update_interval", 60))
        self.count = int(option("departures_count", 6))
        self.mqtt_host = str(option("mqtt_host", "core-mosquitto"))
        self.mqtt_port = int(option("mqtt_port", 1883))
        self.mqtt_username = str(option("mqtt_username", ""))
        self.mqtt_password = str(option("mqtt_password", ""))
        self.discovery_prefix = str(option("mqtt_discovery_prefix", "homeassistant")).strip("/")
        self.topic_prefix = str(option("mqtt_topic_prefix", "cestujok")).strip("/")
        self.http = requests.Session()
        self.http.headers.update({
            "User-Agent": "HA-CestujOK-Departures/0.1.0",
            "Accept": "application/json",
        })
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="ha_cestujok_multi",
            clean_session=True,
        )
        if self.mqtt_username:
            self.client.username_pw_set(self.mqtt_username, self.mqtt_password or None)
        for station in self.stations:
            self.client.will_set(f"{self.topic_prefix}/{station['slug']}/availability", "offline", qos=1, retain=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.connected = False

    def on_connect(self, client, _userdata, _flags, reason_code, _properties) -> None:
        self.connected = reason_code == 0
        if self.connected:
            LOG.info("Connected to MQTT broker %s:%s", self.mqtt_host, self.mqtt_port)
            for station in self.stations:
                client.publish(f"{self.topic_prefix}/{station['slug']}/availability", "online", qos=1, retain=True)
                self.publish_discovery(station)

    def on_disconnect(self, _client, _userdata, _disconnect_flags, reason_code, _properties) -> None:
        self.connected = False
        if reason_code:
            LOG.warning("MQTT disconnected: %s", reason_code)

    def publish_discovery(self, station: dict[str, str]) -> None:
        station_slug = station["slug"]
        station_name = station["name"]
        state_topic = f"{self.topic_prefix}/{station_slug}/departures"
        availability_topic = f"{self.topic_prefix}/{station_slug}/availability"
        device = {
            "identifiers": [f"cestujok_{station_slug}"],
            "name": f"CestujOK – {station_name}",
            "manufacturer": "CestujOK / IDSOK (neoficiální klient)",
            "model": "Odjezdy ze zastávky",
        }
        for index in range(self.count):
            object_id = f"{station_slug}_departure_{index + 1}"
            config = {
                "name": f"{station_name} – odjezd {index + 1}",
                "unique_id": f"cestujok_{object_id}",
                "object_id": f"cestujok_{object_id}",
                "state_topic": state_topic,
                "value_template": f"{{{{ value_json.departures[{index}].time if value_json.departures|length > {index} else 'unknown' }}}}",
                "json_attributes_topic": state_topic,
                "json_attributes_template": f"{{{{ value_json.departures[{index}] | tojson if value_json.departures|length > {index} else '{{}}' }}}}",
                "availability_topic": availability_topic,
                "payload_available": "online",
                "payload_not_available": "offline",
                "icon": "mdi:bus-clock",
                "device": device,
            }
            topic = f"{self.discovery_prefix}/sensor/{object_id}/config"
            self.client.publish(topic, json.dumps(config, ensure_ascii=False), qos=1, retain=True)
        LOG.info("Published MQTT Discovery configuration for %s departure sensors", self.count)

    def get_departures(self, station: dict[str, str]) -> list[dict[str, Any]]:
        url = f"{API_BASE}/station/{station['id']}/nextservices"
        response = self.http.get(url, timeout=20)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("CestujOK returned an unexpected response (expected a list)")
        departures = []
        for item in payload[: self.count]:
            departures.append({
                "id": item.get("id"),
                "line": item.get("name"),
                "destination": item.get("dest"),
                "time": item.get("time"),
                "delay": item.get("delay"),
                "vehicle_type": item.get("vehicleType"),
                "line_type": item.get("lineType"),
                "is_detour": item.get("isDetour", False),
                "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            })
        return departures

    def publish(self, station: dict[str, str]) -> None:
        departures = self.get_departures(station)
        state_topic = f"{self.topic_prefix}/{station['slug']}/departures"
        availability_topic = f"{self.topic_prefix}/{station['slug']}/availability"
        payload = {
            "station_id": station["id"],
            "station_name": station["name"],
            "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "departures": departures,
        }
        self.client.publish(state_topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=True)
        self.client.publish(availability_topic, "online", qos=1, retain=True)
        if departures:
            first = departures[0]
            LOG.info("Published %d departures; next: %s at %s (delay: %s min)",
                     len(departures), first.get("destination"), first.get("time"), first.get("delay", "n/a"))
        else:
            LOG.info("CestujOK returned no upcoming departures")

    def run(self) -> None:
        LOG.info("Starting for %s stations (%s), refresh every %ss",
                 len(self.stations), ", ".join(station["name"] for station in self.stations), self.interval)
        self.client.reconnect_delay_set(min_delay=2, max_delay=60)
        self.client.connect_async(self.mqtt_host, self.mqtt_port, keepalive=60)
        self.client.loop_start()
        try:
            while RUNNING:
                if self.connected:
                    try:
                        for station in self.stations:
                            try:
                                self.publish(station)
                            except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
                                LOG.warning("Unable to fetch departures for %s (%s): %s", station["name"], station["id"], exc)
                            except Exception:
                                LOG.exception("Unexpected error while publishing departures for %s", station["name"])
                else:
                    LOG.debug("Waiting for MQTT connection")
                for _ in range(self.interval):
                    if not RUNNING:
                        break
                    time.sleep(1)
        finally:
            try:
                for station in self.stations:
                    self.client.publish(f"{self.topic_prefix}/{station['slug']}/availability", "offline", qos=1, retain=True)
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                LOG.exception("Error while shutting down MQTT client")
            self.http.close()


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)
    CestujOKPublisher().run()


if __name__ == "__main__":
    main()
