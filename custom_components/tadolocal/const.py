"""Constants for the TadoLocal integration."""

from homeassistant.const import Platform

DOMAIN = "tadolocal"

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 4407
DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 5

MIN_TEMP = 5.0
MAX_TEMP = 30.0
TEMP_STEP = 0.5

# TadoLocal "mode" (TargetHeatingCoolingState)
MODE_OFF = 0
MODE_HEAT = 1
MODE_COOL = 2
MODE_AUTO = 3

# TadoLocal "cur_heating" (CurrentHeatingCoolingState)
HEATING_IDLE = 0
HEATING_HEATING = 1
HEATING_COOLING = 2

MANUFACTURER = "tado°"
