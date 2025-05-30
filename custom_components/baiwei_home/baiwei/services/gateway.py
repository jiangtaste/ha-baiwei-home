import logging
from typing import Callable, Awaitable

from ..connection import AsyncTcpClient, UDPBroadcastClient
from ..protocol import Protocol

logger = logging.getLogger(__name__)


class GatewayService:
    GATEWAY_PORT = 7102

    def __init__(self):
        self.gateway_list = []
        self.protocol = Protocol()
        self.udp_client = UDPBroadcastClient(self.GATEWAY_PORT)
        self.tcp_client = None
        self.report_handler = None

    async def discovery(self):
        request = self.protocol.pack("gateway_mgmt/gateway_discovery", {})
        results = await self.udp_client.broadcast(7103, request)

        for result in results:
            print(f"Discovered Gateway: {result}")
            payload = self.protocol.unpack(result)

            gateway = payload.get("baiwei", {})
            if not any(gw["sn"] == gateway.get("sn") for gw in self.gateway_list):
                self.gateway_list.append(gateway)

    async def connect(self, host: str, port: int, report_handler: Callable[[dict], Awaitable[None]]):
        # 关闭已存在链接
        if self.tcp_client is not None:
            await self.tcp_client.close()
            self.tcp_client = None

        # await self.discovery()

        # baiwei = next((item for item in self.gateway_list if item["sn"] == gateway_sn), None)

        # 获取到网关信息后，更新protocol
        # await self.protocol.update_gateway_sn(gateway_sn)

        # tcp_client = AsyncTcpClient(baiwei.get("ip"), baiwei.get("port"))

        tcp_client = AsyncTcpClient(host, port)
        await tcp_client.connect()
        await tcp_client.register_report_handler(self._report_handler)

        self.tcp_client = tcp_client
        self.report_handler = report_handler

    async def _report_handler(self, msg: dict):
        payload = self.protocol.unpack(msg)
        await self.report_handler(payload)

    async def send(self, path: str, payload: dict):
        if self.tcp_client:
            req_body = self.protocol.pack(path, payload)
            logger.debug(f"req: {req_body}")

            res = await self.tcp_client.send(req_body)
            res_body = self.protocol.unpack(res)
            logger.debug(f"res: {res_body}")

            return res_body
        else:
            raise "tcp client is None"

    async def update_token_from_response(self, res: dict):
        await self.protocol.update_token_from_response(res)

    async def permit_zb_join(self):
        return await self.send("gateway_mgmt/zb_net_open", {"msg_type": "set", "time": 10})

    async def stop_zb_join(self):
        return await self.send("gateway_mgmt/zb_net_open", {"msg_type": "set", "time": 0})
