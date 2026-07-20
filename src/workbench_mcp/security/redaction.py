"""Secret redaction helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern


@dataclass(frozen=True)
class Redactor:
    """Redact configured secret patterns from service output."""

    patterns: tuple[Pattern[str], ...]

    @classmethod
    def from_patterns(cls, patterns: tuple[str, ...]) -> Redactor:
        return cls(tuple(re.compile(pattern) for pattern in patterns))

    def redact(self, value: str) -> str:
        redacted = value
        for pattern in self.patterns:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
