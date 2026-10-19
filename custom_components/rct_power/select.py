"""Select platform for RCT Power, used for settings written to the inverter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import Entity
from rctclient.registry import REGISTRY

from . import RctConfigEntry
from .const import CONF_ALLOW_WRITES, EntityUpdatePriority
from .lib.device_info_helpers import get_battery_device_info
from .lib.entity import RctPowerEntity, RctPowerEntityDescription
from .models import RctConfEntryOptions


@dataclass(frozen=True, kw_only=True)
class RctPowerSelectEntityDescription(
    RctPowerEntityDescription, SelectEntityDescription
):
    pass


def get_enum_map(object_name: str) -> dict[int, str]:
    return REGISTRY.get_by_name(object_name).enum_map or {}


select_entity_descriptions: list[RctPowerSelectEntityDescription] = [
    RctPowerSelectEntityDescription(
        get_device_info=get_battery_device_info,
        key="power_mng.soc_strategy",
        unique_id="soc_strategy",
        name="Battery State of Charge Strategy",
        icon="mdi:battery-charging-high",
        update_priority=EntityUpdatePriority.INFREQUENT,
        options=list(get_enum_map("power_mng.soc_strategy").values()),
        entity_category=EntityCategory.CONFIG,
    ),
]


class RctPowerSelectEntity(SelectEntity, RctPowerEntity):
    entity_description: RctPowerSelectEntityDescription  # pyright: ignore [reportIncompatibleVariableOverride]

    @property
    def enum_map(self) -> dict[int, str]:
        return self.object_infos[0].enum_map or {}

    @property
    def current_option(self) -> str | None:
        value = self.get_valid_api_response_value_by_id(
            self.object_infos[0].object_id, None
        )
        if isinstance(value, int):
            return self.enum_map.get(value)
        return None

    async def async_select_option(self, option: str) -> None:
        # the inverter stores the setting permanently, so avoid needless writes
        if option == self.current_option:
            return

        [value] = [key for key, name in self.enum_map.items() if name == option]
        written = await self.async_write_value(value)

        if written != value:
            raise HomeAssistantError(
                f"The inverter kept {self.enum_map.get(int(written), written)}"
                f" instead of {option}"
            )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RctConfigEntry,
    async_add_entities: Callable[[list[Entity]], None],
) -> None:
    """Setup select platform, only if writing is allowed for this inverter."""
    options = cast(RctConfEntryOptions, entry.options)

    if not options.get(CONF_ALLOW_WRITES, False):
        return

    data = entry.runtime_data

    async_add_entities(
        [
            RctPowerSelectEntity(
                coordinators=list(data.update_coordinators.values()),
                config_entry=entry,
                entity_description=entity_description,
            )
            for entity_description in select_entity_descriptions
        ]
    )
