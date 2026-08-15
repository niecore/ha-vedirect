"""Constants and enumerations for the VE.Direct protocol."""

from __future__ import annotations

from enum import IntEnum, IntFlag

#: VE.Direct is always 19200 8N1. There is no autobaud.
BAUDRATE = 19200

#: The device emits one TEXT block per second unencrypted, unsolicited.
FRAME_INTERVAL = 1.0

#: Value used by the device for "not applicable / not available".
NOT_AVAILABLE = "---"


class ChargerState(IntEnum):
    """`CS` — operational state of a charger, inverter or solar charger."""

    OFF = 0
    LOW_POWER = 1
    FAULT = 2
    BULK = 3
    ABSORPTION = 4
    FLOAT = 5
    STORAGE = 6
    EQUALIZE_MANUAL = 7
    INVERTING = 9
    POWER_SUPPLY = 11
    STARTING_UP = 245
    REPEATED_ABSORPTION = 246
    AUTO_EQUALIZE = 247
    BATTERY_SAFE = 248
    EXTERNAL_CONTROL = 252


class DeviceMode(IntEnum):
    """`MODE` — configured device mode of an inverter or charger."""

    CHARGER = 1
    INVERTER = 2
    OFF = 4
    ECO = 5
    HIBERNATE = 253


class MonitorMode(IntEnum):
    """`MON` — DC monitor mode of a BMV-71x / SmartShunt."""

    SOLAR_CHARGER = -9
    WIND_TURBINE = -8
    SHAFT_GENERATOR = -7
    ALTERNATOR = -6
    FUEL_CELL = -5
    WATER_GENERATOR = -4
    DC_DC_CHARGER = -3
    AC_CHARGER = -2
    GENERIC_SOURCE = -1
    BATTERY_MONITOR = 0
    GENERIC_LOAD = 1
    ELECTRIC_DRIVE = 2
    FRIDGE = 3
    WATER_PUMP = 4
    BILGE_PUMP = 5
    DC_SYSTEM = 6
    INVERTER = 7
    WATER_HEATER = 8


class AlarmReason(IntFlag):
    """`AR` / `WARN` — bitmask of alarm/warning conditions. Sent in decimal."""

    NONE = 0
    LOW_VOLTAGE = 1
    HIGH_VOLTAGE = 2
    LOW_SOC = 4
    LOW_STARTER_VOLTAGE = 8
    HIGH_STARTER_VOLTAGE = 16
    LOW_TEMPERATURE = 32
    HIGH_TEMPERATURE = 64
    MID_VOLTAGE = 128
    OVERLOAD = 256
    DC_RIPPLE = 512
    LOW_V_AC_OUT = 1024
    HIGH_V_AC_OUT = 2048
    SHORT_CIRCUIT = 4096
    BMS_LOCKOUT = 8192


class TrackerMode(IntEnum):
    """`MPPT` — what the MPP tracker is currently doing."""

    OFF = 0
    VOLTAGE_OR_CURRENT_LIMITED = 1
    MPP_TRACKER_ACTIVE = 2


class OffReason(IntFlag):
    """`OR` — bitmask explaining why the device is off. Sent as 0x-prefixed hex."""

    NONE = 0x00000000
    NO_INPUT_POWER = 0x00000001
    SWITCHED_OFF_POWER_SWITCH = 0x00000002
    SWITCHED_OFF_REGISTER = 0x00000004
    REMOTE_INPUT = 0x00000008
    PROTECTION_ACTIVE = 0x00000010
    PAYGO = 0x00000020
    BMS = 0x00000040
    ENGINE_SHUTDOWN = 0x00000080
    ANALYSING_INPUT_VOLTAGE = 0x00000100


