import asyncio
import json
from typing import Callable, List, Optional

from ..consts import HEADER_SIZE
from ..connection.tcp_client import MAGIC
from ..utils import generate_request


class UDPBroadcastClient(asyncio.DatagramProtocol):
    def __init__(self, local_port: int = 0):
        self.local_port = local_port
        self.transport = None
        self.loop = asyncio.get_event_loop()
        self.on_response: Callable[[dict, tuple], None] = lambda msg, addr: None

        self._response_fut: Optional[asyncio.Future] = None
        self._response_list: List[dict] = []

    async def start(self):
        self.transport, _ = await self.loop.create_datagram_endpoint(
            lambda: self,
            local_addr=("0.0.0.0", self.local_port),
            allow_broadcast=True
        )

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        header_magic, content_length_hex, body = data[:4], data[4:8], data[8:]

        if len(data) < HEADER_SIZE or header_magic != MAGIC:
            print(f"Ignored invalid packet from {addr}")
            return

        body_length = len(body)
        content_length = int(content_length_hex, 16)
        if body_length != content_length - HEADER_SIZE:
            print(f"Invalid Content-Length, expected {content_length}, got {body_length}")
            return

        try:
            message = json.loads(body.decode("utf-8"))

            if self._response_fut is not None and not self._response_fut.done():
                self._response_list.append(message)
            else:
                self.on_response(message, addr)

        except Exception as e:
            print(f"Failed to parse JSON from {addr}: {e}")

    async def broadcast(self, port: int, message: dict, timeout=1):
        self._response_list.clear()
        self._response_fut = self.loop.create_future()

        await self.start()
        _, request_data = generate_request(message)
        self.transport.sendto(request_data, ("255.255.255.255", port))

        try:
            await asyncio.wait_for(self._response_fut, timeout)
        except asyncio.TimeoutError:
            pass
        finally:
            self.close()

        return self._response_list

    def close(self):
        if self.transport:
            self.transport.close()
