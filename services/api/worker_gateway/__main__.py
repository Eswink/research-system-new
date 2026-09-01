"""Worker gateway process entrypoint (M16 re-audit F-3): `python -m services.api.worker_gateway`.

Resolves the deployable `/worker/v1` ASGI app from the environment (PG DSN +
WORKER credential domain via the shared resolver) and serves it with uvicorn.
A non-loopback bind without `RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS=1` is
refused at app construction (fail closed, ADR-0027 §3).

Environment:
  RESEARCHOS_POSTGRES_DSN / DATABASE_URL   canonical store (required)
  WORKER_ENROLLMENT_SECRET                 pre-shared enrollment (required)
  RESEARCHOS_WORKER_GATEWAY_HOST           bind host (default 127.0.0.1)
  RESEARCHOS_WORKER_GATEWAY_PORT           bind port (default 8081)
  RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS    1 for non-loopback production bind
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    _ = argv
    import uvicorn

    from services.api.worker_gateway.composition import build_gateway_from_env

    app, host, port = build_gateway_from_env()
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
