"""Test writing the grid feed-in limit."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.number import (
    ATTR_VALUE,
    SERVICE_SET_VALUE,
)
from homeassistant.components.number import (
    DOMAIN as NUMBER_DOMAIN,
)
from homeassistant.const import ATTR_ENTITY_ID, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from rctclient.registry import REGISTRY

from custom_components.rct_power.const import (
    CONF_ALLOW_WRITES,
    CONF_ENTITY_PREFIX,
    CONF_GRID_FEED_POWER_MAX,
    CONF_HOSTNAME,
    DEFAULT_PORT,
    DOMAIN,
)
from custom_components.rct_power.lib.api import RctPowerData, ValidApiResponse

LIMIT_ID = REGISTRY.get_by_name(
    "buf_v_control.power_reduction_max_solar_grid"
).object_id
ENTITY_ID = "number.master_grid_feed_power_limit"


def response(value: float) -> ValidApiResponse:
    return ValidApiResponse(
        object_id=LIMIT_ID, time=datetime.now(tz=UTC), value=value, raw=None
    )


async def fake_get_data(object_ids: list[int]) -> RctPowerData:
    data: RctPowerData = {}
    for object_id in object_ids:
        name = REGISTRY.get_by_id(object_id).name
        if name == "inverter_sn":
            data[object_id] = ValidApiResponse(
                object_id=object_id, time=datetime.now(tz=UTC), value="INV1", raw=None
            )
        elif name == "android_description":
            data[object_id] = ValidApiResponse(
                object_id=object_id, time=datetime.now(tz=UTC), value="Master", raw=None
            )
        elif object_id == LIMIT_ID:
            data[object_id] = response(9600.0)
    return data


async def setup(hass: HomeAssistant, options: dict) -> MockConfigEntry:
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOSTNAME: "localhost",
            CONF_PORT: DEFAULT_PORT,
            CONF_ENTITY_PREFIX: "Master",
        },
        options=options,
        entry_id="test",
    )
    config_entry.add_to_hass(hass)

    with patch(
        "custom_components.rct_power.RctPowerApiClient.async_get_data",
        side_effect=fake_get_data,
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    return config_entry


async def set_value(hass: HomeAssistant, value: float) -> None:
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_VALUE: value},
        blocking=True,
    )


async def test_no_number_without_allow_writes(hass: HomeAssistant) -> None:
    await setup(hass, {})
    assert hass.states.async_all(NUMBER_DOMAIN) == []


async def test_write_grid_feed_power_limit(hass: HomeAssistant) -> None:
    await setup(hass, {CONF_ALLOW_WRITES: True, CONF_GRID_FEED_POWER_MAX: 9600})

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == "9600.0"
    assert state.attributes["max"] == 9600
    assert state.attributes["unit_of_measurement"] == "W"

    with patch(
        "custom_components.rct_power.RctPowerApiClient.async_write_value",
        new=AsyncMock(side_effect=lambda object_id, value: response(value)),
    ) as write:
        # an unchanged value is not written
        await set_value(hass, 9600)
        write.assert_not_called()

        await set_value(hass, 5000)
        write.assert_awaited_once_with(LIMIT_ID, 5000)

    assert hass.states.get(ENTITY_ID).state == "5000.0"  # type: ignore
    # the read-only sensor follows the written value
    [sensor] = [
        s
        for s in hass.states.async_all("sensor")
        if s.entity_id.endswith("_grid_maximum_feed_power")
    ]
    assert sensor.state == "5000.0"

    # values above the configured ceiling are rejected by Home Assistant
    with pytest.raises(ServiceValidationError):
        await set_value(hass, 12000)


async def test_write_not_accepted(hass: HomeAssistant) -> None:
    await setup(hass, {CONF_ALLOW_WRITES: True})

    with (
        patch(
            "custom_components.rct_power.RctPowerApiClient.async_write_value",
            new=AsyncMock(return_value=response(9600.0)),
        ),
        pytest.raises(HomeAssistantError),
    ):
        await set_value(hass, 4000)

    assert hass.states.get(ENTITY_ID).state == "9600.0"  # type: ignore
