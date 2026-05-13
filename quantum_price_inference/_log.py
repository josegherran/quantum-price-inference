"""
Logging configuration for the quantum-price-inference package.

Each module obtains its own logger via the standard pattern:

    import logging
    log = logging.getLogger(__name__)

Call ``configure_logging()`` once at application startup (e.g., in ``api/main.py``
or the top notebook cell) to set level and format.  The core library never calls
``configure_logging()`` itself — that is the caller's responsibility.

Request ID injection
--------------------
When running inside the FastAPI application, a ``request_id`` is stored in a
``contextvars.ContextVar`` by ``api.middleware.RequestIDMiddleware``.  The
``_RequestIDFilter`` defined here reads that variable and injects it into every
log record emitted during the request, enabling log correlation across modules.

JSON logging
------------
Pass ``json=True`` to ``configure_logging()`` to emit one JSON object per line.
This is the recommended format for production log aggregators (CloudWatch,
Datadog, Loki, etc.).  The plain-text format is the default for local development
and notebook use.
"""

from __future__ import annotations

import json as _json
import logging
import sys
from contextvars import ContextVar

# ---------------------------------------------------------------------------
# Request-ID context variable
# ---------------------------------------------------------------------------

#: Stores the current request ID.  Set by ``api.middleware.RequestIDMiddleware``.
#: Defaults to ``"-"`` when no request is active (e.g., notebook cells, tests).
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


# ---------------------------------------------------------------------------
# Filters and formatters
# ---------------------------------------------------------------------------


class _RequestIDFilter(logging.Filter):
    """Inject the current ``request_id`` into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.request_id = request_id_var.get()  # type: ignore[attr-defined]
        return True


class _JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record.

    Fields: ``ts``, ``level``, ``logger``, ``msg``, and optionally
    ``request_id`` when one is present in the record.
    """

    def format(self, record: logging.LogRecord) -> str:
        obj: dict[str, object] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        request_id = getattr(record, "request_id", "-")
        if request_id and request_id != "-":
            obj["request_id"] = request_id
        if record.exc_info:
            obj["exc_info"] = self.formatException(record.exc_info)
        return _json.dumps(obj)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def configure_logging(
    level: int | str = logging.INFO,
    fmt: str = "%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s — %(message)s",
    datefmt: str = "%Y-%m-%dT%H:%M:%S",
    json: bool = False,
) -> None:
    """Configure root logger for the application.

    Safe to call multiple times; subsequent calls update the existing handler.

    Args:
        level:   Logging level (default ``INFO``).  Pass ``logging.DEBUG`` or
                 the string ``"DEBUG"`` for verbose output.
        fmt:     Log record format string (plain-text mode only).
        datefmt: Timestamp format (ISO-8601 by default).
        json:    Emit JSON lines instead of plain text.  Recommended for
                 production deployments and log aggregators.
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.addFilter(_RequestIDFilter())

    if json:
        handler.setFormatter(_JsonFormatter(datefmt=datefmt))
    else:
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    root = logging.getLogger()
    root.setLevel(level)

    # Replace existing handlers to avoid duplicate output on repeated calls.
    root.handlers = [handler]
