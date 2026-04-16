"""MiKiLED custom integration for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .api import MikiledApi
from .const import DOMAIN
from .coordinator import MikiledCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MiKiLED from a config entry."""
    host = entry.data[CONF_HOST]
    port = int(entry.data[CONF_PORT])
    session = aiohttp_client.async_get_clientsession(hass)
    api = MikiledApi(session, host, port)
    coordinator = MikiledCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
