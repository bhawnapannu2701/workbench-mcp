"""Server bootstrap helpers.

FastMCP tool registration is intentionally deferred until later implementation phases.
"""

from __future__ import annotations

from workbench_mcp.config import WorkbenchConfig, load_config
from workbench_mcp.logging_config import configure_logging


def load_runtime_config() -> WorkbenchConfig:
    """Load configuration and configure structured logging for startup."""

    config = load_config()
    configure_logging(config.log_level)
    return config
