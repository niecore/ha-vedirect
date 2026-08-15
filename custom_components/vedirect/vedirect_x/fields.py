"""Registry mapping raw VE.Direct labels to typed, scaled values.

The wire format is entirely stringly-typed and the scaling is implicit in the
label, not in the payload. `V` is millivolts, `H19` is hundredths of a kWh,
`AC_OUT_I` is tenths of an amp. Getting this table right is most of the work of
supporting a new device.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .const import (
    NOT_AVAILABLE,
    AlarmReason,
    ChargerError,
    ChargerState,
    DeviceMode,
    MonitorMode,
    OffReason,
    TrackerMode,
)


def _scaled(factor: float, digits: int) -> Callable[[str], float]:
    def convert(raw: str) -> float:
        return round(int(raw) * factor, digits)

    return convert


_milli = _scaled(0.001, 3)
_centi = _scaled(0.01, 2)
_deci = _scaled(0.1, 1)


def _integer(raw: str) -> int:
    return int(raw)


def _text(raw: str) -> str:
    return raw


def _on_off(raw: str) -> bool:
    # BMV-600 firmware <= v2.09 sends "On"/"Off"; the spec mandates a
    # case-insensitive comparison.
    return raw.upper() == "ON"


def _alarm_reason(raw: str) -> AlarmReason:
    # AR/WARN are sent in decimal notation, unlike OR which is 0x-prefixed hex.
    return AlarmReason(int(raw))


def _time_to_go(raw: str) -> int | None:
    # -1 means "not discharging, time-to-go infinite".
    minutes = int(raw)
    return None if minutes < 0 else minutes


def _enum(cls: type) -> Callable[[str], Any]:
    def convert(raw: str) -> Any:
        value = int(raw)
        try:
            return cls(value)
        except ValueError:
            # Firmware newer than this library. Surface the raw int rather
            # than throwing away a reading the caller might still want.
            return value

    return convert


def _off_reason(raw: str) -> OffReason:
    return OffReason(int(raw, 16))


@dataclass(frozen=True, slots=True)
class Field:
    """Description of a single VE.Direct label."""

    key: str
    name: str
    convert: Callable[[str], Any]
    unit: str | None = None


def _f(key: str, name: str, convert: Callable[[str], Any], unit: str | None = None) -> Field:
    return Field(key, name, convert, unit)


#: Full TEXT-mode field set of VE.Direct protocol 3.34. Unknown labels pass
#: through raw.
FIELDS: dict[str, Field] = {
    field.key: field
    for field in (
        # --- identification -------------------------------------------------
        _f("PID", "product_id", _text),
        _f("FW", "firmware_version", _text),
        _f("FWE", "firmware_version_extended", _text),
        _f("SER#", "serial_number", _text),
        _f("BMV", "model_description", _text),  # deprecated, prefer PID
        # --- battery --------------------------------------------------------
        _f("V", "battery_voltage", _milli, "V"),
        _f("V2", "battery_voltage_2", _milli, "V"),
        _f("V3", "battery_voltage_3", _milli, "V"),
        _f("VS", "starter_voltage", _milli, "V"),
        _f("VM", "mid_point_voltage", _milli, "V"),
        _f("DM", "mid_point_deviation", _deci, "%"),  # wire unit is ‰
        _f("I", "battery_current", _milli, "A"),
        _f("I2", "battery_current_2", _milli, "A"),
        _f("I3", "battery_current_3", _milli, "A"),
        _f("T", "battery_temperature", _integer, "°C"),
        _f("P", "instantaneous_power", _integer, "W"),
        _f("SOC", "state_of_charge", _deci, "%"),  # wire unit is ‰
        _f("TTG", "time_to_go", _time_to_go, "min"),
        _f("CE", "consumed_amp_hours", _milli, "Ah"),
        _f("MON", "monitor_mode", _enum(MonitorMode)),
        # --- solar ----------------------------------------------------------
        _f("VPV", "panel_voltage", _milli, "V"),
        _f("PPV", "panel_power", _integer, "W"),
        _f("MPPT", "tracker_mode", _enum(TrackerMode)),
        # --- charger / inverter state ---------------------------------------
        _f("CS", "charger_state", _enum(ChargerState)),
        _f("MODE", "device_mode", _enum(DeviceMode)),
        _f("ERR", "error", _enum(ChargerError)),
        _f("OR", "off_reason", _off_reason),
        _f("Alarm", "alarm", _on_off),
        _f("Relay", "relay_state", _on_off),
        _f("LOAD", "load_output", _on_off),
        _f("IL", "load_current", _milli, "A"),
        _f("AR", "alarm_reason", _alarm_reason),
        _f("WARN", "warning_reason", _alarm_reason),
        # --- BMV history ----------------------------------------------------
        _f("H1", "deepest_discharge", _milli, "Ah"),
        _f("H2", "last_discharge", _milli, "Ah"),
        _f("H3", "average_discharge", _milli, "Ah"),
        _f("H4", "charge_cycles", _integer),
        _f("H5", "full_discharges", _integer),
        _f("H6", "total_amp_hours_drawn", _milli, "Ah"),
        _f("H7", "min_battery_voltage", _milli, "V"),
        _f("H8", "max_battery_voltage", _milli, "V"),
        _f("H9", "time_since_last_full_charge", _integer, "s"),
        _f("H10", "automatic_synchronizations", _integer),
        _f("H11", "low_voltage_alarms", _integer),
        _f("H12", "high_voltage_alarms", _integer),
        _f("H13", "low_starter_voltage_alarms", _integer),
        _f("H14", "high_starter_voltage_alarms", _integer),
        _f("H15", "min_starter_voltage", _milli, "V"),
        _f("H16", "max_starter_voltage", _milli, "V"),
        _f("H17", "discharged_energy", _centi, "kWh"),
        _f("H18", "charged_energy", _centi, "kWh"),
        # --- solar yield history --------------------------------------------
        _f("H19", "yield_total", _centi, "kWh"),
        _f("H20", "yield_today", _centi, "kWh"),
        _f("H21", "max_power_today", _integer, "W"),
        _f("H22", "yield_yesterday", _centi, "kWh"),
        _f("H23", "max_power_yesterday", _integer, "W"),
        _f("HSDS", "day_sequence_number", _integer),
        # --- inverter output ------------------------------------------------
        _f("AC_OUT_V", "ac_output_voltage", _centi, "V"),
        _f("AC_OUT_I", "ac_output_current", _deci, "A"),
        _f("AC_OUT_S", "ac_output_apparent_power", _integer, "VA"),
        # --- DC input (Smart BuckBoost) -------------------------------------
        _f("DC_IN_V", "dc_input_voltage", _centi, "V"),
        _f("DC_IN_I", "dc_input_current", _deci, "A"),
        _f("DC_IN_P", "dc_input_power", _integer, "W"),
    )
}


def decode(raw: dict[str, str]) -> dict[str, Any]:
    """Convert a raw label/value block into typed, canonically-named values.

    Unknown labels are kept under their raw key so a new firmware revision
    degrades to "extra strings" rather than a crash. Fields the device reports
    as unavailable are dropped entirely.
    """
    decoded: dict[str, Any] = {}
    for key, value in raw.items():
        if value == NOT_AVAILABLE:
            continue
        field = FIELDS.get(key)
        if field is None:
            decoded[key] = value
            continue
        try:
            decoded[field.name] = field.convert(value)
        except (ValueError, TypeError):
            # A malformed value in one label must not discard the whole frame.
            decoded[field.name] = None
    return decoded
