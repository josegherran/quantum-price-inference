"""Custom ASGI middleware for the quantum-price-inference API."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from quantum_price_inference._log import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a UUID4 request ID to every incoming request.

    The ID is:
    - Stored in the ``request_id_var`` ContextVar so all log records emitted
      during the request automatically include it (via ``_RequestIDFilter``).
    - Added to the response as the ``X-Request-ID`` header so clients can
      correlate their logs with server logs.

    If the client sends an ``X-Request-ID`` header, that value is used instead
    of generating a new one.  This allows end-to-end tracing across services.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response
