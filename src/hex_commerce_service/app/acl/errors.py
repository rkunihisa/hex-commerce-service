from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MappingIssue:
    path: str
    code: str
    message: str


class MappingError(Exception):
    def __init__(self, issues: list[MappingIssue]) -> None:
        super().__init__("invalid external payload")
        self.issues = issues

    def to_dict(self) -> dict[str, str | list[dict[str, str]]]:
        return {"error": "mapping_error", "issues": [vars(i) for i in self.issues]}
