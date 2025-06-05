import logging

from homeassistant.helpers.entity import Entity

from .const import DOMAIN

logger = logging.getLogger(__name__)

GATEWAY_PLATFORM_MAP = {
    "On/Off Switch": "开关",
    "On/Off Light": "灯光",
    "AC gateway": "中央空调网关",
    "Air Box": "空气盒子",
    "BW Cateye": "猫眼",
    "Floor heat controller": "地暖控制器",
    "IAS Zone": "人体移动检测",
    "New wind controller": "新风控制器",
    "Scene Selector": "场景控制器",
    "Window Covering Device": "窗帘控制器",
}


class BaiweiEntity(Entity):

    def __init__(self, gateway, device: dict):
        self.gateway = gateway

        self.device = device
        self.device_id = device.get("device_id")
        self.endpoint = device.get("endpoint")
        self._status = device.get("device_status")

        self._attr_name = device.get("device_name") or device.get("product_name")
        self._attr_unique_id = f"baiwei_{self.device_id}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(device.get("mac")))},
            "name": self._get_localized_name(),
            "manufacturer": "Baiwei",
            "model": device.get("model"),
            "sw_version": device.get("soft_ver"),
            "hw_version": device.get("hard_ver"),
        }

    async def async_added_to_hass(self):
        self.gateway.device_service.register_entry(self.device_id, self)

    def _get_localized_name(self) -> str:
        name = self.device.get("product_name")

        return GATEWAY_PLATFORM_MAP.get(name, name)

    def update_status(self, status: dict):
        self._status.update(status)
        self.async_write_ha_state()