class ChargerError(IntEnum):
    """`ERR` — error code. Unknown codes are preserved as plain ints."""

    NO_ERROR = 0
    BATTERY_VOLTAGE_TOO_HIGH = 2
    CHARGER_TEMPERATURE_TOO_HIGH = 17
    CHARGER_OVER_CURRENT = 18
    CHARGER_CURRENT_POLARITY_REVERSED = 19
    BULK_TIME_LIMIT_EXCEEDED = 20
    CURRENT_SENSOR_ISSUE = 21
    TERMINAL_TEMPERATURE_TOO_HIGH = 26
    CONVERTER_ISSUE = 28
    INPUT_VOLTAGE_TOO_HIGH = 33
    INPUT_CURRENT_TOO_HIGH = 34
    INPUT_SHUTDOWN_EXCESSIVE_BATTERY_VOLTAGE = 38
    INPUT_SHUTDOWN_CURRENT_FLOW = 39
    LOST_COMMUNICATION = 65
    SYNCHRONISED_CHARGING_CONFIG_ISSUE = 66
    BMS_CONNECTION_LOST = 67
    NETWORK_MISCONFIGURED = 68
    FACTORY_CALIBRATION_LOST = 116
    INVALID_FIRMWARE = 117
    USER_SETTINGS_INVALID = 119


