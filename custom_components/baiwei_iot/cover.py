import json
import logging
from typing import Any

from homeassistant import core
from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, GatewayPlatform
from .entity import BaiweiEntity
from .gateway.client import GatewayClient

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    devices, states = await client.get_devices(GatewayPlatform.WINDOW_COVER)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"get devices: {json.dumps(devices)}")
    logger.debug(f"get states: {json.dumps(states)}")

    covers = []
    for device in devices:
        device_id = device.get("device_id")
        if device_id in states_map:
            logger.debug(f"{device_id}: {states_map[device_id]}")
            device["device_status"] = states_map[device_id]
        covers.append(BaiweiCover(client, device))

    async_add_entities(covers)


class BaiweiCover(CoverEntity, BaiweiEntity):
    def __init__(self, gateway, device):
        super().__init__(gateway, device)

        # 支持的功能
        self._attr_supported_features = (
                CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP | CoverEntityFeature.SET_POSITION
        )

    @property
    def is_closed(self) -> bool:
        return self.status["state"] == "off"

    @property
    def current_cover_position(self) -> int:
        return self.status["level"]

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {"state": "on"}
        })

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {"state": "off"}
        })

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {"state": "stop"}
        })

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        position = kwargs["position"]
        logger.debug(f"async_set_cover_position: {position}")
        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {"level": position}
        })

    async def reverse_motor(self):
        # 反转电机方向
        # home assistant 不支持此功能，仅做备忘
        await self.gateway.device_service.set_state({
            "device_id": self.device_id,
            "device_status": {"reverse": "on"}
        })
