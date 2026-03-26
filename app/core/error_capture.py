"""
Central place to record errors: structured logging today, Sentry/Datadog tomorrow.

Call `capture_exception` from exception handlers or middleware so all failures
go through one pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request

_logger = logging.getLogger("app.errors")


def _request_summary(request: Request | None) -> str:
    if request is None:
        return "request=unknown"
    client = request.client.host if request.client else "-"
    return f"{request.method} {request.url.path} client={client}"


def capture_exception(
    exc: BaseException,
    request: Request | None,
    *,
    expected: bool,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Log an exception with HTTP context.

    :param expected: True for client/domain errors (4xx-style); False for bugs/unhandled.
    """
    msg = f"{_request_summary(request)} | {type(exc).__name__}: {exc}"
    if extra:
        msg = f"{msg} | {extra}"

    if expected:
        _logger.warning(msg)
        _hook_optional_monitoring(exc, request, expected=True)
        return

    _logger.error(msg, exc_info=exc)
    _hook_optional_monitoring(exc, request, expected=False)


def _hook_optional_monitoring(
    exc: BaseException,
    request: Request | None,
    *,
    expected: bool,
) -> None:
    """Reserved for Sentry, OpenTelemetry, etc."""
    _ = (exc, request, expected)
