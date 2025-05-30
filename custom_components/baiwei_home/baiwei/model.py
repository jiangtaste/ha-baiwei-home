from typing import TypedDict, Optional


class Device(TypedDict):
    device_id: int
    product_id: int
    device_attr: str
    device_name: str
    room_id: int
    network_type: int
    create_time: str
    acoutside_id: int
    acgateway_id: int
    product_type: str
    product_name: str
    node_id: int
    endpoint: int
    address: int
    sn: str
    mac: str
    com: int
    node_type: int
    soft_ver: str
    hard_ver: str
    model: str

class CoverStatus(TypedDict):
    state: str  # 一般是 "on"/"off"
    level: int  # 一般是 1 (open), 0 (close), -1 (stop/unknown)