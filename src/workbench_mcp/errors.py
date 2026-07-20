"""Shared exception types for workbench-mcp."""


class WorkbenchMcpError(Exception):
    """Base class for expected workbench-mcp failures."""


class ConfigError(WorkbenchMcpError):
    """Raised when configuration cannot be loaded or validated safely."""
