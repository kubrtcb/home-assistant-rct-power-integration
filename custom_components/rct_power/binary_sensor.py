"""Binary sensor platform for RCT Power."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from . import RctConfigEntry
from .lib.entities import binary_sensor_entity_descriptions
from .lib.entity import RctPowerBinarySensorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RctConfigEntry,
    async_add_entities: Callable[[list[Entity]], None],
) -> None:
    """Setup binary sensor platform."""
    data = entry.runtime_data

    async_add_entities(
        [
            RctPowerBinarySensorEntity(
                coordinators=list(data.update_coordinators.values()),
                config_entry=entry,
                entity_description=entity_description,
            )
            for entity_description in binary_sensor_entity_descriptions
        ]
    )
