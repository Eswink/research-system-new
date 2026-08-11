from __future__ import annotations

from collections.abc import Callable
from functools import partial

from architecture_fixture.adapters.in_memory import InMemoryResearchRepository
from architecture_fixture.application.use_cases import (
    SubmitResearchQuestion,
    submit_research_question,
)


def build_submitter() -> Callable[[SubmitResearchQuestion], None]:
    return partial(submit_research_question, InMemoryResearchRepository())
