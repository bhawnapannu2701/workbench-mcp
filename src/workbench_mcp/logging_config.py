"""Structured logging setup for workbench-mcp."""

from __future__ import annotations

import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter for machine-readable local diagnostics."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True)


def configure_logging(level: str) -> None:
    """Configure root logging once with structured output."""

    logging.basicConfig(level=level, format="%(message)s", force=True)
    for handler in logging.getLogger().handlers:
        handler.setFormatter(JsonFormatter())
