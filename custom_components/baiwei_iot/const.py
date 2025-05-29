from enum import Enum

DOMAIN = "baiwei_iot"

PLATFORMS = [
    "switch",
    "climate",
    "cover",
    "fan",
    "button",
    "sensor",
    "binary_sensor",
]


class GatewayPlatform(str, Enum):
    ON_OFF_LIGHT = "On/Off Light"
    AC_GATEWAY = "AC gateway"
    AIR_BOX = "Air Box"
    BW_CATEYE = "BW Cateye"
    FLOOR_HEAT = "Floor heat controller"
    IAS_ZONE = "IAS Zone"
    NEW_WIND = "New wind controller"
    ON_OFF_SWITCH = "On/Off Switch"
    SCENE_SELECTOR = "Scene Selector"
    WINDOW_COVER = "Window Covering Device"


GATEWAY_PLATFORM_MAP = {
    "On/Off Switch": "开关",
    "On/Off Light": "灯光",
    "AC gateway": "中央空调网关",
    "Air Box": "空气盒子",
    "BW Cateye": "猫眼",
    "Floor heat controller": "地暖控制器",
    "IAS Zone": "人体移动检测",
    "New wind controller": "新风控制器",
    "Scene Selector": "场景控制器",
    "Window Covering Device": "窗帘控制器",
}
