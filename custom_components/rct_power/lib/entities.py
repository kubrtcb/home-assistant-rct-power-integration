from __future__ import annotations

import re
from collections.abc import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.helpers.device_registry import DeviceInfo
from rctclient.registry import REGISTRY

from ..const import BATTERY_MODULE_COUNT, EntityUpdatePriority
from .battery_module_helpers import (
    get_cell_resistance_attributes,
    get_cell_status_attributes,
    get_cell_voltage_spread,
    get_first_api_response_value_as_cell_voltage,
    get_max_cell_resistance,
    get_max_cell_temperature,
    get_max_cell_voltage,
    get_mean_cell_resistance,
    get_mean_cell_voltage,
    get_min_cell_temperature,
    get_min_cell_voltage,
)
from .device_info_helpers import (
    get_battery_device_info,
    get_battery_tower_2_device_info,
    get_inverter_device_info,
)
from .entity import (
    RctPowerBatteryModuleSensorEntityDescription,
    RctPowerBitfieldSensorEntityDescription,
    RctPowerEntity,
    RctPowerSensorEntityDescription,
)
from .state_helpers import (
    available_battery_status,
    get_first_api_response_value_as_absolute_state,
    get_first_api_response_value_as_battery_status,
    get_first_api_response_value_as_timestamp,
    sum_api_response_values_as_state,
)


def get_matching_names(expression: str) -> list[str]:
    compiled_expression = re.compile(expression)
    return [
        object_info.name
        for object_info in REGISTRY.all()
        if compiled_expression.match(object_info.name) is not None
    ]


battery_sensor_entity_descriptions: list[RctPowerSensorEntityDescription] = [
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.bms_sn",
        name="Battery Management System Serial Number",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.bms_software_version",
        name="Battery Management System Software Version",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.module_sn[0]",
        name="Battery Module 1 Serial Number",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.module_sn[1]",
        name="Battery Module 2 Serial Number",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.module_sn[2]",
        name="Battery Module 3 Serial Number",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.module_sn[3]",
        name="Battery Module 4 Serial Number",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.module_sn[4]",
        name="Battery Module 5 Serial Number",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.module_sn[5]",
        name="Battery Module 6 Serial Number",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.charged_amp_hours",
        name="Battery Charge Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.discharged_amp_hours",
        name="Battery Discharge Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.current",
        name="Battery Current",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.voltage",
        name="Battery Voltage",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.maximum_charge_voltage",
        name="Battery Maximum Charging Voltage",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.minimum_discharge_voltage",
        name="Battery Minimum Discharging Voltage",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.maximum_discharge_current",
        name="Battery Maximum Discharging Current",
        update_priority=EntityUpdatePriority.FREQUENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.temperature",
        name="Battery Temperature",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.stored_energy",
        name="Battery Stored Energy",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.used_energy",
        name="Battery Used Energy",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.ah_capacity",
        name="Battery Charge Capacity",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.soc",
        name="Battery State of Charge",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="power_mng.soc_min_island",
        name="Battery Minimum State of Charge (Island)",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="power_mng.soc_min",
        name="Battery Minimum State of Charge",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="power_mng.soc_max",
        name="Battery Maximum State of Charge",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.soc_target",
        name="Battery State of Charge Target",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.soc_target_low",
        name="Battery State of Charge Low Target",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.soc_target_high",
        name="Battery State of Charge High Target",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.soh",
        name="Battery State of Health",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.cycles",
        name="Battery Cycles",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="power_mng.bat_next_calib_date",
        name="Next Battery Calibration Date",
        update_priority=EntityUpdatePriority.INFREQUENT,
        device_class=SensorDeviceClass.TIMESTAMP,
        get_native_value=get_first_api_response_value_as_timestamp,
    ),
]


