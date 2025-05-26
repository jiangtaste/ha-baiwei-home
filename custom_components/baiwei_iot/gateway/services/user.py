from .gateway import GatewayService


class UserService:
    def __init__(self, gateway_service: GatewayService):
        self.gateway_service = gateway_service

    async def login(self):
        res = await self.gateway_service.send("user_mgmt/user_login", {"user": {"appId": "010", "user_pwd": "888888"}})
        await self.gateway_service.update_token_from_response(res)
