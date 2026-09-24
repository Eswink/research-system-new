"""默认门的**凭据隔离**：出厂目录声明的凭据引用，默认门（非 live 用例）不得看见。

**为什么需要**：`litellm` 在**导入期**调用 `load_dotenv()`（`litellm/__init__.py`），把本机
gitignored 的 `.env` 注入**进程环境**。于是「未配置控制面」这类本应诚实失败的用例，在
整轮跑里会因凭据**可解析**而真的去探端点（`preflight_support._probe_endpoint` 先解析凭据、
再 `probe_connectivity`）——默认门的出站结构判据（`tests/egress_guard.py`）按设计把它拦下并
判红整轮。判据没有错：**漏的是隔离**。

**边界**：只对**未标记** `requires_live_llm` 的用例生效；带该 marker 的 live 用例照旧能读到
真实凭据（与出站判据的放行面**同源**）。

**同步**：本名单必须与出厂目录（`examples/config/*.yaml`）里**有效的** `credential_ref`
集合一致，由 `tests/architecture/python/test_default_gate_credential_isolation.py` 机器强制
——新增凭据若漏登记会判红，而不是静默逃出隔离。
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import yaml

#: 默认门必须隐藏的凭据环境变量。与出厂目录的 active `credential_ref` 一一对应。
LIVE_CREDENTIAL_KEYS: Final = ("LLM_MAIN_KEY",)

#: 出厂目录（相对仓库根）。
CONFIG_DIR: Final = "examples/config"


def catalog_credential_refs(root: Path) -> set[str]:
    """出厂目录里**有效的** `credential_ref` 值（按 YAML 解析：注释里的提及不算）。"""
    found: set[str] = set()
    for path in sorted((root / CONFIG_DIR).glob("*.yaml")):
        _walk(yaml.safe_load(path.read_text(encoding="utf-8")), found)
    return found


def _walk(node: object, found: set[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "credential_ref" and isinstance(value, str):
                found.add(value)
            _walk(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk(item, found)
