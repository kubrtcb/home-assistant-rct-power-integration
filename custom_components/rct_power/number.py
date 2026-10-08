"""Number platform for RCT Power, used for settings written to the inverter."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import Entity

from . import RctConfigEntry
from .const import (
    CONF_ALLOW_WRITES,
    CONF_GRID_FEED_POWER_MAX,
    DEFAULT_GRID_FEED_POWER_MAX,
    EntityUpdatePriority,
)
from .lib.api import ValidApiResponse
from .lib.device_info_helpers import get_inverter_device_info
from .lib.entity import RctPowerEntity, RctPowerEntityDescription
from .models import RctConfEntryOptions


@dataclass(frozen=True, kw_only=True)
class RctPowerNumberEntityDescription(
    RctPowerEntityDescription, NumberEntityDescription
):
    # the inverter value multiplied by this is shown in Home Assistant
    scale: float = 1


def get_number_entity_descriptions(
    options: RctConfEntryOptions,
) -> list[RctPowerNumberEntityDescription]:
    return [
        RctPowerNumberEntityDescription(
            get_device_info=get_inverter_device_info,
            key="buf_v_control.power_reduction_max_solar_grid",
            unique_id="grid_feed_power_limit",
            name="Grid Feed Power Limit",
            icon="mdi:transmission-tower-export",
            update_priority=EntityUpdatePriority.STATIC,
            device_class=NumberDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.WATT,
            native_min_value=0,
            native_max_value=options.get(
                CONF_GRID_FEED_POWER_MAX, DEFAULT_GRID_FEED_POWER_MAX
            ),
            native_step=100,
            mode=NumberMode.BOX,
            entity_category=EntityCategory.CONFIG,
        ),
        # the inverter takes a fraction of the solar plant peak power
        RctPowerNumberEntityDescription(
            get_device_info=get_inverter_device_info,
            key="buf_v_control.power_reduction",
            unique_id="external_power_reduction",
            name="External Power Reduction",
            icon="mdi:solar-power-variant",
            update_priority=EntityUpdatePriority.INFREQUENT,
            native_unit_of_measurement=PERCENTAGE,
            native_min_value=0,
            native_max_value=100,
            native_step=1,
            scale=100,
            mode=NumberMode.BOX,
            entity_category=EntityCategory.CONFIG,
        ),
    ]


class RctPowerNumberEntity(NumberEntity, RctPowerEntity):
    entity_description: RctPowerNumberEntityDescription  # pyright: ignore [reportIncompatibleVariableOverride]

    @property
    def native_value(self) -> float | None:
        value = self.get_valid_api_response_value_by_id(
            self.object_infos[0].object_id, None
        )
        if isinstance(value, int | float) and math.isfinite(value):
            return round(value * self.entity_description.scale, 2)
        return None

    async def async_set_native_value(self, value: float) -> None:
        # the inverter stores the setting permanently, so avoid needless writes
        if self.native_value is not None and math.isclose(
            self.native_value, value, abs_tol=0.5
        ):
            return

        object_id = self.object_infos[0].object_id
        coordinator = self.coordinators[0]
        scale = self.entity_description.scale
        response = await coordinator.client.async_write_value(object_id, value / scale)

        if not isinstance(response, ValidApiResponse) or not isinstance(
            response.value, int | float
        ):
            raise HomeAssistantError(
                f"The inverter did not confirm the new value for {self.name}"
            )

        # update every coordinator that holds this object so all entities agree
        for coordinator in self.coordinators:
            if object_id in coordinator.object_ids:
                coordinator.async_set_updated_data(
                    {**coordinator.data, object_id: response}
                )

        if not math.isclose(response.value * scale, value, abs_tol=0.5):
            raise HomeAssistantError(
                f"The inverter kept {response.value * scale} instead of {value}"
            )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RctConfigEntry,
    async_add_entities: Callable[[list[Entity]], None],
) -> None:
    """Setup number platform, only if writing is allowed for this inverter."""
    options = cast(RctConfEntryOptions, entry.options)

    if not options.get(CONF_ALLOW_WRITES, False):
        return

    data = entry.runtime_data

    async_add_entities(
        [
            RctPowerNumberEntity(
                coordinators=list(data.update_coordinators.values()),
                config_entry=entry,
                entity_description=entity_description,
            )
            for entity_description in get_number_entity_descriptions(options)
        ]
    )
