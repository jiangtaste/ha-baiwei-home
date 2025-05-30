from enum import Enum

DOMAIN = "baiwei_home"

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
    AC_GATEWAY = "AC baiwei"
    AIR_BOX = "Air Box"
    BW_CATEYE = "BW Cateye"
    FLOOR_HEAT = "Floor heat controller"
    IAS_ZONE = "IAS Zone"
    NEW_WIND = "New wind controller"
    ON_OFF_SWITCH = "On/Off Switch"
    SCENE_SELECTOR = "Scene Selector"
    WINDOW_COVER = "Window Covering Device"



