"""Constants for the NUT Hass.io integration."""

DOMAIN = "nut_hassio"

CONF_UPS_NAME = "ups_name"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_PORT = 3493
DEFAULT_HOST = "127.0.0.1"

EVENT_NUT_UPS = "nut.ups_event"

STATUS_ONLINE = "ONLINE"
STATUS_ONBATT = "ONBATT"
STATUS_LOWBATT = "LOWBATT"
STATUS_FSD = "FSD"
STATUS_UNKNOWN = "UNKNOWN"

NOTIFY_STATUSES = frozenset(
    {STATUS_ONLINE, STATUS_ONBATT, STATUS_LOWBATT, STATUS_FSD}
)

POLL_INTERVAL_SECONDS = 30

NUMERIC_SENSORS = (
    ("battery.charge", "battery_charge", "%"),
    ("input.voltage", "input_voltage", "V"),
    ("ups.load", "load", "%"),
    ("battery.runtime", "battery_runtime", "s"),
)
