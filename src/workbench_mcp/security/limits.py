"""Limit enforcement helpers."""

from __future__ import annotations

from pathlib import Path

from workbench_mcp.errors import BinaryFileError, FileTooLargeError

TEXT_SAMPLE_BYTES = 4096


def enforce_file_size(path: Path, max_size_bytes: int) -> int:
    """Return file size after enforcing a maximum byte limit."""

    size_bytes = path.stat().st_size
    if size_bytes > max_size_bytes:
        msg = f"file exceeds maximum size: {size_bytes} bytes > {max_size_bytes} bytes"
        raise FileTooLargeError(msg)
    return size_bytes


def decode_text_bytes(data: bytes) -> str:
    """Decode UTF-8 text bytes and reject binary-looking content."""

    if b"\x00" in data[:TEXT_SAMPLE_BYTES]:
        msg = "file appears to be binary because it contains NUL bytes"
        raise BinaryFileError(msg)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        msg = "file is not valid UTF-8 text"
        raise BinaryFileError(msg) from exc


def utf8_size(value: str) -> int:
    """Return UTF-8 encoded size for output-limit accounting."""

    return len(value.encode("utf-8"))


def truncate_text(value: str, max_bytes: int) -> tuple[str, bool]:
    """Truncate text to a UTF-8 byte budget without splitting code points."""

    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value, False

    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated, True


def truncate_output_pair(
    stdout: str,
    stderr: str,
    max_total_bytes: int,
) -> tuple[str, str, bool, bool]:
    """Apply one total output budget across stdout first, then stderr."""

    stdout_limited, stdout_truncated = truncate_text(stdout, max_total_bytes)
    remaining_bytes = max(max_total_bytes - utf8_size(stdout_limited), 0)
    stderr_limited, stderr_truncated = truncate_text(stderr, remaining_bytes)
    if stderr and remaining_bytes == 0:
        stderr_truncated = True
    return stdout_limited, stderr_limited, stdout_truncated, stderr_truncated
