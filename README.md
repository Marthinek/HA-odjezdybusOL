# CestujOK Bus Departures for Home Assistant

A standalone Home Assistant OS add-on that reads upcoming bus departures from the CestujOK / IDSOK portal and publishes them to Home Assistant using MQTT Discovery.

**Default stops:** Jeseník, Lipovská (`S-13053`) and Jeseník, žel.st. (`S-13064`).

**Language:** [Česká verze README](README.cs.md)

## Features

- Fetches upcoming departures every 60 seconds by default.
- Publishes MQTT Discovery sensors for individual departures (6 by default).
- Exposes departure time as the sensor state and additional information as attributes: destination, line/service label, delay, vehicle type, line type, and detour flag.
- Publishes MQTT availability and retains the latest state.
- Can be restarted or updated independently without restarting Home Assistant Core.

## Installation

1. In Home Assistant, open **Settings → Add-ons → Add-on Store**.
2. Open the menu in the upper-right corner and select **Repositories**.
3. Add this repository: https://github.com/Marthinek/HA-odjezdybusOL
4. Refresh the store and install **CestujOK – Odjezdy autobusů**.
5. Configure the MQTT broker. For the Mosquitto add-on, the host is usually `core-mosquitto` and the port is `1883`. Set the MQTT username and password to match your broker configuration.
6. Start the add-on. Sensors should appear automatically through MQTT Discovery.

## Configuration

- `station_ids`: comma-separated CestujOK stop IDs; defaults to `S-13053,S-13064`.
- `station_names`: stop names separated by `|`, in the same order as `station_ids`; defaults to `Jeseník, Lipovská|Jeseník, žel.st.`. Commas inside stop names are supported.
- `update_interval`: polling interval in seconds (30–600).
- `departures_count`: number of departure sensors (1–10).
- `mqtt_host`, `mqtt_port`, `mqtt_username`, `mqtt_password`: MQTT connection settings.
- `mqtt_discovery_prefix`: MQTT Discovery prefix, usually `homeassistant`.
- `mqtt_topic_prefix`: add-on topic prefix; defaults to `cestujok`.

To use one or more other stops, update `station_ids` and `station_names` in the add-on configuration. Keep both lists in the same order. For example, `station_ids: "S-13053,S-13064"` and `station_names: "Jeseník, Lipovská|Jeseník, žel.st."` configures both stops. Each stop gets its own MQTT topics, device, and departure sensors.

## Data source and limitations

The following CestujOK endpoints were identified from the website's network traffic:

- `GET https://www.cestujok.cz/idspublicservices/api/station` — list of stops.
- `GET https://www.cestujok.cz/idspublicservices/api/station/S-13053/nextservices` — upcoming departures for Jeseník, Lipovská.

This add-on uses an unofficial HTTP interface that may change without notice and is not guaranteed by the service operator. Delay information may not be available for every service. This project is not affiliated with CestujOK, IDSOK, or any transport operator.

## Previous HACS integration

The original experimental HACS integration remains in `custom_components/cestujok_departures`. For standalone updates, the add-on and MQTT Discovery are recommended.

Do not post cookies, authorization headers, tokens, or unredacted HAR files in public issues.
