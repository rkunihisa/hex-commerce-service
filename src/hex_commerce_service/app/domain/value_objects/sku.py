from __future__ import annotations

import re
from dataclasses import dataclass

# Uppercase letters, digits, hyphen and underscore. Length 1..64, must start with alnum.
_SKU_RE = re.compile(r"^[A-Z0-9][A-Z0-9-_]{0,63}$")


@dataclass(frozen=True, slots=True)
class Sku:
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip().upper()
        if not _SKU_RE.match(v):
            msg = "invalid sku (use A-Z, 0-9, -, _, length 1..64; must start with alnum)"
            raise ValueError(msg)
        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value
