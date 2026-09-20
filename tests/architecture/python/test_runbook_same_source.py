"""runbook 与代码同源判据（GOAL-008 EC-06 / PLAN-20260920-119）。

判据判**同源**，不判文笔：`docs/integration/LIVE_MODEL_RUNBOOK.md` 里出现的每个
仓库路径、变量名、pytest 目标、demo 符号，都必须在代码里真实存在；
五类内容（登记 / 凭据注入与轮换 / 重启边界 / Fake↔真实切换与回退 / 仍是 demo 的面）
缺任一类判红。

`docs/INDEX.md` 必须**登记**该文档（按行，不按「提及」）。

运行期产物（gitignored、clean checkout 里不存在）走**逐条白名单**，每条都写明理由——
白名单不是通配，加一条就要解释一条。
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNBOOK = REPO_ROOT / "docs/integration/LIVE_MODEL_RUNBOOK.md"
INDEX = REPO_ROOT / "docs/INDEX.md"

#: 运行期产物：clean checkout 里不存在，但 runbook 必须提到它们。
RUNTIME_ARTIFACTS: dict[str, str] = {
    "data/research-os-control.db": "配置面 SQLite，运行期首次启动时创建（gitignored）",
}

#: 会被当成「仓库路径」核对的顶层根。
PATH_ROOTS = (
    "adapters/",
    "apps/",
    "docs/",
    "examples/",
    "packages/",
    "services/",
    "tests/",
    "tools/",
    ".cursor/",
)

#: 代码扫描面：变量名/符号必须在这里面出现过。
CODE_ROOTS = ("adapters", "apps/web/src", "examples", "packages", "services", "tests", "tools")
CODE_SUFFIXES = (".py", ".ts", ".tsx", ".yaml", ".yml", ".json")
_SKIP_DIRS = {"node_modules", "__pycache__", ".venv", "dist", ".git"}

#: 五类内容各自的小节标题（缺任一 ⇒ 红）。
REQUIRED_SECTIONS: tuple[str, ...] = (
    "## 1. 登记一个端点与模型",
    "## 2. 凭据：注入与轮换",
    "## 3. 重启后重输的边界",
    "## 4. Fake ↔ 真实：切换与回退",
    "## 5. 哪些面仍是 demo",
)

_BACKTICK = re.compile(r"`([^`]+)`")
_ENV_TOKEN = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")
_FAKE_SYMBOL = re.compile(r"\bFake[A-Za-z]+")


def _code_text() -> str:
    chunks: list[str] = []
    for root in CODE_ROOTS:
        for path in sorted((REPO_ROOT / root).rglob("*")):
            if not path.is_file() or path.suffix not in CODE_SUFFIXES:
                continue
            if _SKIP_DIRS & set(path.relative_to(REPO_ROOT).parts):
                continue
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def _runbook() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def _tokens(text: str) -> set[str]:
    """反引号里的 token——**按行**抽取。

    跨行配对会让代码围栏（```）把反引号配错位，于是文档里明明写着的 token 被整段
    吞掉、判据「看着绿其实没看」（本判据第一版就这么漏掉了一个变量名，反证 F2 抓到）。
    行内代码本来就不跨行，按行抽是对的。
    """
    tokens: set[str] = set()
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            continue
        tokens.update(match.strip() for match in _BACKTICK.findall(line))
    return tokens


def _path_like(token: str) -> bool:
    return token.startswith(PATH_ROOTS) and " " not in token


def _missing_paths(tokens: set[str]) -> list[str]:
    missing: list[str] = []
    for token in sorted(tokens):
        if not _path_like(token) or token in RUNTIME_ARTIFACTS:
            continue
        if not (REPO_ROOT / token).exists():
            missing.append(token)
    return missing


def _missing_env_tokens(tokens: set[str], code: str) -> list[str]:
    return sorted(token for token in tokens if _ENV_TOKEN.match(token) and token not in code)


def _pytest_targets(text: str) -> set[str]:
    return {
        token for token in _tokens(text) if token.endswith(".py") and token.startswith("tests/")
    }


def _demo_symbols(text: str) -> set[str]:
    section = text.split("## 5. 哪些面仍是 demo", 1)[1]
    return {symbol for symbol in _FAKE_SYMBOL.findall(section) if symbol != "Fake"}


class TestRunbookIsIndexed:
    def test_runbook_exists(self) -> None:
        assert RUNBOOK.is_file(), f"{RUNBOOK.relative_to(REPO_ROOT)} 不存在"

    def test_docs_index_registers_the_runbook(self) -> None:
        """登记 = Integrations 清单里的**条目行**，不是「某处提过一句」。

        只判「全文出现过」会太松：快捷问答里的一句引用就能让它蒙混过关，
        而清单漏项正是这份索引最容易漂的地方。
        """
        entry = "- `integration/LIVE_MODEL_RUNBOOK.md`"
        rows = [line.strip() for line in INDEX.read_text(encoding="utf-8").splitlines()]
        assert entry in rows, f"docs/INDEX.md 的 Integrations 清单缺条目：{entry}"


class TestFiveContentClassesArePresent:
    def test_every_required_section_is_present(self) -> None:
        text = _runbook()
        missing = [section for section in REQUIRED_SECTIONS if section not in text]
        assert not missing, f"runbook 缺小节（EC-06 四类内容 + demo 清单）：{missing}"

    def test_restart_boundary_names_the_in_process_registry(self) -> None:
        """「重启后重输」必须落到**具体机制**上，不能只说「凭据不持久化」。"""
        text = _runbook()
        assert "RegistryCredentialResolver" in text
        assert "_registry" in text

    def test_switching_section_names_the_real_switch(self) -> None:
        text = _runbook()
        assert "RESEARCHOS_AGENT_RUNTIME" in text
        assert "openhands" in text


class TestCitedSymbolsAreReal:
    def test_every_cited_repo_path_exists(self) -> None:
        missing = _missing_paths(_tokens(_runbook()))
        assert not missing, f"runbook 引用了不存在的路径：{missing}"

    def test_runtime_artifacts_are_explicitly_allowlisted(self) -> None:
        """白名单逐条给理由，且每条都真的出现在 runbook 里（不许留死条目）。"""
        text = _runbook()
        assert RUNTIME_ARTIFACTS, "运行期产物白名单为空 = 没想过这件事"
        for token, reason in RUNTIME_ARTIFACTS.items():
            assert reason, f"{token} 的白名单条目没有理由"
            assert token in text, f"白名单里的 {token} 在 runbook 里已经不提了"

    def test_every_env_style_token_exists_in_code(self) -> None:
        missing = _missing_env_tokens(_tokens(_runbook()), _code_text())
        assert not missing, f"runbook 引用了代码里不存在的变量名：{missing}"

    def test_every_pytest_target_exists(self) -> None:
        targets = _pytest_targets(_runbook())
        assert targets, "runbook 必须给出可直接跑的 pytest 目标，否则读者只能猜"
        missing = sorted(t for t in targets if not (REPO_ROOT / t).exists())
        assert not missing, f"runbook 里的 pytest 目标不存在：{missing}"

    def test_demo_symbols_exist_in_the_fake_layer(self) -> None:
        symbols = _demo_symbols(_runbook())
        assert len(symbols) >= 5, f"demo 清单太短，不像是清点过的：{symbols}"
        code = _code_text()
        missing = sorted(symbol for symbol in symbols if symbol not in code)
        assert not missing, f"demo 清单里的符号在代码里找不到（清单陈旧）：{missing}"
