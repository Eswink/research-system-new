"""PostgreSQL 可达性守卫（**加载无关**）。

**问题**：`postgres` / `distributed` 标记的跳过逻辑原先只写在
`tests/postgres/conftest.py` 与 `tests/distributed/conftest.py`，而 conftest **只有在 pytest
真的收集到该目录时才会加载**。于是「跨目录的 postgres 标记」在**定向跑**里没有这道守卫：
2026-09-25 实测（PG 不可达）`pytest tests/api/test_worker_plane_composition.py -q` **挂死**
（120s 无输出，超时被杀），而同一条命令加上 `tests/postgres` 收集就正常 `16 passed, 93 skipped`。

**修法**：判定与跳过集中在本模块，由**根 conftest**（`tests/conftest.py` 的
`pytest_collection_modifyitems`）安装——它**任何** pytest 运行都会加载，因此与「收集到哪个
目录」无关。两个子目录 conftest 只保留各自的 schema 准备夹具。

**判据未动**：PG 可达 ⇒ 照常跑；不可达 ⇒ 跳过带原因的 skip；`RESEARCHOS_REQUIRE_POSTGRES=1`
⇒ **fail-closed**（不可达即硬失败，绝不静默跳过）。最后一条在定向跑里尤其重要：原先那台
`pytest.fail` 也只在 schema 夹具被加载时才生效，定向跑会**挂死**而不是失败——现在由本模块
在收集期直接以非零码退出（`pytest.exit`），比挂死更响亮、更快。
"""

from __future__ import annotations

import os
from typing import Final

import pytest

#: 与 `infra/compose/postgres-test.yaml` 的测试库一致（非凭据：本地测试库口令）。
DEFAULT_DSN: Final = "postgresql://research_os:research_os_m14_test@localhost:15432/research_os"

#: 需要 PostgreSQL 的标记（跨目录；守卫与目录无关）。
MARKERS: Final = ("postgres", "distributed")

#: 不可达时给出的启动提示（skip 原因与 fail-closed 判词共用一句）。
_START_HINT: Final = (
    "start with: docker compose --project-directory . -f infra/compose/postgres-test.yaml up -d"
)


def postgres_dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get("DATABASE_URL", DEFAULT_DSN),
    )


def postgres_required() -> bool:
    return os.environ.get("RESEARCHOS_REQUIRE_POSTGRES") == "1"


def postgres_available(dsn: str) -> bool:
    try:
        import psycopg

        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=2)
    except Exception:  # noqa: BLE001 - 任何连接层失败都意味着「不可达」
        return False
    conn.close()
    return True


def _marked(items: list[pytest.Item]) -> list[pytest.Item]:
    return [item for item in items if any(item.get_closest_marker(m) for m in MARKERS)]


def apply_reachability_skips(items: list[pytest.Item]) -> None:
    """按可达性给标记用例加 skip；`REQUIRE=1` 且不可达时 fail-closed。"""
    marked = _marked(items)
    if not marked:
        return
    dsn = postgres_dsn()
    if postgres_available(dsn):
        return
    if postgres_required():
        pytest.exit(
            f"RESEARCHOS_REQUIRE_POSTGRES=1 但 PostgreSQL 不可达（{dsn}）⇒ fail-closed："
            f"{len(marked)} 条 {'/'.join(MARKERS)} 标记用例必须失败而不是被跳过。"
            f"启动方式：{_START_HINT}",
            returncode=1,
        )
    reason = f"PostgreSQL not reachable at {dsn} — {_START_HINT}"
    skip = pytest.mark.skip(reason=reason)
    for item in marked:
        item.add_marker(skip)
