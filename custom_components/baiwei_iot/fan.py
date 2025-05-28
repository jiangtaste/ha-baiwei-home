import json
import logging

from homeassistant import core
from homeassistant.components.climate import FAN_LOW, FAN_MEDIUM, FAN_HIGH
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, GatewayPlatform
from .entity import BaiweiEntity
from .gateway.client import GatewayClient

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    devices, states = await client.get_devices(GatewayPlatform.NEW_WIND)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"got fresh air devices: {json.dumps(devices)}")
    logger.debug(f"got fresh air states: {json.dumps(states)}")

    fans = []
    for device in devices:
        device_id = device.get("device_id")
        if device_id in states_map:
            logger.debug(f"{device_id}: {states_map[device_id]}")
            device["device_status"] = states_map[device_id]
        fans.append(BaiweiFreshAir(client, device))

    async_add_entities(fans)


WIND_LOW = "l"
WIND_MEDIUM = "m"
WIND_HIGH = "h"

FAN_TO_STATE = {
    WIND_LOW: FAN_LOW,
    WIND_MEDIUM: FAN_MEDIUM,
    WIND_HIGH: FAN_HIGH,
}

STATE_TO_FAN = {v: k for k, v in FAN_TO_STATE.items()}

FAN_MODES = ["low", "medium", "high"]


class BaiweiFreshAir(FanEntity, BaiweiEntity):
    def __init__(self, gateway, device):
        super().__init__(gateway, device)
        self.gateway = gateway

        # 支持的功能
        self._attr_supported_features = FanEntityFeature.SET_SPEED
        self._attr_speed_count = 3

    @property
    def is_on(self):
        return self.status.get("state") == "online"

    @property
    def percentage(self):
        try:
            index = FAN_MODES.index(self.status.get("fan_mode"))
            return (index + 1) * 33
        except ValueError:
            return 0

    async def async_turn_on(self, **kwargs):
        logger.debug(f"async_turn_on")

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "state": "online"
            }
        })

    async def async_turn_off(self, **kwargs):
        logger.debug(f"async_turn_off")

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "state": "offline"
            }
        })

    async def async_set_percentage(self, percentage: int):
        logger.debug(f"async_turn_off")

        index = min(2, percentage // 33)

        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "fan_mode": FAN_MODES[index]
            }
        })

    @property
    def extra_state_attributes(self):
        return {
            "lock_mode": self.status.get("lock_mode"),
            "temperature": self.status.get("temp") / 100
        }
