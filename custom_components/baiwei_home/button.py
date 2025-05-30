import json
import logging

from homeassistant import core
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .baiwei.const import DOMAIN, GatewayPlatform
from .baiwei.client import GatewayClient
from .baiwei.baiwei_entity import BaiweiEntity

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    devices, states = await client.get_devices(GatewayPlatform.SCENE_SELECTOR)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"get scene devices: {json.dumps(devices)}")
    logger.debug(f"get scene states: {json.dumps(states)}")

    buttons = []

    for device in devices:
        device_id = device.get("device_id")

        # 合并状态
        if device_id in states_map:
            logger.debug(f"{device_id}: {states_map[device_id]}")
            device["device_status"] = states_map[device_id]

        buttons.append(BaiweiSceneButton(client, device))

    async_add_entities(buttons)


class BaiweiSceneButton(ButtonEntity, BaiweiEntity):
    def __init__(self, gateway, device: dict):
        super().__init__(gateway, device)

    async def async_press(self) -> None:
        logger.debug(f"async_press", self.endpoint)

        await self.gateway.device_service.call_scene(self.endpoint)
