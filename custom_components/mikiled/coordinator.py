"""Data update coordinator for MiKiLED."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MikiledApi
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class MikiledDeviceData:
    """Cached JSON payloads from the device."""

    status: dict[str, Any] | None
    version: dict[str, Any] | None
    sensors: dict[str, Any] | None


class MikiledCoordinator(DataUpdateCoordinator[MikiledDeviceData]):
    """Polls status, version, and sensors in parallel."""

    def __init__(self, hass: HomeAssistant, api: MikiledApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> MikiledDeviceData:
        status_c, version_c, sensors_c = await asyncio.gather(
            self.api.get_status(),
            self.api.get_version(),
            self.api.get_sensors(),
            return_exceptions=True,
        )

        status = status_c if isinstance(status_c, dict) else None
        version = version_c if isinstance(version_c, dict) else None
        sensors = sensors_c if isinstance(sensors_c, dict) else None

        if isinstance(status_c, BaseException):
            _LOGGER.warning("Status update failed: %s", status_c)
        if isinstance(version_c, BaseException):
            _LOGGER.warning("Version update failed: %s", version_c)
        if isinstance(sensors_c, BaseException):
            _LOGGER.warning("Sensors update failed: %s", sensors_c)

        if status is None and version is None and sensors is None:
            raise UpdateFailed("All MiKiLED API requests failed")

        return MikiledDeviceData(status=status, version=version, sensors=sensors)
