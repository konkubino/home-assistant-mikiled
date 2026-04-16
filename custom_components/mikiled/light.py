"""Light platform for MiKiLED day and night profiles."""

from __future__ import annotations

import logging
from typing import Any, Literal

import aiohttp
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import MikiledApiError
from .const import DOMAIN
from .coordinator import MikiledCoordinator, MikiledDeviceData
from .validators import is_safe_hex_color

_LOGGER = logging.getLogger(__name__)


def _normalize_hex(value: str | None, fallback: str) -> str:
    raw = (value or fallback).lstrip("#").upper()
    if not is_safe_hex_color(raw):
        fb = fallback.lstrip("#").upper()
        return fb if is_safe_hex_color(fb) else "FFFFFF"
    return raw


def _hex_to_rgb(hex_no_hash: str) -> tuple[int, int, int]:
    if not is_safe_hex_color(hex_no_hash):
        hex_no_hash = "FFFFFF"
    return (
        int(hex_no_hash[0:2], 16),
        int(hex_no_hash[2:4], 16),
        int(hex_no_hash[4:6], 16),
    )


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = (max(0, min(255, int(x))) for x in rgb)
    return f"{r:02X}{g:02X}{b:02X}"


def _pct_from_brightness(brightness: int | None) -> int:
    if brightness is None:
        return 100
    return max(0, min(100, round(brightness * 100 / 255)))


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Register day and night lights."""
    coordinator: MikiledCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            MikiledProfileLight(coordinator, config_entry, "day"),
            MikiledProfileLight(coordinator, config_entry, "night"),
        ],
        update_before_add=False,
    )


class MikiledProfileLight(CoordinatorEntity[MikiledCoordinator], LightEntity):
    """Controls day or night color and brightness on the device."""

    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(
        self,
        coordinator: MikiledCoordinator,
        config_entry: ConfigEntry,
        profile: Literal["day", "night"],
    ) -> None:
        super().__init__(coordinator)
        self._profile = profile
        self._attr_unique_id = f"{config_entry.entry_id}_{profile}_light"
        self._attr_has_entity_name = False
        self._attr_name = "Day" if profile == "day" else "Night"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="MiKiLED",
            model="MiKiLED Controller",
            configuration_url=f"http://{coordinator.api.host}:{coordinator.api.port}/",
        )

    @property
    def color_mode(self) -> ColorMode | None:
        if self.is_on:
            return ColorMode.RGB
        return None

    @property
    def is_on(self) -> bool:
        colors = (self.coordinator.data.status or {}).get("colors") or {}
        if self._profile == "day":
            return int(colors.get("dayBrightness", 0) or 0) > 0
        return int(colors.get("nightBrightness", 0) or 0) > 0

    @property
    def brightness(self) -> int | None:
        if not self.is_on:
            return None
        colors = (self.coordinator.data.status or {}).get("colors") or {}
        if self._profile == "day":
            pct = int(colors.get("dayBrightness", 0) or 0)
        else:
            pct = int(colors.get("nightBrightness", 0) or 0)
        return round(pct * 255 / 100)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        colors = (self.coordinator.data.status or {}).get("colors") or {}
        if self._profile == "day":
            hx = _normalize_hex(str(colors.get("day", "")), "FF934C")
        else:
            hx = _normalize_hex(str(colors.get("night", "")), "000066")
        return _hex_to_rgb(hx)

    async def async_turn_on(self, **kwargs: Any) -> None:
        data: MikiledDeviceData = self.coordinator.data
        colors = (data.status or {}).get("colors") or {}
        if self._profile == "day":
            default_hex = _normalize_hex(str(colors.get("day", "")), "FF934C")
            bri_key = "dayBrightness"
            setter = self.coordinator.api.set_day_color
        else:
            default_hex = _normalize_hex(str(colors.get("night", "")), "000066")
            bri_key = "nightBrightness"
            setter = self.coordinator.api.set_night_color

        rgb_in = kwargs.get(ATTR_RGB_COLOR)
        if rgb_in is not None:
            if (
                not isinstance(rgb_in, (tuple, list))
                or len(rgb_in) != 3
                or not all(isinstance(x, int) for x in rgb_in)
            ):
                hex_out = default_hex
            else:
                hex_out = _rgb_to_hex((rgb_in[0], rgb_in[1], rgb_in[2]))
        else:
            hex_out = default_hex

        if kwargs.get(ATTR_BRIGHTNESS) is not None:
            pct = _pct_from_brightness(int(kwargs[ATTR_BRIGHTNESS]))
            if pct == 0:
                await self.async_turn_off()
                return
        elif self.is_on:
            pct = int(colors.get(bri_key, 100) or 100)
        else:
            pct = 100

        pct = max(1, min(100, pct))

        try:
            await setter(color_hex=hex_out, brightness_pct=pct)
        except (MikiledApiError, aiohttp.ClientError, TimeoutError, OSError) as err:
            _LOGGER.error("Failed to set %s color on MiKiLED: %s", self._profile, err)
            raise
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        data: MikiledDeviceData = self.coordinator.data
        colors = (data.status or {}).get("colors") or {}
        try:
            if self._profile == "day":
                hx = _normalize_hex(str(colors.get("day", "")), "FF934C")
                await self.coordinator.api.set_day_color(color_hex=hx, brightness_pct=0)
            else:
                hx = _normalize_hex(str(colors.get("night", "")), "000066")
                await self.coordinator.api.set_night_color(color_hex=hx, brightness_pct=0)
        except (MikiledApiError, aiohttp.ClientError, TimeoutError, OSError) as err:
            _LOGGER.error("Failed to turn off %s on MiKiLED: %s", self._profile, err)
            raise
        await self.coordinator.async_request_refresh()
