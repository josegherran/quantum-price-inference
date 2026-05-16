"""Application settings loaded from environment variables (QPI_ prefix).

All values have sensible defaults so the application starts with no
environment configuration.  Set QPI_* variables (or add them to
deploy/.env) to override for production deployments.

Example
-------
    QPI_LOG_LEVEL=DEBUG
    QPI_LOG_JSON=true
    QPI_CORS_ORIGINS='["https://myapp.example.com"]'
    QPI_ESTIMATION_TIMEOUT_SECONDS=60
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Logging
    log_level: str = "INFO"
    log_json: bool = False

    # CORS — list of allowed origins for the API
    cors_origins: list[str] = [
        "http://localhost:8888",   # Jupyter notebook default port
        "http://localhost:3000",   # local frontend dev server
        "http://127.0.0.1:8888",
        "http://127.0.0.1:3000",
    ]

    # Rate limiting (slowapi format: "N/period")
    classical_rate_limit: str = "30/minute"
    quantum_rate_limit: str = "10/minute"

    # Quantum estimation timeout in seconds
    estimation_timeout_seconds: float = 30.0

    # In-process LRU cache sizes
    classical_cache_maxsize: int = 256
    quantum_cache_maxsize: int = 128

    model_config = {"env_prefix": "QPI_"}


settings = Settings()
