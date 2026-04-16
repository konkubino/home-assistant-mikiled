"""Async HTTP client for MiKiLED devices."""

from __future__ import annotations

import json
from typing import Any

import aiohttp
from yarl import URL

from .const import API_SENSORS, API_STATUS, API_VERSION, SET_DAY_COLOR, SET_NIGHT_COLOR


class MikiledApiError(Exception):
    """Raised when the device returns an error or unexpected payload."""


class MikiledApi:
    """Minimal client for MiKiLED HTTP API (see MiKiLED docs/API.md)."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
    ) -> None:
        self._session = session
        self._base = URL.build(scheme="http", host=host, port=port)

    @property
    def host(self) -> str:
        """Configured hostname or IP."""
        return self._base.host  # type: ignore[no-any-return]

    @property
    def port(self) -> int:
        """Configured TCP port."""
        return self._base.port or 80

    async def get_version(self) -> dict[str, Any]:
        return await self._get_json(API_VERSION)

    async def get_status(self) -> dict[str, Any]:
        return await self._get_json(API_STATUS)

    async def get_sensors(self) -> dict[str, Any]:
        return await self._get_json(API_SENSORS)

    async def set_day_color(self, *, color_hex: str, brightness_pct: int) -> None:
        await self._post_form(
            SET_DAY_COLOR,
            {"dayColor": color_hex, "dayBrightness": str(brightness_pct)},
        )

    async def set_night_color(self, *, color_hex: str, brightness_pct: int) -> None:
        await self._post_form(
            SET_NIGHT_COLOR,
            {"nightColor": color_hex, "nightBrightness": str(brightness_pct)},
        )

    def _url(self, path: str) -> URL:
        if not path.startswith("/"):
            path = f"/{path}"
        return self._base.with_path(path)

    async def _get_json(self, path: str) -> dict[str, Any]:
        url = self._url(path)
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            body = await resp.text()
            if resp.status >= 400:
                raise MikiledApiError(f"HTTP {resp.status} for {path}: {body[:200]}")
            try:
                data = json.loads(body)
            except json.JSONDecodeError as err:
                raise MikiledApiError(f"Invalid JSON from {path}: {body[:200]}") from err
            if not isinstance(data, dict):
                raise MikiledApiError(f"Unexpected JSON type from {path}")
            return data

    async def _post_form(self, path: str, data: dict[str, str]) -> None:
        url = self._url(path)
        async with self._session.post(
            url,
            data=data,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise MikiledApiError(f"HTTP {resp.status} for {path}: {text[:200]}")
