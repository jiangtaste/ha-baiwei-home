import json
import logging
from typing import Any

from homeassistant import core
from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, GatewayPlatform
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
        covers.append(JQCover(client, device))

    async_add_entities(covers)


class JQCover(CoverEntity):
    def __init__(self, client, device):
        self._client = client
        self._device = device

        # 唯一ID，建议使用设备唯一标识，防止重复
        self._attr_unique_id = str(self._device["device_id"])

        # 设备名称
        self._attr_name = self._device["device_name"] or self._device["product_name"]

        # 支持的功能
        self._attr_supported_features = (
                CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP | CoverEntityFeature.SET_POSITION
        )

        # 属性
        self._status = self._device["device_status"]

        self._is_closed = self._status["state"] == "off"
        self._current_cover_position = self._status["level"]

        # 其他属性
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.get("mac"))},
            "name": f"窗帘 {device.get("model")}",
            "model": device.get("model"),
            "manufacturer": "Baiwei",  # 根据实际填写
            "sw_version": device.get("soft_ver"),
            "hw_version": device.get("hard_ver"),
        }

        self._client.device_service.register_entry(self._device["device_id"], self)

    @property
    def is_closed(self) -> bool:
        return self._is_closed

    @property
    def current_cover_position(self) -> int:
        return self._current_cover_position

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._client.device_service.set_state({
            "device_id": self._device["device_id"],
            "device_status": {"state": "on"}
        })

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._client.device_service.set_state({
            "device_id": self._device["device_id"],
            "device_status": {"state": "off"}
        })

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._client.device_service.set_state({
            "device_id": self._device["device_id"],
            "device_status": {"state": "stop"}
        })

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        position = kwargs["position"]
        logger.debug(f"async_set_cover_position: {position}")
        await self._client.device_service.set_state({
            "device_id": self._device["device_id"],
            "device_status": {"level": position}
        })

    async def update_state(self, new_status: dict):
        self._status.update(new_status)
        self.async_write_ha_state()

    async def reverse_motor(self):
        # 反转电机方向
        # home assistant 不支持此功能，仅做备忘
        await self._client.device_service.set_state({
            "device_id": self._device["device_id"],
            "device_status": {"reverse": "on"}
        })