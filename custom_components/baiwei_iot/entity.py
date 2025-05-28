from homeassistant.core import DOMAIN
from homeassistant.helpers.entity import Entity

from custom_components.baiwei_iot.const import GATEWAY_PLATFORM_MAP


class BaiweiEntity(Entity):

    def __init__(self, gateway, device: dict):
        self.gateway = gateway

        self.device = device
        self.device_id = device.get("device_id")
        self.endpoint = device.get("endpoint")
        self.status = device.get("device_status")

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

        self.gateway.device_service.register_entry(self.device_id, self)

    def _get_localized_name(self) -> str:
        name = self.device.get("product_name")

        return GATEWAY_PLATFORM_MAP.get(name, name)
