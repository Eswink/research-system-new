from __future__ import annotations

from dataclasses import dataclass, field

from architecture_fixture.domain.model import ResearchQuestion


@dataclass(slots=True)
class InMemoryResearchRepository:
    saved: list[ResearchQuestion] = field(default_factory=list)

    def save(self, question: ResearchQuestion) -> None:
        self.saved.append(question)
