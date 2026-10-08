"""Test deriving states from battery module cell data."""

from __future__ import annotations

import struct
from unittest.mock import MagicMock

from rctclient.registry import REGISTRY
from rctclient.types import DataType
from rctclient.utils import decode_value

from .api import get_response_data_type
from .battery_module_helpers import (
    get_cell_resistance_attributes,
    get_cell_status_attributes,
    get_cell_voltage_spread,
    get_max_cell_resistance,
    get_max_cell_temperature,
    get_max_cell_voltage,
    get_mean_cell_resistance,
    get_mean_cell_voltage,
    get_min_cell_temperature,
    get_min_cell_voltage,
)

entity = MagicMock()


def encode_module_status(cells: list[tuple[int, int, int]]) -> bytes:
    """Encode (temperature °C, voltage mV, status) records, padded to 24 cells."""
    cells = cells + [(0, 0, 0)] * (24 - len(cells))
    return b"".join(
        bytes([temperature]) + struct.pack("<H", voltage) + bytes([status])
        for temperature, voltage, status in cells
    )


def encode_module_resistance(resistances_mohm: list[float]) -> bytes:
    resistances_mohm = resistances_mohm + [0] * (24 - len(resistances_mohm))
    return b"".join(
        struct.pack(">H", round(resistance * 256)) + b"\x00\x00"
        for resistance in resistances_mohm
    )


module_status = decode_value(
    DataType.BATTERY_MODULE_STATUS,
    encode_module_status(
        [(21, 3301, 0), (24, 3312, 0), (0, 0, 0), (22, 3295, 1), (255, 3300, 0)]
    ),
)

module_resistance = decode_value(
    DataType.BATTERY_MODULE_RESISTANCE,
    encode_module_resistance([0.5, 0.75, 0, 0.625]),
)


def test_cell_voltages_ignore_empty_slots() -> None:
    assert get_max_cell_voltage(entity, [module_status]) == 3.312
    assert get_min_cell_voltage(entity, [module_status]) == 3.295
    assert get_mean_cell_voltage(entity, [module_status]) == 3.302
    assert get_cell_voltage_spread(entity, [module_status]) == 17


def test_cell_temperatures() -> None:
    assert get_max_cell_temperature(entity, [module_status]) == 24
    # temperatures are signed bytes
    assert get_min_cell_temperature(entity, [module_status]) == -1


def test_cell_status_attributes() -> None:
    assert get_cell_status_attributes(entity, [module_status]) == {
        "cell_count": 4,
        "cell_voltages": [3.301, 3.312, None, 3.295, 3.3],
        "cell_temperatures": [21, 24, None, 22, -1],
        "cell_status": [0, 0, None, 1, 0],
        "max_voltage_cell": 2,
        "min_voltage_cell": 4,
        "max_temperature_cell": 2,
    }


def test_cell_resistances() -> None:
    assert get_max_cell_resistance(entity, [module_resistance]) == 0.75
    assert get_mean_cell_resistance(entity, [module_resistance]) == 0.62
    assert get_cell_resistance_attributes(entity, [module_resistance]) == {
        "cell_resistances": [0.5, 0.75, None, 0.625],
        "max_resistance_cell": 2,
    }


def test_missing_values() -> None:
    assert get_max_cell_voltage(entity, [None]) is None
    assert get_cell_voltage_spread(entity, []) is None
    assert get_max_cell_resistance(entity, ["unexpected"]) is None
    assert get_cell_status_attributes(entity, [None]) == {}


def test_second_tower_uses_module_data_types() -> None:
    def data_type_of(name: str) -> DataType:
        return get_response_data_type(REGISTRY.get_by_name(name).object_id)

    assert (
        data_type_of("battery_placeholder[0].cells[3]")
        == DataType.BATTERY_MODULE_STATUS
    )
    assert (
        data_type_of("battery_placeholder[0].cells_resist[3]")
        == DataType.BATTERY_MODULE_RESISTANCE
    )
    assert data_type_of("battery.cells[3]") == DataType.BATTERY_MODULE_STATUS
    assert data_type_of("battery_placeholder[0].module_sn[3]") == DataType.STRING


# Captured from a real RCT Power Storage 10 diagnostics download.
_REAL_TOWER_2_MODULE_1_CELLS = bytes.fromhex(
    "14960c0014970c00159a0c0015990c00158e0c00159a0c0015930c0015990c00"
    "15940c0015990c0015970c00159a0c00168e0c00169f0c00169d0c0016990c00"
    "16970c0015930c00159a0c00159c0c0015930c00159a0c0015990c00159a0c00"
)


def test_second_tower_decodes_real_payload() -> None:
    object_id = REGISTRY.get_by_name("battery_placeholder[0].cells[0]").object_id
    value = decode_value(
        get_response_data_type(object_id), _REAL_TOWER_2_MODULE_1_CELLS
    )

    assert get_min_cell_voltage(entity, [value]) == 3.214
    assert get_max_cell_voltage(entity, [value]) == 3.231
    assert get_max_cell_temperature(entity, [value]) == 22
    assert get_cell_status_attributes(entity, [value])["cell_count"] == 24


def test_second_tower_without_cell_data() -> None:
    object_id = REGISTRY.get_by_name("battery_placeholder[0].cells[0]").object_id
    value = decode_value(get_response_data_type(object_id), bytes(96))

    assert get_min_cell_voltage(entity, [value]) is None
    assert get_cell_voltage_spread(entity, [value]) is None
    assert get_max_cell_temperature(entity, [value]) is None
    assert get_cell_status_attributes(entity, [value]) == {}
