import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import async_get as async_get_area_registry

from .gateway.client import GatewayClient
from .const import DOMAIN, PLATFORMS


logger = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    serial_number = entry.data.get("serial_number")
    host = entry.data.get("host")
    port = entry.data.get("port")

    # 实例化并连接网关
    client = GatewayClient()

    await client.connect(host, port)
    await client.user_service.login()

    await client.device_service.get_devices_from_gateway()



    await client.scene_service.get_scenes()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    # setup areas
    rooms = await client.room_service.fetch_rooms()
    area_registry = async_get_area_registry(hass)
    for room in rooms:
        area_registry.async_get_or_create(room.get("name"))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)





    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
