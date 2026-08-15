"""Sensor platform for Victron VE.Direct.

Entities are created dynamically: a description only becomes an entity once
its field has actually been seen on the wire, so an MPPT gets solar entities,
a BMV gets battery-monitor entities, and firmware additions appear without
code changes to this file.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, IntFlag
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import VEDirectConfigEntry, VEDirectCoordinator
from .vedirect_x import ChargerError, ChargerState, DeviceMode, MonitorMode, TrackerMode


@dataclass(frozen=True, kw_only=True)
class VEDirectSensorDescription(SensorEntityDescription):
    """Sensor description with an optional raw-value transform."""

    value_fn: Callable[[Any], StateType] | None = None


def _enum_state(value: Any) -> StateType:
    """Map a decoded IntEnum to its slug; unknown ints become unknown."""
    if isinstance(value, Enum):
        return value.name.lower()
    return None


def _flag_state(value: Any) -> StateType:
    """Render an IntFlag bitmask as a comma-separated list of conditions."""
    if not isinstance(value, IntFlag):
        return None
    if value.value == 0:
        return "none"
    return ", ".join(
        flag.name.lower()
        for flag in type(value)
        if flag.name and flag.value and flag.value & value.value == flag.value
    )


def _options(enum: type[Enum]) -> list[str]:
    return [member.name.lower() for member in enum]


def _v(key: str, **kwargs: Any) -> VEDirectSensorDescription:
    return VEDirectSensorDescription(key=key, translation_key=key, **kwargs)


SENSORS: tuple[VEDirectSensorDescription, ...] = (
    # --- live measurements --------------------------------------------------
    _v(
        "battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "battery_voltage_2",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "battery_voltage_3",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "starter_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "mid_point_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "mid_point_deviation",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _v(
        "battery_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "battery_current_2",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "battery_current_3",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "battery_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _v(
        "instantaneous_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _v(
        "state_of_charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _v(
        "time_to_go",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    _v(
        "consumed_amp_hours",
        native_unit_of_measurement="Ah",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _v(
        "load_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    # --- solar --------------------------------------------------------------
    _v(
        "panel_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "panel_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # --- states -------------------------------------------------------------
    _v(
        "charger_state",
        device_class=SensorDeviceClass.ENUM,
        options=_options(ChargerState),
        value_fn=_enum_state,
    ),
    _v(
        "tracker_mode",
        device_class=SensorDeviceClass.ENUM,
        options=_options(TrackerMode),
        value_fn=_enum_state,
    ),
    _v(
        "device_mode",
        device_class=SensorDeviceClass.ENUM,
        options=_options(DeviceMode),
        value_fn=_enum_state,
    ),
    _v(
        "monitor_mode",
        device_class=SensorDeviceClass.ENUM,
        options=_options(MonitorMode),
        value_fn=_enum_state,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _v(
        "error",
        device_class=SensorDeviceClass.ENUM,
        options=_options(ChargerError),
        value_fn=_enum_state,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _v(
        "off_reason",
        value_fn=_flag_state,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _v(
        "alarm_reason",
        value_fn=_flag_state,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _v(
        "warning_reason",
        value_fn=_flag_state,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # --- solar yield history ------------------------------------------------
    _v(
        "yield_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    _v(
        "yield_today",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    _v(
        "yield_yesterday",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
    ),
    _v(
        "max_power_today",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    _v(
        "max_power_yesterday",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    _v(
        "day_sequence_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # --- BMV history --------------------------------------------------------
    _v(
        "discharged_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    _v(
        "charged_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    _v(
        "deepest_discharge",
        native_unit_of_measurement="Ah",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "last_discharge",
        native_unit_of_measurement="Ah",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "average_discharge",
        native_unit_of_measurement="Ah",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "charge_cycles",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "full_discharges",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "total_amp_hours_drawn",
        native_unit_of_measurement="Ah",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "min_battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        suggested_display_precision=2,
    ),
    _v(
        "max_battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        suggested_display_precision=2,
    ),
    _v(
        "min_starter_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        suggested_display_precision=2,
    ),
    _v(
        "max_starter_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        suggested_display_precision=2,
    ),
    _v(
        "time_since_last_full_charge",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "automatic_synchronizations",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "low_voltage_alarms",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "high_voltage_alarms",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "low_starter_voltage_alarms",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    _v(
        "high_starter_voltage_alarms",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # --- inverter output ----------------------------------------------------
    _v(
        "ac_output_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "ac_output_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _v(
        "ac_output_apparent_power",
        device_class=SensorDeviceClass.APPARENT_POWER,
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # --- DC input (Smart BuckBoost) -----------------------------------------
    _v(
        "dc_input_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    _v(
        "dc_input_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _v(
        "dc_input_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VEDirectConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for fields as they appear in the broadcast data."""
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def _sync_entities() -> None:
        new = [
            VEDirectSensor(coordinator, description)
            for description in SENSORS
            if description.key in coordinator.data and description.key not in known
        ]
        known.update(entity.entity_description.key for entity in new)
        if new:
            async_add_entities(new)

    _sync_entities()
    entry.async_on_unload(coordinator.async_add_listener(_sync_entities))


class VEDirectSensor(CoordinatorEntity[VEDirectCoordinator], SensorEntity):
    """One VE.Direct broadcast field."""

    entity_description: VEDirectSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VEDirectCoordinator,
        description: VEDirectSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> StateType:
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(value)
        return value
