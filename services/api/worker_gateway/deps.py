"""Worker gateway dependency container (M16 WP1)."""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.worker_registry import WorkerRegistry
from services.api.worker_gateway.settings import WorkerGatewaySettings


@dataclass(frozen=True, slots=True)
class WorkerGatewayDeps:
    """Assembled worker-gateway dependencies: registry + credentials + settings.

    `bind_host` records the address the gateway is served on; a non-loopback
    bind without TLS is refused at app construction (fail closed).
    """

    registry: WorkerRegistry
    credentials: CredentialResolver
    settings: WorkerGatewaySettings
    bind_host: str = "127.0.0.1"
