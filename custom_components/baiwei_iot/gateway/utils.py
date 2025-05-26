import itertools
import json
import struct

from .consts import MAGIC, HEADER_SIZE, MSG_ID_PREFIX

_msg_counter = itertools.count(1)


def next_msg_id(prefix=None):
    return f"{prefix}-{next(_msg_counter):03}"


def generate_request(data: dict):
    msg_id = next_msg_id(MSG_ID_PREFIX)
    data["msg_id"] = msg_id

    body = json.dumps(data).encode("utf-8")
    header = MAGIC + struct.pack(">H", len(body) + HEADER_SIZE).hex().upper().encode("utf-8")

    request_data = header + body
    return msg_id, request_data
