"""默认门凭据隔离的机械判据：夹具名单 ↔ 出厂目录 `credential_ref` ↔ 行为按压。

三件事各自可红：
1. **同步**：`tests/default_gate_credentials.LIVE_CREDENTIAL_KEYS` 必须等于出厂目录
   （`examples/config/*.yaml`）里有效的 `credential_ref` 集合 —— 新增凭据漏登记即判红。
2. **隔离**：在**子进程**里注入凭据键后跑 `test_default_gate_isolation_probe.py`
   （未标记 `requires_live_llm` 的用例）⇒ 它**看不到**凭据键。
3. **按压**：同一个子进程里跑 `tests/api/test_runs_api.py` ⇒ 出站判据不得判红（`blocked 0`）。

**为什么全部放在子进程**：本判据初版在**模块导入期**把凭据键放进进程环境来「制造泄漏」，
结果它**泄漏给了整个 pytest 会话**——`tests/e2e/test_run_chain_retrieval_live.py` 因此不再
skip，在 CI 上带着这个探针值真去调端点，把默认门判红（2026-09-25 实测）。
注入必须**限定在子进程内**：父进程只负责「带着凭据键启动子进程」。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests.default_gate_credentials import LIVE_CREDENTIAL_KEYS, catalog_credential_refs

_REPO = Path(__file__).resolve().parents[3]
#: 未标记 live 的探针（断言凭据键在默认门里不可见）。它本身也是常规用例（`test_` 命名由
#: `tests/architecture/test_module_file_naming.py` 强制），这里显式点名是为了连同按压文件
#: 一起在**同一子进程**里跑。
_PROBE_FILE = "tests/architecture/python/test_default_gate_isolation_probe.py"
#: 会走真实组合路径探端点健康的用例文件（凭据可见时它真的会出站）。
_PRESS_FILE = "tests/api/test_runs_api.py"
_CREDENTIAL_ENV_VALUE = "offline-isolation-probe-not-a-credential"


def test_isolation_list_matches_shipped_catalog() -> None:
    declared = catalog_credential_refs(_REPO)
    assert set(LIVE_CREDENTIAL_KEYS) == declared, (
        "默认门隔离名单与出厂目录的 credential_ref 不一致："
        f"名单={sorted(LIVE_CREDENTIAL_KEYS)} 目录={sorted(declared)}"
    )


def test_credential_leak_is_hidden_from_the_default_gate(tmp_path: Path) -> None:
    """按压：把凭据键注入**子进程**环境 ⇒ 探针看不到它，且默认门 `blocked 0`。"""
    env = dict(os.environ)
    for key in LIVE_CREDENTIAL_KEYS:
        env[key] = _CREDENTIAL_ENV_VALUE
    completed = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", _PROBE_FILE, _PRESS_FILE, "-q"],
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
