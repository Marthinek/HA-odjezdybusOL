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
        self.station_id = str(option("station_id", "S-13053"))
        self.station_name = str(option("station_name", "Jeseník, Lipovská"))
        self.interval = int(option("update_interval", 60))
        self.count = int(option("departures_count", 6))
        self.mqtt_host = str(option("mqtt_host", "core-mosquitto"))
        self.mqtt_port = int(option("mqtt_port", 1883))
        self.mqtt_username = str(option("mqtt_username", ""))
        self.mqtt_password = str(option("mqtt_password", ""))
        self.discovery_prefix = str(option("mqtt_discovery_prefix", "homeassistant")).strip("/")
        self.topic_prefix = str(option("mqtt_topic_prefix", "cestujok")).strip("/")
        self.station_slug = clean_id(self.station_id)
        self.state_topic = f"{self.topic_prefix}/{self.station_slug}/departures"
        self.availability_topic = f"{self.topic_prefix}/{self.station_slug}/availability"
        self.http = requests.Session()
        self.http.headers.update({
            "User-Agent": "HA-CestujOK-Departures/0.1.0",
            "Accept": "application/json",
        })
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"ha_cestujok_{self.station_slug}",
            clean_session=True,
        )
        if self.mqtt_username:
            self.client.username_pw_set(self.mqtt_username, self.mqtt_password or None)
        self.client.will_set(self.availability_topic, "offline", qos=1, retain=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.connected = False

    def on_connect(self, client, _userdata, _flags, reason_code, _properties) -> None:
        self.connected = reason_code == 0
        if self.connected:
            LOG.info("Connected to MQTT broker %s:%s", self.mqtt_host, self.mqtt_port)
            client.publish(self.availability_topic, "online", qos=1, retain=True)
            self.publish_discovery()

    def on_disconnect(self, _client, _userdata, _disconnect_flags, reason_code, _properties) -> None:
        self.connected = False
        if reason_code:
            LOG.warning("MQTT disconnected: %s", reason_code)

    def publish_discovery(self) -> None:
        device = {
            "identifiers": [f"cestujok_{self.station_slug}"],
            "name": f"CestujOK – {self.station_name}",
            "manufacturer": "CestujOK / IDSOK (neoficiální klient)",
            "model": "Odjezdy ze zastávky",
        }
        for index in range(self.count):
            object_id = f"{self.station_slug}_departure_{index + 1}"
            config = {
                "name": f"{self.station_name} – odjezd {index + 1}",
                "unique_id": f"cestujok_{object_id}",
                "object_id": f"cestujok_{object_id}",
                "state_topic": self.state_topic,
                "value_template": f"{{{{ value_json.departures[{index}].time if value_json.departures|length > {index} else 'unknown' }}}}",
                "json_attributes_topic": self.state_topic,
                "json_attributes_template": f"{{{{ value_json.departures[{index}] | tojson if value_json.departures|length > {index} else '{{}}' }}}}",
                "availability_topic": self.availability_topic,
                "payload_available": "online",
                "payload_not_available": "offline",
                "icon": "mdi:bus-clock",
                "device": device,
            }
            topic = f"{self.discovery_prefix}/sensor/{object_id}/config"
            self.client.publish(topic, json.dumps(config, ensure_ascii=False), qos=1, retain=True)
        LOG.info("Published MQTT Discovery configuration for %s departure sensors", self.count)

    def get_departures(self) -> list[dict[str, Any]]:
        url = f"{API_BASE}/station/{self.station_id}/nextservices"
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

    def publish(self) -> None:
        departures = self.get_departures()
        payload = {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "departures": departures,
        }
        self.client.publish(self.state_topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=True)
        self.client.publish(self.availability_topic, "online", qos=1, retain=True)
        if departures:
            first = departures[0]
            LOG.info("Published %d departures; next: %s at %s (delay: %s min)",
                     len(departures), first.get("destination"), first.get("time"), first.get("delay", "n/a"))
        else:
            LOG.info("CestujOK returned no upcoming departures")

    def run(self) -> None:
        LOG.info("Starting for station %s (%s), refresh every %ss", self.station_name, self.station_id, self.interval)
        self.client.reconnect_delay_set(min_delay=2, max_delay=60)
        self.client.connect_async(self.mqtt_host, self.mqtt_port, keepalive=60)
        self.client.loop_start()
        try:
            while RUNNING:
                if self.connected:
                    try:
                        self.publish()
                    except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
                        LOG.warning("Unable to fetch departures: %s", exc)
                    except Exception:
                        LOG.exception("Unexpected error while publishing departures")
                else:
                    LOG.debug("Waiting for MQTT connection")
                for _ in range(self.interval):
                    if not RUNNING:
                        break
                    time.sleep(1)
        finally:
            try:
                self.client.publish(self.availability_topic, "offline", qos=1, retain=True)
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
