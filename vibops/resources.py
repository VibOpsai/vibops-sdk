"""Base resource with HTTP helpers and auto-retry."""

from __future__ import annotations

from typing import Any

import httpx

from vibops.exceptions import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    VibOpsError,
)

_RETRY_STATUSES = {502, 503}
_MAX_RETRIES = 1


def _raise_for_status(response: httpx.Response) -> None:
    """Translate HTTP errors into typed SDK exceptions."""
    if response.is_success:
        return

    try:
        body = response.json()
    except Exception:
        body = None

    message = body.get("detail", response.reason_phrase) if isinstance(body, dict) else response.reason_phrase
    status = response.status_code

    if status == 401:
        raise AuthenticationError(message, status_code=status, body=body)
    if status == 403:
        raise ForbiddenError(message, status_code=status, body=body)
    if status == 404:
        raise NotFoundError(message, status_code=status, body=body)
    if status == 422:
        raise ValidationError(message, status_code=status, body=body)
    if status == 429:
        raise RateLimitError(message, status_code=status, body=body)
    if status >= 500:
        raise ServerError(message, status_code=status, body=body)
    raise VibOpsError(message, status_code=status, body=body)


class Resource:
    """Base class for all API resources."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        """Send an HTTP request with auto-retry on 502/503."""
        url = f"/api/v1/{path}"
        last_response: httpx.Response | None = None

        for attempt in range(_MAX_RETRIES + 1):
            response = await self._http.request(method, url, params=params, json=json)
            if response.status_code not in _RETRY_STATUSES or attempt == _MAX_RETRIES:
                last_response = response
                break
            last_response = response

        assert last_response is not None
        _raise_for_status(last_response)

        if last_response.status_code == 204:
            return None
        return last_response.json()

    async def _get(self, path: str, **params: Any) -> Any:
        cleaned = {k: v for k, v in params.items() if v is not None}
        return await self._request("GET", path, params=cleaned or None)

    async def _post(self, path: str, *, json: Any | None = None) -> Any:
        return await self._request("POST", path, json=json)

    async def _delete(self, path: str, **params: Any) -> Any:
        cleaned = {k: v for k, v in params.items() if v is not None}
        return await self._request("DELETE", path, params=cleaned or None)

    async def _patch(self, path: str, *, json: Any | None = None) -> Any:
        return await self._request("PATCH", path, json=json)
