"""
Logging configuration for the quantum-price-inference package.

Each module obtains its own logger via the standard pattern:

    import logging
    log = logging.getLogger(__name__)

Call ``configure_logging()`` once at application startup (e.g., in ``api/main.py``
or the top notebook cell) to set level and format.  The core library never calls
``configure_logging()`` itself — that is the caller's responsibility.
"""

from __future__ import annotations

import logging
import sys


def configure_logging(
    level: int | str = logging.INFO,
    fmt: str = "%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt: str = "%Y-%m-%dT%H:%M:%S",
) -> None:
    """Configure root logger for the application.

    Safe to call multiple times; subsequent calls update the existing handler.

    Args:
        level:   Logging level (default ``INFO``).  Pass ``logging.DEBUG`` or
                 the string ``"DEBUG"`` for verbose output.
        fmt:     Log record format string.
        datefmt: Timestamp format (ISO-8601 by default).
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    root = logging.getLogger()
    root.setLevel(level)

    # Replace existing handlers to avoid duplicate output on repeated calls.
    root.handlers = [handler]
