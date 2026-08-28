"""Subprocess script builders for memory/claim concurrency tests (M14 DS-3).

Keeps `tests/postgres/test_memory_claim_concurrency.py` under the 300-line
source limit. Every script runs in an independent OS process against the
shared PostgreSQL DSN.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

_DSN = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)
_ENV = os.environ.copy()
_ENV["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
_ENV["RESEARCHOS_POSTGRES_DSN"] = _DSN


def env() -> dict[str, str]:
    return _ENV


def dsn() -> str:
    return _DSN


def memory_commit_script(memory_id: str, source: str) -> str:
    """Inline script: attempt to commit a MemoryWriteProposal."""
    return textwrap.dedent(f"""\
        import sys, json
        import pathlib, sys
        sys.path.insert(0, r"{_ENV["PYTHONPATH"]}")
        from adapters.postgres.db import migrate, dsn_from_env
        from adapters.postgres.memory_store import PostgresMemoryStore
        from packages.domain.enums import MemoryTier, MemoryType
        from packages.domain.memory import MemoryWriteProposal

        migrate(r"{_DSN}")
        store = PostgresMemoryStore(dsn=r"{_DSN}", allowed_sources=("{source}",))
        try:
            proposal = MemoryWriteProposal(
                id="{memory_id}",
                tier=MemoryTier.PROJECT,
                kind=MemoryType.FACT,
                content="concurrent fact",
                provenance="{source}",
                confidence=0.9,
            )
            record = store.commit(proposal)
            print("COMMITTED", flush=True)
        except Exception as e:
            print(f"REJECTED: {{type(e).__name__}}: {{e}}", flush=True)
        finally:
            store.close()
    """)


def memory_delete_script() -> str:
    """Inline script: deleting a non-existent memory must raise InvalidInputError."""
    return textwrap.dedent(f"""\
        import sys
        sys.path.insert(0, r"{_ENV["PYTHONPATH"]}")
        from adapters.postgres.db import migrate
        from adapters.postgres.memory_store import PostgresMemoryStore
        from packages.application.ports.errors import InvalidInputError

        migrate(r"{_DSN}")
        store = PostgresMemoryStore(dsn=r"{_DSN}")
        try:
            store.delete("non-existent-id")
            print("ERROR: should have raised", flush=True)
        except InvalidInputError as e:
            print(f"CORRECT: {{e}}", flush=True)
        finally:
            store.close()
    """)


def memory_commit_for_deactivate(memory_id: str) -> str:
    """Inline script: commit a memory row (pre-step for deactivate test)."""
    return textwrap.dedent(f"""\
        import sys
        sys.path.insert(0, r"{_ENV["PYTHONPATH"]}")
        from adapters.postgres.db import migrate
        from adapters.postgres.memory_store import PostgresMemoryStore
        from packages.domain.enums import MemoryTier, MemoryType
        from packages.domain.memory import MemoryWriteProposal

        migrate(r"{_DSN}")
        store = PostgresMemoryStore(dsn=r"{_DSN}", allowed_sources=("test",))
        proposal = MemoryWriteProposal(
            id="{memory_id}", tier=MemoryTier.PROJECT, kind=MemoryType.FACT,
            content="to deactivate", provenance="test", confidence=0.8,
        )
        store.commit(proposal)
        store.close()
        print("COMMITTED", flush=True)
    """)


def memory_deactivate_script(memory_id: str) -> str:
    """Inline script: deactivate twice; both must be idempotent no-ops."""
    return textwrap.dedent(f"""\
        import sys
        sys.path.insert(0, r"{_ENV["PYTHONPATH"]}")
        from adapters.postgres.memory_store import PostgresMemoryStore

        store = PostgresMemoryStore(dsn=r"{_DSN}")
        r1 = store.deactivate("{memory_id}")
        r2 = store.deactivate("{memory_id}")
        assert r1.active is False
        assert r2.active is False
        store.close()
        print("IDEMPOTENT_OK", flush=True)
    """)


def claim_register_script(claim_id: str, statement: str, *, expect_success: bool) -> str:
    """Inline script: register a claim; asserts on expected outcome."""
    try_branch = (
        'print("REGISTERED_B", flush=True)'
        if expect_success
        else ('raise AssertionError("conflict should have been raised")')
    )
    return textwrap.dedent(f"""\
        import sys
        sys.path.insert(0, r"{_ENV["PYTHONPATH"]}")
        from adapters.postgres.db import migrate
        from adapters.postgres.evidence_ledger import PostgresEvidenceLedger
        from packages.domain.evidence import Claim, ClaimStatus

        migrate(r"{_DSN}")
        ledger = PostgresEvidenceLedger(dsn=r"{_DSN}")
        claim = Claim(id="{claim_id}", statement="{statement}", status=ClaimStatus.PROPOSED)
        try:
            ledger.register_claim(claim)
            {try_branch}
        except Exception as e:
            if {not expect_success}:
                print(f"CONFLICT: {{type(e).__name__}}: {{e}}", flush=True)
            else:
                raise
        ledger.close()
    """)


def claim_update_script() -> str:
    """Inline script: updating a non-existent claim must raise InvalidInputError."""
    return textwrap.dedent(f"""\
        import sys
        sys.path.insert(0, r"{_ENV["PYTHONPATH"]}")
        from adapters.postgres.db import migrate
        from adapters.postgres.evidence_ledger import PostgresEvidenceLedger
        from packages.application.ports.errors import InvalidInputError
        from packages.domain.evidence import Claim, ClaimStatus

        migrate(r"{_DSN}")
        ledger = PostgresEvidenceLedger(dsn=r"{_DSN}")
        claim = Claim(id="nonexistent", statement="x", status=ClaimStatus.PROPOSED)
        try:
            ledger.update_claim(claim)
            print("ERROR: should have raised", flush=True)
        except InvalidInputError as e:
            print(f"CORRECT: {{e}}", flush=True)
        finally:
            ledger.close()
    """)
