import logging

from .services.device import DeviceService
from .services.gateway import GatewayService
from .services.room import RoomService
from .services.scene import SceneService
from .services.user import UserService

logger = logging.getLogger(__name__)


class GatewayClient:
    def __init__(self):
        self.gateway_service = GatewayService()

        self.user_service = UserService(self.gateway_service)
        self.room_service = RoomService(self.gateway_service)
        self.device_service = DeviceService(self.gateway_service)
        self.scene_service = SceneService(self.gateway_service)



    async def discover(self, gateway_sn: str):
        # await self.gateway_service.connect(gateway_sn, self.device_service.sync_state)
        pass

    async def connect(self, host: str, port: int):
        await self.gateway_service.connect(host, port, self.device_service.sync_state)

    async def get_devices(self, platform: str):
        devices = await self.device_service.extract_devices(platform)
        states = await self.device_service.fetch_states(platform)
        return devices, states