def get_battery_tower_sensor_entity_descriptions(
    object_prefix: str,
    name_prefix: str,
    get_device_info: Callable[[RctPowerEntity], DeviceInfo | None],
) -> list[RctPowerSensorEntityDescription]:
    """Sensors reported by the BMS of a battery tower."""
    return [
        RctPowerSensorEntityDescription(
            get_device_info=get_device_info,
            key=f"{object_prefix}.max_cell_voltage",
            name=f"{name_prefix} Max Cell Voltage",
            update_priority=EntityUpdatePriority.FREQUENT,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=3,
            get_native_value=get_first_api_response_value_as_cell_voltage,
        ),
        RctPowerSensorEntityDescription(
            get_device_info=get_device_info,
            key=f"{object_prefix}.min_cell_voltage",
            name=f"{name_prefix} Min Cell Voltage",
            update_priority=EntityUpdatePriority.FREQUENT,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=3,
            get_native_value=get_first_api_response_value_as_cell_voltage,
        ),
        RctPowerSensorEntityDescription(
            get_device_info=get_device_info,
            key=f"{object_prefix}.max_cell_temperature",
            name=f"{name_prefix} Max Cell Temperature",
            update_priority=EntityUpdatePriority.FREQUENT,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        RctPowerSensorEntityDescription(
            get_device_info=get_device_info,
            key=f"{object_prefix}.min_cell_temperature",
            name=f"{name_prefix} Min Cell Temperature",
            update_priority=EntityUpdatePriority.FREQUENT,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ]


def get_battery_module_sensor_entity_descriptions(
    object_prefix: str,
    name_prefix: str,
    get_device_info: Callable[[RctPowerEntity], DeviceInfo | None],
) -> list[RctPowerSensorEntityDescription]:
    """Sensors for each module of a battery tower."""
    descriptions: list[RctPowerSensorEntityDescription] = []

    for module_index in range(BATTERY_MODULE_COUNT):
        module_name = f"{name_prefix} Module {module_index + 1}"
        cells_object_name = f"{object_prefix}.cells[{module_index}]"
        cells_object_id = REGISTRY.get_by_name(cells_object_name).object_id
        resist_object_name = f"{object_prefix}.cells_resist[{module_index}]"
        resist_object_id = REGISTRY.get_by_name(resist_object_name).object_id

        descriptions += [
            RctPowerSensorEntityDescription(
                get_device_info=get_device_info,
                key=f"{object_prefix}.stack_cycles[{module_index}]",
                name=f"{module_name} Cycles",
                update_priority=EntityUpdatePriority.INFREQUENT,
                state_class=SensorStateClass.TOTAL_INCREASING,
            ),
            RctPowerBatteryModuleSensorEntityDescription(
                get_device_info=get_device_info,
                key=f"{cells_object_name}.max_cell_voltage",
                object_names=[cells_object_name],
                unique_id=f"{cells_object_id}-max_cell_voltage",
                name=f"{module_name} Max Cell Voltage",
                update_priority=EntityUpdatePriority.INFREQUENT,
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.VOLTAGE,
                native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                suggested_display_precision=3,
                get_native_value=get_max_cell_voltage,
                get_extra_state_attributes=get_cell_status_attributes,
            ),
            RctPowerBatteryModuleSensorEntityDescription(
                get_device_info=get_device_info,
                key=f"{cells_object_name}.min_cell_voltage",
                object_names=[cells_object_name],
                unique_id=f"{cells_object_id}-min_cell_voltage",
                name=f"{module_name} Min Cell Voltage",
                update_priority=EntityUpdatePriority.INFREQUENT,
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.VOLTAGE,
                native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                suggested_display_precision=3,
                get_native_value=get_min_cell_voltage,
            ),
            RctPowerBatteryModuleSensorEntityDescription(
                get_device_info=get_device_info,
                key=f"{cells_object_name}.mean_cell_voltage",
                object_names=[cells_object_name],
                unique_id=f"{cells_object_id}-mean_cell_voltage",
                name=f"{module_name} Mean Cell Voltage",
                update_priority=EntityUpdatePriority.INFREQUENT,
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.VOLTAGE,
                native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                suggested_display_precision=3,
                get_native_value=get_mean_cell_voltage,
                entity_registry_enabled_default=False,
            ),
            RctPowerBatteryModuleSensorEntityDescription(
                get_device_info=get_device_info,
                key=f"{cells_object_name}.cell_voltage_spread",
                object_names=[cells_object_name],
                unique_id=f"{cells_object_id}-cell_voltage_spread",
                name=f"{module_name} Cell Voltage Spread",
                update_priority=EntityUpdatePriority.INFREQUENT,
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.VOLTAGE,
                native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
                get_native_value=get_cell_voltage_spread,
            ),
            RctPowerBatteryModuleSensorEntityDescription(
                get_device_info=get_device_info,
                key=f"{cells_object_name}.max_cell_temperature",
                object_names=[cells_object_name],
                unique_id=f"{cells_object_id}-max_cell_temperature",
                name=f"{module_name} Max Cell Temperature",
                update_priority=EntityUpdatePriority.INFREQUENT,
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.TEMPERATURE,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                get_native_value=get_max_cell_temperature,
            ),
            RctPowerBatteryModuleSensorEntityDescription(
                get_device_info=get_device_info,
                key=f"{cells_object_name}.min_cell_temperature",
                object_names=[cells_object_name],
                unique_id=f"{cells_object_id}-min_cell_temperature",
                name=f"{module_name} Min Cell Temperature",
                update_priority=EntityUpdatePriority.INFREQUENT,
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.TEMPERATURE,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                get_native_value=get_min_cell_temperature,
                entity_registry_enabled_default=False,
            ),
            RctPowerBatteryModuleSensorEntityDescription(
                get_device_info=get_device_info,
                key=f"{resist_object_name}.max_cell_resistance",
                object_names=[resist_object_name],
                unique_id=f"{resist_object_id}-max_cell_resistance",
                name=f"{module_name} Max Cell Resistance",
                update_priority=EntityUpdatePriority.STATIC,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement="mΩ",
                entity_category=EntityCategory.DIAGNOSTIC,
                get_native_value=get_max_cell_resistance,
                get_extra_state_attributes=get_cell_resistance_attributes,
            ),
            RctPowerBatteryModuleSensorEntityDescription(
                get_device_info=get_device_info,
                key=f"{resist_object_name}.mean_cell_resistance",
                object_names=[resist_object_name],
                unique_id=f"{resist_object_id}-mean_cell_resistance",
                name=f"{module_name} Mean Cell Resistance",
                update_priority=EntityUpdatePriority.STATIC,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement="mΩ",
                entity_category=EntityCategory.DIAGNOSTIC,
                get_native_value=get_mean_cell_resistance,
            ),
        ]

    return descriptions


battery_tower_2_sensor_entity_descriptions: list[RctPowerSensorEntityDescription] = [
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_tower_2_device_info,
        key="battery_placeholder[0].bms_sn",
        name="Battery Tower 2 Battery Management System Serial Number",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_tower_2_device_info,
        key="battery_placeholder[0].bms_software_version",
        name="Battery Tower 2 Battery Management System Software Version",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    *(
        RctPowerSensorEntityDescription(
            get_device_info=get_battery_tower_2_device_info,
            key=f"battery_placeholder[0].module_sn[{module_index}]",
            name=f"Battery Tower 2 Module {module_index + 1} Serial Number",
            update_priority=EntityUpdatePriority.STATIC,
        )
        for module_index in range(BATTERY_MODULE_COUNT)
    ),
    *get_battery_tower_sensor_entity_descriptions(
        "battery_placeholder[0]", "Battery Tower 2", get_battery_tower_2_device_info
    ),
]

battery_cell_sensor_entity_descriptions: list[RctPowerSensorEntityDescription] = [
    *get_battery_tower_sensor_entity_descriptions(
        "battery", "Battery", get_battery_device_info
    ),
    *get_battery_module_sensor_entity_descriptions(
        "battery", "Battery", get_battery_device_info
    ),
    *get_battery_module_sensor_entity_descriptions(
        "battery_placeholder[0]", "Battery Tower 2", get_battery_tower_2_device_info
    ),
]

inverter_sensor_entity_descriptions: list[RctPowerSensorEntityDescription] = [
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="adc.u_acc",
        name="Inverter Battery Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="android_description",
        name="Inverter Device Name",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="buf_v_control.power_reduction_max_solar",
        name="Generator Maximum Power",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="buf_v_control.power_reduction_max_solar_grid",
        name="Grid Maximum Feed Power",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="db.core_temp",
        name="Core Temperature",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="db.temp1",
        name="Heat Sink Temperature",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="db.temp2",
        name="Heat Sink (battery actuator) Temperature",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[0].enabled",
        name="Generator A Connected",
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[0].mpp.fixed_voltage",
        name="Generator A MPP Fixed Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[0].mpp.mpp_step",
        name="Generator A MPP Search Step",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[0].p_dc",
        name="Generator A Power",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[0].rescan_correction",
        name="Generator A MPP Rescan Correction",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[0].u_sg_lp",
        name="Generator A Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[1].enabled",
        name="Generator B Connected",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[1].mpp.fixed_voltage",
        name="Generator B MPP Fixed Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[1].mpp.mpp_step",
        name="Generator B MPP Search Step",
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[1].p_dc",
        name="Generator B Power",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[1].rescan_correction",
        name="Generator B MPP Rescan Correction",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct[1].u_sg_lp",
        name="Generator B Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.dc_conv_struct.p_dc",
        object_names=[
            "dc_conv.dc_conv_struct[0].p_dc",
            "dc_conv.dc_conv_struct[1].p_dc",
        ],
        name="All Generators Power",
        state_class=SensorStateClass.MEASUREMENT,
        get_native_value=sum_api_response_values_as_state,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="dc_conv.start_voltage",
        name="Inverter DC Start Voltage",
        update_priority=EntityUpdatePriority.STATIC,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="iso_struct.Riso",
        name="Insulation Resistance",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="iso_struct.r_min",
        name="Minimum Insulation Resistance",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="iso_struct.Rn",
        name="Insulation Resistance Negative Input",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="iso_struct.Rp",
        name="Insulation Resistance Positive Input",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="inverter_sn",
        name="Inverter Serial Number",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="svnversion",
        name="Inverter Software Version",
        update_priority=EntityUpdatePriority.INFREQUENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="flash_rtc.time_stamp_update",
        name="Date of Last Update",
        update_priority=EntityUpdatePriority.INFREQUENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac_sum",
        name="Inverter AC Power",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac[0]",
        name="Inverter Power P1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac[1]",
        name="Inverter Power P2",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac[2]",
        name="Inverter Power P3",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac_load_sum_lp",
        name="Consumer Power",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac_load[0]",
        name="Consumer Power P1",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac_load[1]",
        name="Consumer Power P2",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac_load[2]",
        name="Consumer Power P3",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_acc_lp",
        name="Battery Power",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac_grid_sum_lp",
        name="Grid Power",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac_sc[0]",
        name="Grid Power P1",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac_sc[1]",
        name="Grid Power P2",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="g_sync.p_ac_sc[2]",
        name="Grid Power P3",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="grid_pll[0].f",
        name="Grid Frequency",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="rb485.f_grid[0]",
        name="Grid Frequency P1",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="rb485.f_grid[1]",
        name="Grid Frequency P2",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="rb485.f_grid[2]",
        name="Grid Frequency P3",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="rb485.u_l_grid[0]",
        name="Grid Voltage P1",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="rb485.u_l_grid[1]",
        name="Grid Voltage P2",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="rb485.u_l_grid[2]",
        name="Grid Voltage P3",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_load_day",
        name="Consumer Energy Consumption Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_load_month",
        name="Consumer Energy Consumption Month",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_load_year",
        name="Consumer Energy Consumption Year",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_load_total",
        name="Consumer Energy Consumption Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_ac_day",
        name="Inverter Energy Production Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_ac_month",
        name="Inverter Energy Production Month",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_ac_year",
        name="Inverter Energy Production Year",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_ac_total",
        name="Inverter Energy Production Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_feed_day",
        name="Grid Energy Production Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_feed_month",
        name="Grid Energy Production Month",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_feed_year",
        name="Grid Energy Production Year",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_feed_total",
        name="Grid Energy Production Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_feed_absolute_total",
        unique_id="energy.e_grid_feed_absolute_total",  # to avoid collision
        object_names=["energy.e_grid_feed_total"],
        name="Grid Energy Production Absolute Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
        get_native_value=get_first_api_response_value_as_absolute_state,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_load_day",
        name="Grid Energy Consumption Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_load_month",
        name="Grid Energy Consumption Month",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_load_year",
        name="Grid Energy Consumption Year",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_load_total",
        name="Grid Energy Consumption Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_ext_day",
        name="External Energy Production Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_ext_month",
        name="External Energy Production Month",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_ext_year",
        name="External Energy Production Year",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_ext_total",
        name="External Energy Production Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_day[0]",
        name="Generator A Energy Production Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_month[0]",
        name="Generator A Energy Production Month",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_year[0]",
        name="Generator A Energy Production Year",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_total[0]",
        name="Generator A Energy Production Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_day[1]",
        name="Generator B Energy Production Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_month[1]",
        name="Generator B Energy Production Month",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_year[1]",
        name="Generator B Energy Production Year",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_total[1]",
        name="Generator B Energy Production Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_total",
        object_names=["energy.e_dc_total[0]", "energy.e_dc_total[1]"],
        name="All Generators Energy Production Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
        get_native_value=sum_api_response_values_as_state,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="io_board.s0_external_power",
        name="External Generator S0 Power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="W",
    ),
]

bitfield_sensor_entity_descriptions: list[RctPowerBitfieldSensorEntityDescription] = [
    RctPowerBitfieldSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="fault.flt",
        object_names=[
            "fault[0].flt",
            "fault[1].flt",
            "fault[2].flt",
            "fault[3].flt",
        ],
        name="Faults",
        update_priority=EntityUpdatePriority.FREQUENT,
        unique_id=f"{0x37F9D5CA}",  # for backwards-compatibility
    ),
    RctPowerBitfieldSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.bat_status",
        name="Battery Status",
        update_priority=EntityUpdatePriority.FREQUENT,
        get_native_value=get_first_api_response_value_as_battery_status,
        options=available_battery_status,
    ),
]

sensor_entity_descriptions = [
    *battery_sensor_entity_descriptions,
    *battery_tower_2_sensor_entity_descriptions,
    *battery_cell_sensor_entity_descriptions,
    *inverter_sensor_entity_descriptions,
    *bitfield_sensor_entity_descriptions,
]

all_entity_descriptions = [
    *sensor_entity_descriptions,
]
