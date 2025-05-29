import json
import logging

from homeassistant import core
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION, CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, PERCENTAGE, \
    UnitOfTemperature
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, GatewayPlatform
from .baiwei_entity import BaiweiEntity
from .gateway.client import GatewayClient

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: GatewayClient = hass.data[DOMAIN][entry.entry_id]

    devices, states = await client.get_devices(GatewayPlatform.AIR_BOX)
    # 构建一个 device_id -> device_status 的快速查找字典
    states_map = {state["device_id"]: state["device_status"] for state in states}

    logger.debug(f"got air box sensor devices: {json.dumps(devices)}")
    logger.debug(f"got air box sensor states: {json.dumps(states)}")

    sensors = []

    for device in devices:
        device_id = device.get("device_id")

        # 合并状态
        if device_id in states_map:
            logger.debug(f"{device_id}: {states_map[device_id]}")
            device["device_status"] = states_map[device_id]

        # 添加传感器实体
        sensors.extend([
            BaiweiAirBoxSensor("二氧化碳", CONCENTRATION_PARTS_PER_MILLION, "co2", client, device),
            BaiweiAirBoxSensor("PM2.5", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, "pm25", client, device),
            BaiweiAirBoxSensor("温度", UnitOfTemperature.CELSIUS, "temp", client, device),
            BaiweiAirBoxSensor("湿度", PERCENTAGE, "hum", client, device),
        ])

    async_add_entities(sensors)


class BaiweiAirBoxSensor(SensorEntity, BaiweiEntity):
    def __init__(self, name, unit, key, gateway, device):
        super().__init__(gateway, device)

        self._attr_name = name
        self._key = key
        self._attr_unique_id = f"baiwei_{self.device_id}_{self._key}"
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        raw = self.status.get(self._key)
        if self._key == "temp":
            return raw / 100
        elif self._key == "hum":
            return raw / 100
        return raw
