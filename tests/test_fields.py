"""Field decoding tests: scaling, enums, bitmask notation, edge values."""

from vedirect_x.const import (
    AlarmReason,
    ChargerState,
    MonitorMode,
    OffReason,
    product_name,
)
from vedirect_x.fields import decode


def test_scaling() -> None:
    decoded = decode(
        {
            "V": "12800",  # mV
            "SOC": "854",  # per mille
            "H19": "1234",  # 0.01 kWh
            "AC_OUT_I": "15",  # 0.1 A
            "DC_IN_V": "1420",  # 0.01 V
            "CE": "-4500",  # mAh
            "T": "23",  # °C
        }
    )
    assert decoded["battery_voltage"] == 12.8
    assert decoded["state_of_charge"] == 85.4
    assert decoded["yield_total"] == 12.34
    assert decoded["ac_output_current"] == 1.5
    assert decoded["dc_input_voltage"] == 14.2
    assert decoded["consumed_amp_hours"] == -4.5
    assert decoded["battery_temperature"] == 23


def test_alarm_reason_is_decimal() -> None:
    """Spec: AR/WARN are decimal, unlike OR which is 0x-prefixed hex."""
    decoded = decode({"AR": "5", "OR": "0x00000010"})
    assert decoded["alarm_reason"] == AlarmReason.LOW_VOLTAGE | AlarmReason.LOW_SOC
    assert decoded["off_reason"] == OffReason.PROTECTION_ACTIVE


def test_on_off_case_insensitive() -> None:
    """BMV-600 firmware <= v2.09 sends 'On'/'Off'."""
    assert decode({"Relay": "On"})["relay_state"] is True
    assert decode({"Alarm": "OFF"})["alarm"] is False
    assert decode({"LOAD": "ON"})["load_output"] is True


def test_not_available_dropped() -> None:
    assert decode({"T": "---", "V": "12000"}) == {"battery_voltage": 12.0}


def test_time_to_go_infinite() -> None:
    assert decode({"TTG": "-1"})["time_to_go"] is None
    assert decode({"TTG": "600"})["time_to_go"] == 600


def test_inverter_states() -> None:
    assert decode({"CS": "9"})["charger_state"] is ChargerState.INVERTING
    assert decode({"CS": "11"})["charger_state"] is ChargerState.POWER_SUPPLY


def test_unknown_enum_value_degrades_to_int() -> None:
    assert decode({"CS": "99"})["charger_state"] == 99


def test_negative_monitor_mode() -> None:
    assert decode({"MON": "-9"})["monitor_mode"] is MonitorMode.SOLAR_CHARGER


def test_unknown_label_passthrough() -> None:
    assert decode({"XYZZY": "42"}) == {"XYZZY": "42"}


def test_malformed_value_does_not_discard_frame() -> None:
    decoded = decode({"V": "bogus", "I": "1000"})
    assert decoded["battery_voltage"] is None
    assert decoded["battery_current"] == 1.0


def test_product_name() -> None:
    assert product_name("0xA053") == "SmartSolar MPPT 75|15"
    assert product_name("0x203") == "BMV-700"
    assert product_name("0xFFFF") is None
    assert product_name("garbage") is None
