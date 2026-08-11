from __future__ import annotations

from typing import Protocol

from architecture_fixture.domain.model import ResearchQuestion


class ResearchRepository(Protocol):
    def save(self, question: ResearchQuestion) -> None: ...
