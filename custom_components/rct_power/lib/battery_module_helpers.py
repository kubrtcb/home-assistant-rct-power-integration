"""Helpers for deriving states from per-module battery cell data."""

from __future__ import annotations

from statistics import mean
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import StateType
from rctclient.types import (
    BatteryModuleCellStatus,
    BatteryModuleResistance,
    BatteryModuleStatus,
)

from .api import ApiResponseValue

CELL_VOLTAGE_DECIMAL_DIGITS = 3
CELL_RESISTANCE_DECIMAL_DIGITS = 2


def get_populated_cells(
    value: ApiResponseValue | None,
) -> dict[int, BatteryModuleCellStatus]:
    """Return the cells of a module status that report a voltage.

    The payload always contains 24 cell slots; slots without a cell report a
    voltage of 0 and are skipped.
    """
    if not isinstance(value, BatteryModuleStatus):
        return {}

    return {
        cell_id: cell for cell_id, cell in value.cells.items() if cell.voltage_mv > 0
    }


def get_populated_cell_resistances(
    value: ApiResponseValue | None,
) -> dict[int, float]:
    if not isinstance(value, BatteryModuleResistance):
        return {}

    return {
        cell_id: cell.resistance_mohm
        for cell_id, cell in value.cells.items()
        if cell.raw_value > 0
    }


def _first(values: list[ApiResponseValue | None]) -> ApiResponseValue | None:
    return values[0] if len(values) > 0 else None


#
# Cell voltages (V)
#
def get_first_api_response_value_as_cell_voltage(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    """Like the default state, but with enough precision for cell voltages."""
    value = _first(values)
    if not isinstance(value, (int, float)):
        return None
    return round(value, CELL_VOLTAGE_DECIMAL_DIGITS)


def get_max_cell_voltage(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    cells = get_populated_cells(_first(values))
    if not cells:
        return None
    return round(
        max(cell.voltage_v for cell in cells.values()), CELL_VOLTAGE_DECIMAL_DIGITS
    )


def get_min_cell_voltage(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    cells = get_populated_cells(_first(values))
    if not cells:
        return None
    return round(
        min(cell.voltage_v for cell in cells.values()), CELL_VOLTAGE_DECIMAL_DIGITS
    )


def get_mean_cell_voltage(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    cells = get_populated_cells(_first(values))
    if not cells:
        return None
    return round(
        mean(cell.voltage_v for cell in cells.values()), CELL_VOLTAGE_DECIMAL_DIGITS
    )


def get_cell_voltage_spread(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    """Difference between the highest and lowest cell voltage in mV."""
    cells = get_populated_cells(_first(values))
    if not cells:
        return None
    voltages = [cell.voltage_mv for cell in cells.values()]
    return max(voltages) - min(voltages)


#
# Cell temperatures (°C)
#
def get_max_cell_temperature(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    cells = get_populated_cells(_first(values))
    if not cells:
        return None
    return max(cell.temperature_c for cell in cells.values())


def get_min_cell_temperature(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    cells = get_populated_cells(_first(values))
    if not cells:
        return None
    return min(cell.temperature_c for cell in cells.values())


def get_cell_status_attributes(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> dict[str, Any]:
    cells = get_populated_cells(_first(values))
    if not cells:
        return {}

    voltages = {cell_id: cell.voltage_mv for cell_id, cell in cells.items()}
    temperatures = {cell_id: cell.temperature_c for cell_id, cell in cells.items()}

    return {
        "cell_count": len(cells),
        "cell_voltages": [round(cell.voltage_v, 3) for cell in cells.values()],
        "cell_temperatures": list(temperatures.values()),
        "cell_status": [cell.status for cell in cells.values()],
        # 1-based cell numbers to match the module numbering
        "max_voltage_cell": max(voltages, key=lambda cell_id: voltages[cell_id]) + 1,
        "min_voltage_cell": min(voltages, key=lambda cell_id: voltages[cell_id]) + 1,
        "max_temperature_cell": max(
            temperatures, key=lambda cell_id: temperatures[cell_id]
        )
        + 1,
    }


#
# Cell resistances (mΩ)
#
def get_max_cell_resistance(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    resistances = get_populated_cell_resistances(_first(values))
    if not resistances:
        return None
    return round(max(resistances.values()), CELL_RESISTANCE_DECIMAL_DIGITS)


def get_mean_cell_resistance(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    resistances = get_populated_cell_resistances(_first(values))
    if not resistances:
        return None
    return round(mean(resistances.values()), CELL_RESISTANCE_DECIMAL_DIGITS)


def get_cell_resistance_attributes(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> dict[str, Any]:
    resistances = get_populated_cell_resistances(_first(values))
    if not resistances:
        return {}

    return {
        "cell_resistances": [
            round(resistance, CELL_RESISTANCE_DECIMAL_DIGITS)
            for resistance in resistances.values()
        ],
        "max_resistance_cell": max(
            resistances, key=lambda cell_id: resistances[cell_id]
        )
        + 1,
    }
