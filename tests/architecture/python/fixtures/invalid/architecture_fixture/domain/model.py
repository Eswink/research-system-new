from __future__ import annotations

from dataclasses import dataclass

from architecture_fixture.application.request import ApplicationRequest


@dataclass(frozen=True, slots=True)
class InvalidDomainState:
    request: ApplicationRequest
