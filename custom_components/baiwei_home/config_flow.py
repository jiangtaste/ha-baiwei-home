from homeassistant import config_entries
import voluptuous as vol

from .baiwei.const import DOMAIN

# 可选语言列表
LANGUAGES = {
    "zh": "中文",
    "en": "English",
}


class BaiweiHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Baiwei Home."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title="Baiwei Home",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("port"): int,
                vol.Optional("serial_number"): str,
                vol.Optional("language", default="zh"): vol.In(LANGUAGES),
            }),
            errors=errors,
        )
