"""Base resource with HTTP helpers and auto-retry."""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

import httpx

from vibops.exceptions import (
    AuthenticationError,
    ConflictError,
    ConnectionError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
    VibOpsError,
)

__all__ = ["Resource"]

_RETRY_STATUSES = {429, 502, 503}
_DEFAULT_MAX_RETRIES = 2
_BACKOFF_BASE = 0.5  # seconds


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
    if status == 409:
        raise ConflictError(message, status_code=status, body=body)
    if status == 422:
        raise ValidationError(message, status_code=status, body=body)
    if status == 429:
        raise RateLimitError(message, status_code=status, body=body)
    if status >= 500:
        raise ServerError(message, status_code=status, body=body)
    raise VibOpsError(message, status_code=status, body=body)


class Resource:
    """Base class for all API resources."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        *,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        retry_statuses: set[int] | None = None,
    ) -> None:
        self._http = http
        self._max_retries = max_retries
        self._retry_statuses = retry_statuses if retry_statuses is not None else _RETRY_STATUSES

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send an HTTP request with auto-retry on retryable status codes.

        When a 429 response includes a ``Retry-After`` header, that value is
        used as the sleep duration instead of exponential backoff.
        """
        url = f"/api/v1/{path}"
        last_response: httpx.Response | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = await self._http.request(
                    method, url, params=params, json=json, timeout=timeout,
                )
            except httpx.ConnectError:
                base_url = str(self._http.base_url)
                raise ConnectionError(
                    f"Cannot connect to VibOps at {base_url}",
                ) from None
            except (httpx.TimeoutException, httpx.ReadTimeout):
                raise TimeoutError("Request timed out") from None

            if response.status_code not in self._retry_statuses or attempt == self._max_retries:
                last_response = response
                break

            # Respect Retry-After header on 429, otherwise exponential backoff
            if response.status_code == 429 and response.headers.get("retry-after"):
                try:
                    delay = float(response.headers["retry-after"])
                except (ValueError, TypeError):
                    delay = _BACKOFF_BASE * (2 ** attempt)
            else:
                delay = _BACKOFF_BASE * (2 ** attempt)

            await asyncio.sleep(delay)
            last_response = response

        if last_response is None:
            raise ServerError("No response received after retries", status_code=502)
        _raise_for_status(last_response)

        if last_response.status_code == 204:
            return None
        return last_response.json()

    async def _get(self, path: str, **params: Any) -> Any:
        cleaned = {k: v for k, v in params.items() if v is not None}
        return await self._request("GET", path, params=cleaned or None)

    async def _post(self, path: str, *, json: Any | None = None) -> Any:
        return await self._request("POST", path, json=json)

    async def _put(self, path: str, *, json: Any | None = None) -> Any:
        return await self._request("PUT", path, json=json)

    async def _delete(self, path: str, **params: Any) -> Any:
        cleaned = {k: v for k, v in params.items() if v is not None}
        return await self._request("DELETE", path, params=cleaned or None)

    async def _patch(self, path: str, *, json: Any | None = None) -> Any:
        return await self._request("PATCH", path, json=json)

    async def _paginate(self, path: str, limit: int = 100, **params: Any) -> AsyncIterator[dict[str, Any]]:
        """Auto-paginating async generator."""
        offset = 0
        while True:
            data = await self._get(path, limit=limit, offset=offset, **params)
            items = data if isinstance(data, list) else data.get("items", [])
            if not items:
                break
            for item in items:
                yield item
            if len(items) < limit:
                break
            offset += limit
