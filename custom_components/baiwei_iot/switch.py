import json
import logging
from typing import Any

from homeassistant import core
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .gateway.client import GatewayClient

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    devices, states = await client.get_devices("On/Off Light")
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"get switch devices: {json.dumps(devices)}")
    logger.debug(f"get switch states: {json.dumps(states)}")

    switches = []
    for device in devices:
        device_id = device.get("device_id")
        if device_id in states_map:
            logger.debug(f"{device_id}: {states_map[device_id]}")
            device["device_status"] = states_map[device_id]
        switches.append(JQSwitch(client, device))

    async_add_entities(switches)


class JQSwitch(SwitchEntity):
    def __init__(self, client, device):
        self._client = client
        self._device = device

        # 唯一ID，建议使用设备唯一标识，防止重复
        self._attr_unique_id = str(self._device["device_id"])

        # 设备名称
        self._attr_name = self._device["device_name"] or self._device["product_name"]

        self._is_on = self._device["device_status"]["state"] == "on"

        # 其他属性
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.get("mac"))},
            "name": f"智能开关 {device.get("model")}",
            "model": device.get("model"),
            "manufacturer": "Baiwei",  # 根据实际填写
            "sw_version": device.get("soft_ver"),
            "hw_version": device.get("hard_ver"),
        }

        self._client.device_service.register_entry(self._device["device_id"], self)

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._client.device_service.set_state({
            "device_id": self._device["device_id"],
            "device_status": {
                "state": "on"
            }
        })

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.device_service.set_state({
            "device_id": self._device["device_id"],
            "device_status": {
                "state": "off"
            }
        })

    async def update_state(self, new_status: dict):
        self._is_on = new_status.get("state") == "on"
        self.async_write_ha_state()