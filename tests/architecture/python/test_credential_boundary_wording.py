"""凭据边界三面同源的判据（GOAL-008 EC-03 AC-04）。

EC-03 的要害不是「有凭据机制」，而是**读面不说谎**：早先
`docs/integration/LLM_ENDPOINTS.md` §9 写「API Key 加密/Secret Store」——本仓既没有
加密，也没有 Secret Manager，凭据只在环境变量或**进程内**注册表里，重启即消失。
这类谎言无法被功能用例发现（功能都对），只能由**措辞判据**钉住。

三面各自承担同一事实的不同措辞，本判据要求三面**都**出现：

1. `docs/integration/LLM_ENDPOINTS.md` §9：对外文档（人读）；
2. `apps/web/src/features/endpoints/EndpointsHome.tsx`：控制台读面（中英双语文案）；
3. `adapters/relay/registry_credential_resolver.py`：机制本身的 docstring（改机制先改它）。

同时断言**不实的持久化声明**在三面都不存在——只钉「说了什么」不够，
还得钉「不许说什么」（`Secret Store` / `加密` 作为凭据存储承诺即属此类）。

判据故意用**子串**而不是 AST：前两面本来就是自然语言（文案/文档），
第三面是 docstring；这里要钉的正是措辞本身。措辞变更时判据变红是**预期**行为
——改文案就要同时改这里，正是「同源」的含义。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs" / "integration" / "LLM_ENDPOINTS.md"
UI = ROOT / "apps" / "web" / "src" / "features" / "endpoints" / "EndpointsHome.tsx"
RESOLVER = ROOT / "adapters" / "relay" / "registry_credential_resolver.py"

#: 三面各自必须出现的措辞（面 → (人读名, 必需子串...)）。
REQUIRED: dict[Path, tuple[str, tuple[str, ...]]] = {
    DOCS: (
        "文档 §9",
        (
            "只存在于环境变量或进程内注册表",  # 值存在哪里
            "重启后需重新注入",  # 重启边界
            "不伪装 Secret Manager",  # 不做 Secret Manager 的样子
        ),
    ),
    UI: (
        "控制台读面",
        (
            "Credential values live only in environment variables",  # 值存在哪里（en）
            "重启后需重新注入",  # 重启边界（zh）
            "not a Secret Manager",  # 不做 Secret Manager 的样子（en）
        ),
    ),
    RESOLVER: (
        "凭据解析器 docstring",
        (
            "永不落盘",
            "服务重启后注册表清空",
            "不伪装 Secret Manager",
        ),
    ),
}

#: 明令禁止出现在这些面上的**不实持久化承诺**（措辞级，不是语义级）。
FORBIDDEN = (
    "Secret Store",
    "凭据已保存",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"判据引用的面不存在：{path}"
    return path.read_text(encoding="utf-8")


def test_all_faces_state_the_credential_boundary() -> None:
    missing: list[str] = []
    for path, (label, phrases) in REQUIRED.items():
        text = _read(path)
        missing.extend(f"{label} 缺少措辞：{phrase!r}" for phrase in phrases if phrase not in text)
    assert missing == [], "; ".join(missing)


def test_no_face_promises_secret_persistence() -> None:
    offenders: list[str] = []
    for path, (label, _) in REQUIRED.items():
        text = _read(path)
        offenders.extend(
            f"{label} 出现不实声明：{phrase!r}" for phrase in FORBIDDEN if phrase in text
        )
    assert offenders == [], "; ".join(offenders)
