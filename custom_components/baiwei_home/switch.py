import json
import logging
from typing import Any

from homeassistant import core
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .baiwei.const import DOMAIN, GatewayPlatform
from .baiwei.baiwei_entity import BaiweiEntity
from .baiwei.client import GatewayClient

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    devices, states = await client.get_devices(GatewayPlatform.ON_OFF_LIGHT)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"get light switch devices: {json.dumps(devices)}")
    logger.debug(f"get light switch states: {json.dumps(states)}")

    switches = []

    for device in devices:
        device_id = device.get("device_id")

        # 合并状态
        if device_id in states_map:
            logger.debug(f"{device_id}: {states_map[device_id]}")
            device["device_status"] = states_map[device_id]

        switches.append(BaiweiSwitch(client, device))

    async_add_entities(switches)


class BaiweiSwitch(SwitchEntity, BaiweiEntity):
    def __init__(self, gateway, device):
        super().__init__(gateway, device)

    @property
    def is_on(self):
        return self.status["state"] == "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "state": "on"
            }
        })

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {
                "state": "off"
            }
        })
