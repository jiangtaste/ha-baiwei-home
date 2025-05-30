import json
import logging

from homeassistant import core
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .baiwei.const import DOMAIN, GatewayPlatform
from .baiwei.baiwei_entity import BaiweiEntity
from .baiwei.client import GatewayClient

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    devices, states = await client.get_devices(GatewayPlatform.IAS_ZONE)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"got motion sensor devices: {json.dumps(devices)}")
    logger.debug(f"got motion sensor states: {json.dumps(states)}")

    binary_sensors = []

    for device in devices:
        device_id = device.get("device_id")

        # 合并状态
        if device_id in states_map:
            logger.debug(f"{device_id}: {states_map[device_id]}")
            device["device_status"] = states_map[device_id]

        binary_sensors.append(BaiweiMotionSensor(client, device))

    async_add_entities(binary_sensors)


class BaiweiMotionSensor(BinarySensorEntity, BaiweiEntity):
    def __init__(self, gateway, device):
        super().__init__(gateway, device)

        self._attr_device_class = BinarySensorDeviceClass.MOTION

    @property
    def is_on(self):
        """Return True if motion is detected."""
        return self.status.get("status") == "on"
