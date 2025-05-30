import logging

from .gateway import GatewayService

logger = logging.getLogger(__name__)

class RoomService:
    def __init__(self, gateway_service: GatewayService):
        self.gateway_service = gateway_service
        self._room_map = {}

    async def fetch_rooms(self):
        res = await self.gateway_service.send("room_mgmt/room_query", {})
        rooms = res.get("room_list")
        self._room_map = {room["id"]: room["name"] for room in rooms}

        return rooms


    async def get_room_name(self, room_id: int):
        self._room_map.get(room_id, "")