"""Binary sensor platform for Victron VE.Direct."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import VEDirectConfigEntry, VEDirectCoordinator

BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="alarm",
        translation_key="alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="relay_state",
        translation_key="relay_state",
    ),
    BinarySensorEntityDescription(
        key="load_output",
        translation_key="load_output",
        device_class=BinarySensorDeviceClass.POWER,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VEDirectConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add binary sensors for fields as they appear in the broadcast data."""
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def _sync_entities() -> None:
        new = [
            VEDirectBinarySensor(coordinator, description)
            for description in BINARY_SENSORS
            if description.key in coordinator.data and description.key not in known
        ]
        known.update(entity.entity_description.key for entity in new)
        if new:
            async_add_entities(new)

    _sync_entities()
    entry.async_on_unload(coordinator.async_add_listener(_sync_entities))


class VEDirectBinarySensor(CoordinatorEntity[VEDirectCoordinator], BinarySensorEntity):
    """One ON/OFF VE.Direct broadcast field."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VEDirectCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self.entity_description.key)
