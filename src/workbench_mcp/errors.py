"""Shared exception types for workbench-mcp."""


class WorkbenchMcpError(Exception):
    """Base class for expected workbench-mcp failures."""


class ConfigError(WorkbenchMcpError):
    """Raised when configuration cannot be loaded or validated safely."""


class SecurityError(WorkbenchMcpError):
    """Raised when an operation violates a configured security boundary."""


class WorkspaceFileError(WorkbenchMcpError):
    """Raised when a workspace file operation cannot be completed safely."""


class PathSecurityError(WorkspaceFileError):
    """Raised when a requested path violates workspace containment rules."""


class PathTraversalError(PathSecurityError):
    """Raised when a requested path contains parent-directory traversal."""


class PathEscapeError(PathSecurityError):
    """Raised when a requested path resolves outside an approved root."""


class SymlinkEscapeError(PathEscapeError):
    """Raised when a symbolic link would escape an approved root."""


class WorkspacePathNotFoundError(WorkspaceFileError):
    """Raised when a requested workspace path does not exist."""


class FileTooLargeError(WorkspaceFileError):
    """Raised when a requested file exceeds configured size limits."""


class BinaryFileError(WorkspaceFileError):
    """Raised when a text-only operation receives binary data."""


class InvalidRangeError(WorkspaceFileError):
    """Raised when a requested line range is invalid."""


class ReadOnlyModeError(WorkspaceFileError):
    """Raised when a write is blocked by read-only mode."""


class PatchPreconditionError(WorkspaceFileError):
    """Raised when a patch expected-content precondition is not met."""


class CommandSecurityError(SecurityError):
    """Raised when a process command is not approved for execution."""


class ArtifactAccessError(SecurityError):
    """Raised when artifact collection is not approved."""


class ProcessExecutionError(WorkbenchMcpError):
    """Raised when a subprocess cannot be started or managed."""


class GitServiceError(WorkbenchMcpError):
    """Raised when read-only Git inspection fails unexpectedly."""
