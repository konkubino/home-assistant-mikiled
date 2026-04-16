"""Constants for the MiKiLED integration."""

from datetime import timedelta

DOMAIN = "mikiled"

DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

API_STATUS = "/api/status"
API_VERSION = "/api/version"
API_SENSORS = "/api/sensors"
SET_DAY_COLOR = "/setDayColor"
SET_NIGHT_COLOR = "/setNightColor"
