from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

DATA_SCHEMA = vol.Schema({
    vol.Required("host"): str,
    vol.Required("port"): str,
})


class MyComponentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for My Component."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # 你可以在这里添加校验 host/port/serial_number 的逻辑
            return self.async_create_entry(
                title=f"君启智家网关",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("serial_number"): str,
                vol.Required("host"): str,
                vol.Required("port"): int,
            }),
            errors=errors,
        )
