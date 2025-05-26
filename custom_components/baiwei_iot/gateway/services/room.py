from .gateway import GatewayService


class RoomService:
    def __init__(self, gateway_service: GatewayService):
        self.gateway_service = gateway_service
        self._rooms = {}

    async def get_rooms(self):
        rooms = await self.gateway_service.send("room_mgmt/room_query", {})
        self._rooms = rooms
