"""
RFC 7807 — Problem Details for HTTP APIs.

https://www.rfc-editor.org/rfc/rfc7807
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

MEDIA_TYPE_PROBLEM_JSON = "application/problem+json"

# Stable identifiers for clients (URIs need not resolve; they identify problem types).
TYPE_NOT_FOUND = "urn:expenses:problem:not-found"
TYPE_VALIDATION = "urn:expenses:problem:validation"
TYPE_REQUEST_VALIDATION = "urn:expenses:problem:request-validation"
TYPE_CONFLICT = "urn:expenses:problem:conflict"
TYPE_INTERNAL = "urn:expenses:problem:internal"


def problem_json_response(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str | None = None,
    type_uri: str = "about:blank",
    extensions: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build a JSON response that follows RFC 7807."""
    payload: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status,
        "instance": str(request.url.path),
    }
    if detail is not None:
        payload["detail"] = detail
    if extensions:
        payload.update(extensions)
    return JSONResponse(
        status_code=status,
        media_type=MEDIA_TYPE_PROBLEM_JSON,
        content=payload,
    )
