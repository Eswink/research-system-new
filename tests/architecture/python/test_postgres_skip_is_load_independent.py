"""postgres / distributed 标记的跳过必须**与收集面无关**，且 fail-closed 面未被削弱。

2026-09-25 的普查（`docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md` 第 4 节）实测：PG 不可达时
`pytest tests/api/test_worker_plane_composition.py -q`（**不**收集 `tests/postgres`）**挂死**
（120s 无输出），而同一条命令加上 `tests/postgres` 收集就 `16 passed, 93 skipped`——因为跳过
钩子只写在子目录 conftest 里，而它只在被收集到时才加载。

本判据用**子进程**钉住两件事：
1. **加载无关**：定向跑 + PG 不可达 ⇒ 标记用例**跳过**、整轮**快速退出**（不再挂死）；
2. **fail-closed 未削弱**：`RESEARCHOS_REQUIRE_POSTGRES=1` + PG 不可达 ⇒ **非零退出**
   （而不是静默 skip / 挂死）。

PG 不可达用「指向不可达端口的 DSN」模拟（loopback，不触网）。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
#: 含 3 条 `postgres` 标记用例、且**不在** `tests/postgres` 目录下的文件（就是挂死那一例）。
_TARGET = "tests/api/test_worker_plane_composition.py"
_UNREACHABLE_DSN = "postgresql://research_os@127.0.0.1:1/research_os"
_TIMEOUT_SECONDS = 120


def _run(extra_env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["RESEARCHOS_POSTGRES_DSN"] = _UNREACHABLE_DSN
    env["DATABASE_URL"] = ""
    env["POSTGRES_DSN"] = ""
    env.pop("RESEARCHOS_REQUIRE_POSTGRES", None)
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-B", "-m", "pytest", _TARGET, "-q"],
        cwd=_REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        check=False,
    )


def test_targeted_run_skips_instead_of_hanging_when_postgres_is_unreachable() -> None:
    completed = _run({})
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, f"定向跑应当跳过而不是失败/挂死:\n{output[-1500:]}"
    assert "skipped" in output, f"应当出现跳过计数:\n{output[-1500:]}"


def test_require_postgres_still_fails_closed_when_unreachable() -> None:
    completed = _run({"RESEARCHOS_REQUIRE_POSTGRES": "1"})
    output = completed.stdout + completed.stderr
    assert completed.returncode != 0, (
        f"RESEARCHOS_REQUIRE_POSTGRES=1 且不可达时必须硬失败:\n{output[-1500:]}"
    )
    assert "not reachable" in output or "fail-closed" in output, (
        f"判词应点名不可达:\n{output[-1500:]}"
    )
