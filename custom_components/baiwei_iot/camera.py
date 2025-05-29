import json
import logging

from homeassistant import core
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, GatewayPlatform
from .baiwei_entity import BaiweiEntity
from .gateway.client import GatewayClient

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    devices, states = await client.get_devices(GatewayPlatform.BW_CATEYE)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"got cat eye devices: {json.dumps(devices)}")
    logger.debug(f"got cat eye states: {json.dumps(states)}")

    # fans = []
    #
    # for device in devices:
    #     device_id = device.get("device_id")
    #
    #     # 合并状态
    #     if device_id in states_map:
    #         logger.debug(f"{device_id}: {states_map[device_id]}")
    #         device["device_status"] = states_map[device_id]
    #
    #     fans.append(BaiweiFreshAirFan(client, device))
    #
    # async_add_entities(fans)


class BaiweiCatEyeCamera(Camera, BaiweiEntity):
    def __init__(self, gateway, device):
        super().__init__(gateway, device)

    @property
    def is_streaming(self) -> bool:
        return True  # 或根据状态判断

    async def stream_source(self):
        return "self._stream_url"  # e.g. rtsp://...

    async def async_camera_image(self):
        pass
