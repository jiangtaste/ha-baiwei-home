from .gateway import GatewayService


class SceneService:
    def __init__(self, gateway_service: GatewayService):
        self.gateway_service = gateway_service
        self._scenes = {}

    async def get_scenes(self):
        scenes = await self.gateway_service.send("scene_mgmt/scene_query", {})
        self._scenes = scenes
