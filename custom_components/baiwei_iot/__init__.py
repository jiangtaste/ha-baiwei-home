from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .gateway.client import GatewayClient
from .const import DOMAIN, PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    serial_number = entry.data.get("serial_number")
    host = entry.data.get("host")
    port = entry.data.get("port")

    # 实例化并连接网关
    client = GatewayClient()

    await client.connect(host, port)
    await client.user_service.login()

    await client.device_service.get_devices_from_gateway()
    await client.room_service.get_rooms()
    await client.scene_service.get_scenes()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client


    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded