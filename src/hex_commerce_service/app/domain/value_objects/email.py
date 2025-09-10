from __future__ import annotations

import re
from dataclasses import dataclass

# Practical, conservative pattern (not fully RFC 5322, but robust for VO)
_EMAIL_RE = re.compile(
    r"(?i)^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*$"
)


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip()
        v_lower = v.lower()
        if not _EMAIL_RE.match(v_lower):
            msg = f"invalid email: {self.value!r}"
            raise ValueError(msg)
        object.__setattr__(self, "value", v_lower)

    @property
    def local(self) -> str:
        return self.value.split("@", 1)[0]

    @property
    def domain(self) -> str:
        return self.value.split("@", 1)[1]

    def __str__(self) -> str:
        return self.value
