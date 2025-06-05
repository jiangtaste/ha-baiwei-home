import json
import logging

from homeassistant import core
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .baiwei.const import DOMAIN, GatewayPlatform
from .baiwei.baiwei_entity import BaiweiEntity
from .baiwei.client import GatewayClient

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    devices, states = await client.get_devices(GatewayPlatform.NEW_WIND)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"got fresh air fan devices: {json.dumps(devices)}")
    logger.debug(f"got fresh air fan states: {json.dumps(states)}")

    fans = []

    for device in devices:
        device_id = device.get("device_id")

        # 合并状态
        if device_id in states_map:
            logger.debug(f"{device_id}: {states_map[device_id]}")
            device["device_status"] = states_map[device_id]

        fans.append(BaiweiFreshAirFan(client, device))

    async_add_entities(fans)


class BaiweiFreshAirFan(FanEntity, BaiweiEntity):
    def __init__(self, gateway, device):
        super().__init__(gateway, device)

        # 支持的功能
        self._attr_supported_features = FanEntityFeature.SET_SPEED

    @property
    def is_on(self):
        return self._status.get("fan_mode") != "off"

    @property
    def percentage(self):
        return {
            "off": 0,
            "low": 33,
            "medium": 66,
            "high": 100
        }.get(self._status.get("fan_mode"), 0)

    @property
    def percentage_step(self):
        return 33

    async def async_turn_on(self, percentage: int = None, **kwargs):
        logger.debug(f"async_turn_on: {percentage}")

        if percentage is not None:
            await self.async_set_percentage(percentage)
        else:
            await self.gateway.device_service.set_state({
                "device_id": self.device_id,
                "device_status": {
                    "fan_mode": "low"
                }
            })

    async def async_turn_off(self, **kwargs):
        logger.debug(f"async_turn_off")

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "fan_mode": "off"
            }
        })

    async def async_set_percentage(self, percentage):
        fan_mode = (
            "off" if percentage == 0 else
            "low" if percentage <= 33 else
            "medium" if percentage <= 66 else
            "high"
        )

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "fan_mode": fan_mode
            }
        })
