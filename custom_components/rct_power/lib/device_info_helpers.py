from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from ..const import BATTERY_MODEL, DOMAIN, INVERTER_MODEL, NAME
from .entity import RctPowerEntity


def get_inverter_device_info(entity: RctPowerEntity) -> DeviceInfo:
    inverter_sn = str(entity.get_valid_api_response_value_by_name("inverter_sn", None))

    return DeviceInfo(
        identifiers={
            (
                DOMAIN,
                "STORAGE",
                inverter_sn,
            ),
            (
                DOMAIN,
                inverter_sn,
            ),
        },  # type: ignore
        name=str(
            entity.get_valid_api_response_value_by_name("android_description", ""),
        ),
        sw_version=str(entity.get_valid_api_response_value_by_name("svnversion", "")),
        model=INVERTER_MODEL,
        manufacturer=NAME,
    )


def get_battery_device_info(entity: RctPowerEntity) -> DeviceInfo:
    bms_sn = str(entity.get_valid_api_response_value_by_name("battery.bms_sn", None))

    return DeviceInfo(
        identifiers={
            (
                DOMAIN,
                "BATTERY",
                bms_sn,
            ),
            (
                DOMAIN,
                bms_sn,
            ),
        },  # type: ignore
        name=f"Battery at {entity.get_valid_api_response_value_by_name('android_description', '')}",
        sw_version=str(
            entity.get_valid_api_response_value_by_name(
                "battery.bms_software_version", ""
            )
        ),
        model=BATTERY_MODEL,
        manufacturer=NAME,
        via_device=(
            DOMAIN,
            str(entity.get_valid_api_response_value_by_name("inverter_sn", None)),
        ),
    )


def get_battery_tower_2_device_info(entity: RctPowerEntity) -> DeviceInfo:
    inverter_sn = str(entity.get_valid_api_response_value_by_name("inverter_sn", None))
    bms_sn = entity.get_valid_api_response_value_by_name(
        "battery_placeholder[0].bms_sn", None
    )
    # fall back to the inverter serial number so that inverters without a
    # second tower don't end up sharing a device
    tower_id = str(bms_sn) if bms_sn else f"{inverter_sn}-tower-2"

    return DeviceInfo(
        identifiers={
            (
                DOMAIN,
                "BATTERY",
                tower_id,
            ),
            (
                DOMAIN,
                tower_id,
            ),
        },  # type: ignore
        name=f"Battery Tower 2 at {entity.get_valid_api_response_value_by_name('android_description', '')}",
        sw_version=str(
            entity.get_valid_api_response_value_by_name(
                "battery_placeholder[0].bms_software_version", ""
            )
        ),
        model=BATTERY_MODEL,
        manufacturer=NAME,
        via_device=(
            DOMAIN,
            inverter_sn,
        ),
    )
