"""Helpers for deriving states from per-module battery cell data."""

from __future__ import annotations

from statistics import mean, median
from typing import Any, cast

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
CELL_RESISTANCE_ATTRIBUTE_DECIMAL_DIGITS = 3


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


def get_cell_temperature(cell: BatteryModuleCellStatus) -> int:
    """Return the cell temperature in °C.

    The temperature is a signed byte, but rctclient decodes it as unsigned.
    """
    temperature = cell.temperature_c
    return temperature - 256 if temperature > 127 else temperature


def _positional[T](values: dict[int, T], slot_count: int) -> list[T | None]:
    """List values by slot so that missing cells don't shift the numbering.

    Trailing empty slots are dropped.
    """
    if not values:
        return []
    return [values.get(slot) for slot in range(min(slot_count, max(values) + 1))]


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
    return max(get_cell_temperature(cell) for cell in cells.values())


def get_min_cell_temperature(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    cells = get_populated_cells(_first(values))
    if not cells:
        return None
    return min(get_cell_temperature(cell) for cell in cells.values())


def get_cell_status_attributes(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> dict[str, Any]:
    cells = get_populated_cells(_first(values))
    if not cells:
        return {}

    slot_count = len(cast(BatteryModuleStatus, _first(values)).cells)
    voltages = {cell_id: cell.voltage_mv for cell_id, cell in cells.items()}
    temperatures = {
        cell_id: get_cell_temperature(cell) for cell_id, cell in cells.items()
    }

    # lists are indexed by cell slot, cells without a voltage are None
    return {
        "cell_count": len(cells),
        "cell_voltages": _positional(
            {
                cell_id: round(cell.voltage_v, CELL_VOLTAGE_DECIMAL_DIGITS)
                for cell_id, cell in cells.items()
            },
            slot_count,
        ),
        "cell_temperatures": _positional(temperatures, slot_count),
        "cell_status": _positional(
            {cell_id: cell.status for cell_id, cell in cells.items()}, slot_count
        ),
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

    slot_count = len(cast(BatteryModuleResistance, _first(values)).cells)

    # indexed by cell slot, cells without a resistance are None
    return {
        "cell_resistances": _positional(
            {
                # full precision of the 1/256 mΩ raw value
                cell_id: round(resistance, CELL_RESISTANCE_ATTRIBUTE_DECIMAL_DIGITS)
                for cell_id, resistance in resistances.items()
            },
            slot_count,
        ),
        "max_resistance_cell": max(
            resistances, key=lambda cell_id: resistances[cell_id]
        )
        + 1,
    }


#
# Whole tower, across all modules
#
def _cell_label(module_index: int, cell_id: int) -> str:
    """1-based module/cell position, e.g. M3/C1."""
    return f"M{module_index + 1}/C{cell_id + 1}"


def _tower_cell_voltages(values: list[ApiResponseValue | None]) -> dict[str, int]:
    """Cell voltages in mV of all modules, keyed by position."""
    return {
        _cell_label(module_index, cell_id): cell.voltage_mv
        for module_index, value in enumerate(values)
        for cell_id, cell in get_populated_cells(value).items()
    }


def _tower_cell_resistances(values: list[ApiResponseValue | None]) -> dict[str, float]:
    """Cell resistances in mΩ of all modules, keyed by position."""
    return {
        _cell_label(module_index, cell_id): resistance
        for module_index, value in enumerate(values)
        for cell_id, resistance in get_populated_cell_resistances(value).items()
    }


def get_tower_cell_voltage_spread(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    """Difference between the highest and lowest cell of the tower in mV."""
    voltages = _tower_cell_voltages(values)
    if not voltages:
        return None
    return max(voltages.values()) - min(voltages.values())


def get_tower_weakest_cell_deviation(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    """How far the lowest cell is below the median cell of the tower in mV.

    Unlike the spread, a single cell drifting away from the others shows up
    here regardless of which cell is the highest.
    """
    voltages = _tower_cell_voltages(values)
    if not voltages:
        return None
    return round(median(voltages.values()) - min(voltages.values()), 1)


def get_tower_cell_voltage_attributes(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> dict[str, Any]:
    voltages = _tower_cell_voltages(values)
    if not voltages:
        return {}

    return {
        "cell_count": len(voltages),
        "median_cell_voltage": round(median(voltages.values()) / 1000, 4),
        "max_voltage_cell": max(voltages, key=lambda label: voltages[label]),
        "min_voltage_cell": min(voltages, key=lambda label: voltages[label]),
        # one list per module, indexed by cell slot, in V
        "module_cell_voltages": [
            _positional(
                {
                    cell_id: round(cell.voltage_v, CELL_VOLTAGE_DECIMAL_DIGITS)
                    for cell_id, cell in get_populated_cells(value).items()
                },
                len(value.cells),
            )
            if isinstance(value, BatteryModuleStatus)
            else []
            for value in values
        ],
    }


def get_tower_max_cell_resistance(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    resistances = _tower_cell_resistances(values)
    if not resistances:
        return None
    return round(max(resistances.values()), CELL_RESISTANCE_DECIMAL_DIGITS)


def get_tower_max_cell_resistance_deviation(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    """How much the highest cell resistance exceeds the tower median in %."""
    resistances = _tower_cell_resistances(values)
    if not resistances:
        return None
    return round(
        (max(resistances.values()) / median(resistances.values()) - 1) * 100, 1
    )


def get_tower_cell_resistance_attributes(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> dict[str, Any]:
    resistances = _tower_cell_resistances(values)
    if not resistances:
        return {}

    return {
        "median_cell_resistance": round(
            median(resistances.values()), CELL_RESISTANCE_ATTRIBUTE_DECIMAL_DIGITS
        ),
        "max_resistance_cell": max(resistances, key=lambda label: resistances[label]),
        # one list per module, indexed by cell slot, in mΩ
        "module_cell_resistances": [
            _positional(
                {
                    cell_id: round(resistance, CELL_RESISTANCE_ATTRIBUTE_DECIMAL_DIGITS)
                    for cell_id, resistance in get_populated_cell_resistances(
                        value
                    ).items()
                },
                len(value.cells),
            )
            if isinstance(value, BatteryModuleResistance)
            else []
            for value in values
        ],
    }


def get_tower_flagged_cell_count(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> StateType:
    """Number of cells of the tower with a non-zero status byte.

    The meaning of the status byte is not documented. It is expected to flag
    cells the BMS is balancing, which happens near the top of the charge, e.g.
    during a calibration charge.
    """
    statuses = _tower_cell_statuses(values)
    if not statuses:
        return None
    return sum(1 for status in statuses.values() if status != 0)


def get_tower_cell_status_attributes(
    entity: SensorEntity, values: list[ApiResponseValue | None]
) -> dict[str, Any]:
    statuses = _tower_cell_statuses(values)
    if not statuses:
        return {}

    voltages = _tower_cell_voltages(values)
    flagged = {label: status for label, status in statuses.items() if status != 0}

    return {
        "cell_count": len(statuses),
        # positions and raw status bytes of the flagged cells only
        "flagged_cells": flagged,
        "flagged_cell_voltages": {label: voltages[label] for label in flagged},
        "median_cell_voltage": round(median(voltages.values()) / 1000, 4),
    }


def _tower_cell_statuses(values: list[ApiResponseValue | None]) -> dict[str, int]:
    """Status bytes of all cells of the tower, keyed by position."""
    return {
        _cell_label(module_index, cell_id): cell.status
        for module_index, value in enumerate(values)
        for cell_id, cell in get_populated_cells(value).items()
    }


#
# Tower connection
#
# below this the tower voltage is no reading at all, e.g. no second tower
TOWER_MIN_VOLTAGE = 50.0
# parallel towers on the same DC bus differ by well under a volt; a tower
# whose contactor is open drifts away from the bus by tens of volts
TOWER_DISCONNECTED_VOLTAGE_DIFFERENCE = 10.0


def _tower_and_bus_voltage(
    values: list[ApiResponseValue | None],
) -> tuple[float, float] | None:
    match values:
        case [int() | float() as tower_voltage, int() | float() as bus_voltage, *_]:
            pass
        case _:
            return None

    if tower_voltage < TOWER_MIN_VOLTAGE or bus_voltage < TOWER_MIN_VOLTAGE:
        return None
    return float(tower_voltage), float(bus_voltage)


def is_tower_connected(
    entity: Any, values: list[ApiResponseValue | None]
) -> bool | None:
    """Whether the tower is connected to the battery DC bus of the inverter.

    Expects the tower voltage and the battery voltage measured by the inverter.
    The BMS opens the contactor of a tower e.g. when it is deeply discharged,
    the tower then keeps reporting its own voltage, which differs from the bus.
    """
    voltages = _tower_and_bus_voltage(values)
    if voltages is None:
        return None
    tower_voltage, bus_voltage = voltages
    return abs(tower_voltage - bus_voltage) < TOWER_DISCONNECTED_VOLTAGE_DIFFERENCE


def get_tower_connection_attributes(
    entity: Any, values: list[ApiResponseValue | None]
) -> dict[str, Any]:
    voltages = _tower_and_bus_voltage(values)
    if voltages is None:
        return {}
    tower_voltage, bus_voltage = voltages
    return {
        "tower_voltage": round(tower_voltage, 1),
        "bus_voltage": round(bus_voltage, 1),
        "voltage_difference": round(tower_voltage - bus_voltage, 1),
    }
