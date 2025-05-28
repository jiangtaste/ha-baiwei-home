import json
import logging
from typing import Any

from homeassistant import core
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode, FAN_LOW, FAN_MEDIUM, \
    FAN_HIGH
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, GatewayPlatform
from .entity import BaiweiEntity
from .gateway.client import GatewayClient

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    central_ac_climates = await async_get_central_ac_entities(client)
    async_add_entities(central_ac_climates)

    floor_heat_climates = await async_get_floor_heat_entities(client)
    async_add_entities(floor_heat_climates)


async def async_get_central_ac_entities(client: GatewayClient):
    devices, states = await client.get_devices(GatewayPlatform.AC_GATEWAY)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"got central ac devices: {json.dumps(devices)}")
    logger.debug(f"got central ac states: {json.dumps(states)}")

    climates = []
    for device in devices:
        device_attr = device.get("device_attr")
        if device_attr == "CentralAC":
            device_id = device.get("device_id")
            if device_id in states_map:
                logger.debug(f"{device_id}: {states_map[device_id]}")
                device["device_status"] = states_map[device_id]
            climates.append(BaiweiCentralACClimate(client, device))

    return climates


async def async_get_floor_heat_entities(client: GatewayClient):
    devices, states = await client.get_devices(GatewayPlatform.FLOOR_HEAT)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"got floor heat devices: {json.dumps(devices)}")
    logger.debug(f"got floor heat states: {json.dumps(states)}")

    climates = []
    for device in devices:
        device_id = device.get("device_id")
        if device_id in states_map:
            logger.debug(f"{device_id}: {states_map[device_id]}")
            device["device_status"] = states_map[device_id]
        climates.append(BaiweiFloorHeatClimate(client, device))

    return climates


MODE_OFF = "off"
MODE_HEAT = "heat"
MODE_COOL = "cool"
MODE_DRY = "dehumidify"
MODE_FAN_ONLY = "wind"

MODE_TO_STATE = {
    MODE_OFF: HVACMode.OFF,
    MODE_HEAT: HVACMode.HEAT,
    MODE_COOL: HVACMode.COOL,
    MODE_DRY: HVACMode.DRY,
    MODE_FAN_ONLY: HVACMode.FAN_ONLY
}

STATE_TO_MODE = {v: k for k, v in MODE_TO_STATE.items()}

WIND_LOW = "l"
WIND_MEDIUM = "m"
WIND_HIGH = "h"

FAN_TO_STATE = {
    WIND_LOW: FAN_LOW,
    WIND_MEDIUM: FAN_MEDIUM,
    WIND_HIGH: FAN_HIGH,
}

STATE_TO_FAN = {v: k for k, v in FAN_TO_STATE.items()}


class BaiweiCentralACClimate(ClimateEntity, BaiweiEntity):
    def __init__(self, gateway, device):
        super().__init__(gateway, device)

        # 支持的功能
        self._attr_supported_features = (
                ClimateEntityFeature.TARGET_TEMPERATURE |
                ClimateEntityFeature.FAN_MODE
        )

        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY]
        self._attr_fan_modes = [FAN_LOW, FAN_MEDIUM, FAN_HIGH]
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = 16
        self._attr_max_temp = 30
        self._attr_target_temperature_step = 1.0

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self):
        # current temp
        return self.status["curr_temp"] / 100

    @property
    def target_temperature(self):
        # target temp
        return self.status["coolpoint"] / 100

    @property
    def hvac_mode(self):
        # off, cool, wind, heat, dehumidify
        return MODE_TO_STATE[self.status["sys_mode"]]

    @property
    def fan_mode(self):
        # h, m, l
        return FAN_TO_STATE[self.status["wind_level"]]

    async def async_set_temperature(self, **kwargs):
        logger.debug(f"async_set_temperature: {kwargs}")
        temp = kwargs.get("temperature")

        point_key = "heatpoint" if self.hvac_mode == HVACMode.HEAT else "coolpoint"

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                point_key: temp * 100
            }
        })

    async def async_set_hvac_mode(self, hvac_mode):
        logger.debug(f"async_set_hvac_mode {hvac_mode}")

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "sys_mode": STATE_TO_MODE[hvac_mode]
            }
        })

    async def async_set_fan_mode(self, fan_mode):
        logger.debug(f"async_set_hvac_mode {fan_mode}")

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "wind_level": STATE_TO_FAN[fan_mode]
            }
        })


class BaiweiFloorHeatClimate(ClimateEntity, BaiweiEntity):
    def __init__(self, gateway, device):
        super().__init__(gateway, device)

        # 支持的功能
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
        )

        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = 16
        self._attr_max_temp = 35
        self._attr_target_temperature_step = 1.0

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self):
        return self.status["temp"] / 100

    @property
    def target_temperature(self):
        return self.status["heatpoint"] / 100

    @property
    def hvac_mode(self):
        # off, heat
        return MODE_TO_STATE[self.status["sys_mode"]]

    async def async_set_temperature(self, **kwargs):
        logger.debug(f"async_set_temperature: {kwargs}")
        temp = kwargs.get("temperature")

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "heatpoint": temp * 100
            }
        })

    async def async_set_hvac_mode(self, hvac_mode):
        logger.debug(f"async_set_hvac_mode {hvac_mode}")

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "sys_mode": STATE_TO_MODE[hvac_mode]
            }
        })
