"""Config flow for MiKiLED."""

from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import aiohttp_client

from .api import MikiledApi, MikiledApiError
from .const import DEFAULT_PORT, DOMAIN
from .validators import validate_mikiled_host, validate_mikiled_port


def _user_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST): vol.All(vol.Coerce(str), validate_mikiled_host),
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                vol.Coerce(int), validate_mikiled_port
            ),
        }
    )


class MikiledConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a UI-based setup of a MiKiLED device."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Ask for host and port, then validate with /api/version."""
        errors: dict[str, str] = {}
        schema = _user_schema()

        if user_input is not None:
            try:
                user_input = schema(user_input)
            except vol.MultipleInvalid as exc:
                for err in exc.errors:
                    key = err.path[0] if err.path else "base"
                    errors[str(key)] = str(err.msg)
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors=errors
                )

            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            session = aiohttp_client.async_get_clientsession(self.hass)
            api = MikiledApi(session, host, port)
            try:
                version = await api.get_version()
            except (MikiledApiError, aiohttp.ClientError, TimeoutError, OSError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()

                title = f"MiKiLED {host}"
                if isinstance(version, dict) and version.get("version"):
                    title = f"MiKiLED {version['version']} ({host})"
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