#: `PID` → product name, per VE.Direct protocol 3.34.
PRODUCT_IDS: dict[int, str] = {
    0x203: "BMV-700",
    0x204: "BMV-702",
    0x205: "BMV-700H",
    0x300: "BlueSolar MPPT 70|15",
    0xA040: "BlueSolar MPPT 75|50",
    0xA041: "BlueSolar MPPT 150|35",
    0xA042: "BlueSolar MPPT 75|15",
    0xA043: "BlueSolar MPPT 100|15",
    0xA044: "BlueSolar MPPT 100|30",
    0xA045: "BlueSolar MPPT 100|50",
    0xA046: "BlueSolar MPPT 150|70",
    0xA047: "BlueSolar MPPT 150|100",
    0xA049: "BlueSolar MPPT 100|50 rev2",
    0xA04A: "BlueSolar MPPT 100|30 rev2",
    0xA04B: "BlueSolar MPPT 150|35 rev2",
    0xA04C: "BlueSolar MPPT 75|10",
    0xA04D: "BlueSolar MPPT 150|45",
    0xA04E: "BlueSolar MPPT 150|60",
    0xA04F: "BlueSolar MPPT 150|85",
    0xA050: "SmartSolar MPPT 250|100",
    0xA051: "SmartSolar MPPT 150|100",
    0xA052: "SmartSolar MPPT 150|85",
    0xA053: "SmartSolar MPPT 75|15",
    0xA054: "SmartSolar MPPT 75|10",
    0xA055: "SmartSolar MPPT 100|15",
    0xA056: "SmartSolar MPPT 100|30",
    0xA057: "SmartSolar MPPT 100|50",
    0xA058: "SmartSolar MPPT 150|35",
    0xA059: "SmartSolar MPPT 150|100 rev2",
    0xA05A: "SmartSolar MPPT 150|85 rev2",
    0xA05B: "SmartSolar MPPT 250|70",
    0xA05C: "SmartSolar MPPT 250|85",
    0xA05D: "SmartSolar MPPT 250|60",
    0xA05E: "SmartSolar MPPT 250|45",
    0xA05F: "SmartSolar MPPT 100|20",
    0xA060: "SmartSolar MPPT 100|20 48V",
    0xA061: "SmartSolar MPPT 150|45",
    0xA062: "SmartSolar MPPT 150|60",
    0xA063: "SmartSolar MPPT 150|70",
    0xA064: "SmartSolar MPPT 250|85 rev2",
    0xA065: "SmartSolar MPPT 250|100 rev2",
    0xA066: "BlueSolar MPPT 100|20",
    0xA067: "BlueSolar MPPT 100|20 48V",
    0xA068: "SmartSolar MPPT 250|60 rev2",
    0xA069: "SmartSolar MPPT 250|70 rev2",
    0xA06A: "SmartSolar MPPT 150|45 rev2",
    0xA06B: "SmartSolar MPPT 150|60 rev2",
    0xA06C: "SmartSolar MPPT 150|70 rev2",
    0xA06D: "SmartSolar MPPT 150|85 rev3",
    0xA06E: "SmartSolar MPPT 150|100 rev3",
    0xA06F: "BlueSolar MPPT 150|45 rev2",
    0xA070: "BlueSolar MPPT 150|60 rev2",
    0xA071: "BlueSolar MPPT 150|70 rev2",
    0xA072: "BlueSolar MPPT 150|45 rev3",
    0xA073: "SmartSolar MPPT 150|45 rev3",
    0xA074: "SmartSolar MPPT 75|10 rev2",
    0xA075: "SmartSolar MPPT 75|15 rev2",
    0xA076: "BlueSolar MPPT 100|30 rev3",
    0xA077: "BlueSolar MPPT 100|50 rev3",
    0xA078: "BlueSolar MPPT 150|35 rev3",
    0xA079: "BlueSolar MPPT 75|10 rev2",
    0xA07A: "BlueSolar MPPT 75|15 rev2",
    0xA07B: "BlueSolar MPPT 100|15 rev2",
    0xA07C: "BlueSolar MPPT 75|10 rev3",
    0xA07D: "BlueSolar MPPT 75|15 rev3",
    0xA07E: "SmartSolar MPPT 100|30 12V",
    0xA07F: "All-In-1 SmartSolar MPPT 75|15 12V",
    0xA080: "SmartSolar MPPT 250|60 rev3",
    0xA081: "SmartSolar MPPT 250|70 rev3",
    0xA102: "SmartSolar MPPT VE.Can 150|70",
    0xA103: "SmartSolar MPPT VE.Can 150|45",
    0xA104: "SmartSolar MPPT VE.Can 150|60",
    0xA105: "SmartSolar MPPT VE.Can 150|85",
    0xA106: "SmartSolar MPPT VE.Can 150|100",
    0xA107: "SmartSolar MPPT VE.Can 250|45",
    0xA108: "SmartSolar MPPT VE.Can 250|60",
    0xA109: "SmartSolar MPPT VE.Can 250|70",
    0xA10A: "SmartSolar MPPT VE.Can 250|85",
    0xA10B: "SmartSolar MPPT VE.Can 250|100",
    0xA10C: "SmartSolar MPPT VE.Can 150|70 rev2",
    0xA10D: "SmartSolar MPPT VE.Can 150|85 rev2",
    0xA10E: "SmartSolar MPPT VE.Can 150|100 rev2",
    0xA10F: "BlueSolar MPPT VE.Can 150|100",
    0xA112: "BlueSolar MPPT VE.Can 250|70",
    0xA113: "BlueSolar MPPT VE.Can 250|100",
    0xA114: "SmartSolar MPPT VE.Can 250|70 rev2",
    0xA115: "SmartSolar MPPT VE.Can 250|100 rev2",
    0xA116: "SmartSolar MPPT VE.Can 250|85 rev2",
    0xA117: "BlueSolar MPPT VE.Can 150|100 rev2",
    0xA201: "Phoenix Inverter 12V 250VA 230V",
    0xA202: "Phoenix Inverter 24V 250VA 230V",
    0xA204: "Phoenix Inverter 48V 250VA 230V",
    0xA211: "Phoenix Inverter 12V 375VA 230V",
    0xA212: "Phoenix Inverter 24V 375VA 230V",
    0xA214: "Phoenix Inverter 48V 375VA 230V",
    0xA221: "Phoenix Inverter 12V 500VA 230V",
    0xA222: "Phoenix Inverter 24V 500VA 230V",
    0xA224: "Phoenix Inverter 48V 500VA 230V",
    0xA231: "Phoenix Inverter 12V 250VA 230V",
    0xA232: "Phoenix Inverter 24V 250VA 230V",
    0xA234: "Phoenix Inverter 48V 250VA 230V",
    0xA239: "Phoenix Inverter 12V 250VA 120V",
    0xA23A: "Phoenix Inverter 24V 250VA 120V",
    0xA23C: "Phoenix Inverter 48V 250VA 120V",
    0xA241: "Phoenix Inverter 12V 375VA 230V",
    0xA242: "Phoenix Inverter 24V 375VA 230V",
    0xA244: "Phoenix Inverter 48V 375VA 230V",
    0xA249: "Phoenix Inverter 12V 375VA 120V",
    0xA24A: "Phoenix Inverter 24V 375VA 120V",
    0xA24C: "Phoenix Inverter 48V 375VA 120V",
    0xA251: "Phoenix Inverter 12V 500VA 230V",
    0xA252: "Phoenix Inverter 24V 500VA 230V",
    0xA254: "Phoenix Inverter 48V 500VA 230V",
    0xA259: "Phoenix Inverter 12V 500VA 120V",
    0xA25A: "Phoenix Inverter 24V 500VA 120V",
    0xA25C: "Phoenix Inverter 48V 500VA 120V",
    0xA261: "Phoenix Inverter 12V 800VA 230V",
    0xA262: "Phoenix Inverter 24V 800VA 230V",
    0xA264: "Phoenix Inverter 48V 800VA 230V",
    0xA269: "Phoenix Inverter 12V 800VA 120V",
    0xA26A: "Phoenix Inverter 24V 800VA 120V",
    0xA26C: "Phoenix Inverter 48V 800VA 120V",
    0xA271: "Phoenix Inverter 12V 1200VA 230V",
    0xA272: "Phoenix Inverter 24V 1200VA 230V",
    0xA274: "Phoenix Inverter 48V 1200VA 230V",
    0xA279: "Phoenix Inverter 12V 1200VA 120V",
    0xA27A: "Phoenix Inverter 24V 1200VA 120V",
    0xA27C: "Phoenix Inverter 48V 1200VA 120V",
    0xA281: "Phoenix Inverter 12V 1600VA 230V",
    0xA282: "Phoenix Inverter 24V 1600VA 230V",
    0xA284: "Phoenix Inverter 48V 1600VA 230V",
    0xA291: "Phoenix Inverter 12V 2000VA 230V",
    0xA292: "Phoenix Inverter 24V 2000VA 230V",
    0xA294: "Phoenix Inverter 48V 2000VA 230V",
    0xA2A1: "Phoenix Inverter 12V 3000VA 230V",
    0xA2A2: "Phoenix Inverter 24V 3000VA 230V",
    0xA2A4: "Phoenix Inverter 48V 3000VA 230V",
    0xA340: "Phoenix Smart IP43 Charger 12|50 (1+1)",
    0xA341: "Phoenix Smart IP43 Charger 12|50 (3)",
    0xA342: "Phoenix Smart IP43 Charger 24|25 (1+1)",
    0xA343: "Phoenix Smart IP43 Charger 24|25 (3)",
    0xA344: "Phoenix Smart IP43 Charger 12|30 (1+1)",
    0xA345: "Phoenix Smart IP43 Charger 12|30 (3)",
    0xA346: "Phoenix Smart IP43 Charger 24|16 (1+1)",
    0xA347: "Phoenix Smart IP43 Charger 24|16 (3)",
    0xA381: "BMV-712 Smart",
    0xA382: "BMV-710H Smart",
    0xA383: "BMV-712 Smart Rev2",
    0xA389: "SmartShunt 500A/50mV",
    0xA38A: "SmartShunt 1000A/50mV",
    0xA38B: "SmartShunt 2000A/50mV",
    0xA3F0: "Orion XS 12V/12V-50A",
    0xA3F1: "Orion XS 1400",
}


def product_name(pid: str) -> str | None:
    """Resolve a raw `PID` value like ``0xA053`` to a product name."""
    try:
        return PRODUCT_IDS.get(int(pid, 16))
    except ValueError:
        return None
