import asyncio
import json
from collections import defaultdict

from typing import Callable, Awaitable

from ..consts import HEADER_SIZE, MAGIC
from ..utils import generate_request


class AsyncTcpClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self._response_futures = {}
        self._lock = asyncio.Lock()
        self._on_report = None
        self._response_buffers = defaultdict(list)  # msg_id -> list of partial messages
        self._response_end_flags = {}  # msg_id -> whether end received

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        asyncio.create_task(self._listen_response())

    async def _listen_response(self):
        try:
            while True:
                header = await self.reader.readexactly(HEADER_SIZE)
                header_magic, content_length_hex = header[:4], header[4:8]
                if header_magic != MAGIC:
                    print("Invalid header, skipped.")
                    continue

                try:
                    body_length = int(content_length_hex, 16) - HEADER_SIZE
                except ValueError:
                    print(f"Invalid content length: {content_length_hex}")
                    continue

                if body_length < 0:
                    print(f"Invalid body length: {body_length}")
                    continue

                body_bytes = await self.reader.readexactly(body_length)
                print(f"Received raw body: {body_bytes}")

                try:
                    message = json.loads(body_bytes.decode("utf-8"))
                except json.JSONDecodeError as e:
                    print("Failed to decode JSON:", e)
                    continue

                msg_id = message.get("msg_id")
                if msg_id is None:
                    print("Received message without msg_id:", message)
                    continue

                # 判断是否为中间响应（是否是聚合响应的一部分）
                is_end = message.get("end", 1) == 1

                # 多次响应合并逻辑
                self._response_buffers[msg_id].append(message)

                if is_end:
                    result = self._merge_multipart_messages(msg_id)
                    self._response_end_flags.pop(msg_id, None)
                    future = self._response_futures.pop(msg_id, None)
                    if future:
                        future.set_result(result)
                    elif self._on_report:
                        await self._on_report(result)
                    else:
                        print(f"Unmatched response: {result}")
                else:
                    self._response_end_flags[msg_id] = False


        except asyncio.TimeoutError:
            print("Connection closed by server")
        except Exception as e:
            print("Error receiving data:", e)

    def _merge_multipart_messages(self, msg_id: str) -> dict:
        messages = self._response_buffers.pop(msg_id, [])
        if not messages:
            return {}

        if len(messages) == 1:
            return messages[0]

        # 以第一条为模板
        merged = dict(messages[0])

        # 动态识别在 messages 中实际存在的 list 类型字段
        list_fields = set()
        for msg in messages:
            for key, value in msg.items():
                if isinstance(value, list):
                    list_fields.add(key)

        # 合并所有实际存在的 list 字段
        for field in list_fields:
            merged[field] = []
            for msg in messages:
                if field in msg:
                    merged[field].extend(msg[field])

        # 删除 end 字段
        merged.pop("end", None)

        return merged

    async def register_report_handler(self, handler: Callable[[dict], Awaitable[None]]):
        self._on_report = handler

    async def send(self, data: dict, timeout: float = 10):
        msg_id, raw = generate_request(data)

        future = asyncio.get_event_loop().create_future()
        async with self._lock:
            self._response_futures[msg_id] = future
            self.writer.write(raw)
            await self.writer.drain()

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            self._response_futures.pop(msg_id, None)
            raise TimeoutError(f"Response {msg_id} timed out")

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
