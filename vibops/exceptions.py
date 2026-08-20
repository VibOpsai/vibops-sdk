"""VibOps SDK exceptions."""

from __future__ import annotations

__all__ = [
    "AuthenticationError",
    "ConflictError",
    "ConnectionError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
    "VibOpsError",
]


class VibOpsError(Exception):
    """Base exception for all VibOps SDK errors."""

    def __init__(
        self, message: str, status_code: int | None = None,
        body: dict | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class AuthenticationError(VibOpsError):
    """Raised on 401 Unauthorized."""


class ForbiddenError(VibOpsError):
    """Raised on 403 Forbidden."""


class NotFoundError(VibOpsError):
    """Raised on 404 Not Found."""


class ConflictError(VibOpsError):
    """Raised on 409 Conflict."""


class ValidationError(VibOpsError):
    """Raised on 422 Validation Error."""


class RateLimitError(VibOpsError):
    """Raised on 429 Too Many Requests."""


class ServerError(VibOpsError):
    """Raised on 5xx after retries are exhausted."""


class ConnectionError(VibOpsError):
    """Raised when the SDK cannot connect to the VibOps server."""


class TimeoutError(VibOpsError):
    """Raised when a request to the VibOps server times out."""
