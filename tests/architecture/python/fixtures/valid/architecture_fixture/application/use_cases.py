from __future__ import annotations

from dataclasses import dataclass

from architecture_fixture.application.ports import ResearchRepository
from architecture_fixture.domain.model import ResearchQuestion


@dataclass(frozen=True, slots=True)
class SubmitResearchQuestion:
    identifier: str
    prompt: str


def submit_research_question(
    repository: ResearchRepository,
    request: SubmitResearchQuestion,
) -> None:
    repository.save(ResearchQuestion(identifier=request.identifier, prompt=request.prompt))
