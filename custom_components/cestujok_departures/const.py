"""Constants for the CestujOK departures integration."""
DOMAIN = "cestujok_departures"
PLATFORMS = ["sensor"]
CONF_STOP_ID = "stop_id"
CONF_STOP_NAME = "stop_name"
UPDATE_INTERVAL_SECONDS = 60
# Observed in browser traffic; not an officially documented API.
BASE_URL = "https://www.cestujok.cz/idspublicservices/api"
