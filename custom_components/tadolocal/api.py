"""Thin async client for the TadoLocal REST API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class TadoLocalError(Exception):
    """Base error for TadoLocal API."""


class TadoLocalConnectionError(TadoLocalError):
    """Could not reach the TadoLocal bridge."""


class TadoLocalAuthError(TadoLocalError):
    """API key rejected by the TadoLocal bridge."""


class TadoLocalApi:
    """Client for the TadoLocal REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        api_key: str | None = None,
        timeout: int = 15,
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"
        self._api_key = api_key or None
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    @property
    def base_url(self) -> str:
        return self._base

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base}{path}"
        if params:
            # FastAPI expects lowercase booleans in query strings
            params = {
                k: (str(v).lower() if isinstance(v, bool) else v)
                for k, v in params.items()
                if v is not None
            }
        try:
            async with self._session.request(
                method,
                url,
                params=params,
                headers=self._headers(),
                timeout=self._timeout,
            ) as resp:
                if resp.status == 401:
                    raise TadoLocalAuthError("Invalid or missing API key")
                if resp.status >= 400:
                    text = await resp.text()
                    raise TadoLocalError(
                        f"{method} {path} failed with HTTP {resp.status}: {text}"
                    )
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise TadoLocalConnectionError(
                f"Error communicating with TadoLocal at {self._base}: {err}"
            ) from err

    async def get_status(self) -> dict[str, Any]:
        return await self._request("GET", "/status")

    async def get_zones(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/zones")
        return data.get("zones", []) if isinstance(data, dict) else []

    async def get_devices(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/devices")
        return data.get("devices", []) if isinstance(data, dict) else []

    async def set_zone(
        self,
        zone_id: int,
        temperature: float | None = None,
        heating_enabled: bool | None = None,
    ) -> dict[str, Any]:
        """Control a zone via its leader device.

        temperature: target in °C. 0 disables heating, -1 enables heating while
        keeping the stored setpoint.
        """
        return await self._request(
            "POST",
            f"/zones/{zone_id}/set",
            params={"temperature": temperature, "heating_enabled": heating_enabled},
        )

    async def set_device(
        self,
        device_id: int,
        temperature: float | None = None,
        heating_enabled: bool | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/devices/{device_id}/set",
            params={"temperature": temperature, "heating_enabled": heating_enabled},
        )

    async def refresh(self) -> dict[str, Any]:
        return await self._request("POST", "/refresh")
