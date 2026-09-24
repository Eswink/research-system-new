"""默认门凭据隔离的机械判据：夹具名单 ↔ 出厂目录 `credential_ref` ↔ 行为按压。

三件事各自可红：
1. **同步**：`tests/default_gate_credentials.LIVE_CREDENTIAL_KEYS` 必须等于出厂目录
   （`examples/config/*.yaml`）里有效的 `credential_ref` 集合 —— 新增凭据漏登记即判红。
2. **隔离**：本模块在**导入期**把凭据键放进进程环境（**模拟** litellm 导入期
   `load_dotenv()` 的那次泄漏）⇒ 未标记 `requires_live_llm` 的用例**看不到**它。
3. **按压**：在**子进程**里带凭据键跑一个未标记 live 的用例文件 ⇒ 该轮出站判据不得判红
   （复现的正是 2026-09-25 普查里 `blocked 2` 的那条最小复现）。

**放行面未变**：隔离夹具与出站判据共用同一个 `ALLOW_MARKER`（`requires_live_llm`），
带该 marker 的 live 用例照旧能读到真实凭据 —— 隔离只收窄「默认门的进程环境」，
不新增也不删除任何开关。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests.default_gate_credentials import LIVE_CREDENTIAL_KEYS, catalog_credential_refs

_REPO = Path(__file__).resolve().parents[3]
#: 行为按压跑的文件：任意**未标记 live**、且会走真实组合路径探端点健康的用例文件。
_PRESS_FILE = "tests/api/test_runs_api.py"
_CREDENTIAL_ENV_VALUE = "offline-isolation-probe-not-a-credential"

#: 模拟「导入期泄漏」：不改写操作者真实的 `.env` 值（`setdefault`），只在缺位时放入探针值。
#: 解析本模块时进程环境里就有这个键 ⇒ 下面的隔离断言**非空真**（缺位时它本来就会通过）。
for _probe_key in LIVE_CREDENTIAL_KEYS:
    os.environ.setdefault(_probe_key, _CREDENTIAL_ENV_VALUE)


def test_isolation_list_matches_shipped_catalog() -> None:
    declared = catalog_credential_refs(_REPO)
    assert set(LIVE_CREDENTIAL_KEYS) == declared, (
        "默认门隔离名单与出厂目录的 credential_ref 不一致："
        f"名单={sorted(LIVE_CREDENTIAL_KEYS)} 目录={sorted(declared)}"
    )


def test_default_gate_cannot_see_live_credentials() -> None:
    """导入期已在进程环境里放进凭据键；本用例（未标记 live）不得看见它。"""
    visible = [key for key in LIVE_CREDENTIAL_KEYS if os.environ.get(key) is not None]
    assert visible == [], f"默认门凭据隔离失效：{visible} 在未标记 live 的用例里仍可见"


def test_credential_leak_no_longer_reds_the_default_gate(tmp_path: Path) -> None:
    """按压：把凭据键注入子进程环境跑默认门 ⇒ `blocked 0` 且无整轮红灯。"""
    env = dict(os.environ)
    for key in LIVE_CREDENTIAL_KEYS:
        env[key] = _CREDENTIAL_ENV_VALUE
    completed = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", _PRESS_FILE, "-q"],
        cwd=_REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    (tmp_path / "press-output.txt").write_text(output, encoding="utf-8")
    assert completed.returncode == 0, (
        f"按压轮判红（退出码 {completed.returncode}）:\n{output[-2000:]}"
    )
    assert "blocked 0" in output, f"按压轮仍有非环回阻断:\n{output[-2000:]}"
