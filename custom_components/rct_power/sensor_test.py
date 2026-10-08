"""Test the battery tower and module sensors."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from rctclient.registry import REGISTRY
from rctclient.utils import decode_value

from custom_components.rct_power.const import (
    CONF_ENTITY_PREFIX,
    CONF_HOSTNAME,
    DEFAULT_PORT,
    DOMAIN,
)
from custom_components.rct_power.lib.api import (
    ApiResponseValue,
    RctPowerData,
    ValidApiResponse,
    get_response_data_type,
)
from custom_components.rct_power.lib.battery_module_helpers_test import (
    encode_module_resistance,
    encode_module_status,
)

RAW_VALUES: dict[str, ApiResponseValue | bytes] = {
    "inverter_sn": "INV1",
    "android_description": "Master",
    "battery.bms_sn": "BMS1",
    "battery_placeholder[0].bms_sn": "BMS2",
    "battery_placeholder[0].max_cell_voltage": 3.312,
    "battery.cells[0]": encode_module_status([(21, 3301, 0), (24, 3312, 0)]),
    "battery_placeholder[0].cells[5]": encode_module_status([(30, 3280, 0)]),
    "battery_placeholder[0].cells_resist[5]": encode_module_resistance([0.5, 1.0]),
}


def get_value(name: str) -> ApiResponseValue:
    object_id = REGISTRY.get_by_name(name).object_id
    value = RAW_VALUES[name]
    if isinstance(value, bytes):
        return decode_value(get_response_data_type(object_id), value)  # type: ignore
    return value


async def fake_get_data(object_ids: list[int]) -> RctPowerData:
    names = {REGISTRY.get_by_name(name).object_id: name for name in RAW_VALUES}
    return {
        object_id: ValidApiResponse(
            object_id=object_id,
            time=datetime.now(tz=UTC),
            value=get_value(names[object_id]),
        )
        for object_id in object_ids
        if object_id in names
    }


def get_state(hass: HomeAssistant, entity_id_suffix: str) -> State:
    """Find a state by the end of its entity id, which is prefixed by the device name."""
    [state] = [
        state
        for state in hass.states.async_all("sensor")
        if state.entity_id.endswith(f"_{entity_id_suffix}")
    ]
    return state


async def test_battery_module_sensors(hass: HomeAssistant) -> None:
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOSTNAME: "localhost",
            CONF_PORT: DEFAULT_PORT,
            CONF_ENTITY_PREFIX: "Master",
        },
        entry_id="test",
    )
    config_entry.add_to_hass(hass)

    with patch(
        "custom_components.rct_power.RctPowerApiClient.async_get_data",
        side_effect=fake_get_data,
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    state = get_state(hass, "master_battery_module_1_max_cell_voltage")
    assert state.state == "3.312"
    assert state.attributes["cell_voltages"] == [3.301, 3.312]
    assert state.attributes["cell_temperatures"] == [21, 24]

    state = get_state(hass, "master_battery_module_1_cell_voltage_spread")
    assert state.state == "11"

    state = get_state(hass, "master_battery_tower_2_module_6_max_cell_temperature")
    assert state.state == "30"

    state = get_state(hass, "master_battery_tower_2_module_6_max_cell_resistance")
    assert state.state == "1.0"
    assert state.attributes["cell_resistances"] == [0.5, 1.0]

    state = get_state(hass, "master_battery_tower_2_max_cell_voltage")
    assert state.state == "3.312"

    # modules without data are unavailable
    state = get_state(hass, "master_battery_module_2_max_cell_voltage")
    assert state.state == "unavailable"

    # the second tower is a device of its own
    entity_entry = er.async_get(hass).async_get(
        get_state(
            hass, "master_battery_tower_2_module_6_max_cell_temperature"
        ).entity_id
    )
    assert entity_entry is not None and entity_entry.device_id is not None
    device = dr.async_get(hass).async_get(entity_entry.device_id)
    assert device is not None
    assert (DOMAIN, "BMS2") in device.identifiers
