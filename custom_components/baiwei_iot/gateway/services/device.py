import json
import logging
from itertools import chain

from homeassistant.components.ios import devices

from .gateway import GatewayService

logger = logging.getLogger(__name__)


class DeviceService:
    def __init__(self, gateway_service: GatewayService):
        self.gateway_service = gateway_service
        self._devices = {}
        self._states = {}

        self._entity_map = {}  # device_id -> home assistant entity

    async def get_devices_from_gateway(self):
        res = await self.gateway_service.send("device_mgmt/device_query", {})
        self._devices = res["type_list"]

    async def extract_devices(self, platform: str):
        logger.debug(f"{platform}, {self._devices}")
        # {
        #         "device_id": 14,
        #         "product_id": 8,
        #         "device_attr": "Light",
        #         "device_name": "\u4e3b\u706f",
        #         "room_id": 3,
        #         "network_type": 0,
        #         "create_time": "2025-03-29 16:16:57",
        #         "acoutside_id": -1,
        #         "acgateway_id": -1,
        #         "product_type": "On/Off Light",
        #         "product_name": "On/Off Light",
        #         "node_id": 40067,
        #         "endpoint": 1,
        #         "address": 0,
        #         "sn": "304a2656b37e",
        #         "mac": "CCCCCCFFFEA25984",
        #         "com": 0,
        #         "node_type": 0,
        #         "soft_ver": "41",
        #         "hard_ver": "01",
        #         "model": "LG344"
        #     }
        device_lists = [
            device["device_list"]
            for device in self._devices
            if device.get("product_type") == platform and "device_list" in device
        ]

        # 用 itertools.chain.from_iterable 把二维列表展平为一维列表
        flattened_list = list(chain.from_iterable(device_lists))

        return flattened_list

    async def fetch_states(self, platform: str):
        # AC gateway
        # Air Box
        # BW Cateye
        # Floor heat controller
        # IAS Zone
        # New wind controller
        # On/Off Light
        # On/Off Switch 双开遥控
        # Scene Selector
        # Window Covering Device
        res = await self.gateway_service.send("control_mgmt/device_state_get", {"device": {"type": platform}})
        states = res["device_list"]
        logger.debug("device states", json.dumps(states))
        return states

    async def get_state(self, device_id: str):
        # "AC gateway"
        # "Air Box"
        # "BW Cateye"
        return self._states.get(device_id)

    async def set_state(self, device: dict):
        state = await self.gateway_service.send("control_mgmt/device_control", {"msg_type": "set", "device": device})

        # 同步本地状态缓存
        await self.sync_state(state)

    async def sync_state(self, state: dict):
        try:
            device = state["device"]
            device_id = device["device_id"]
            device_status = device["device_status"]
            self._states[device_id] = device_status
            logger.debug(f"Device States: {self._states}")

            # 更新 entry status
            entity = self._entity_map[device_id]
            if entity:
                await entity.update_state(device_status)
        except (TypeError, KeyError) as e:
            # 可以加入日志记录
            logger.error(e)

    def register_entry(self, device_id: int, entity):
        self._entity_map[device_id] = entity
