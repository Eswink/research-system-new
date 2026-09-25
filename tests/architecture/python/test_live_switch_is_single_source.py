"""live 显式开关的同源判据（GOAL-017 EC-02 / D-11）。

**为什么需要它**：D-11 把「凭据在场」从**充分**条件降为**必要**条件——开门从此还要一个
**显式开关**。这条收紧最容易在实现里漏成两半：门改了、某个 live 模块的 skip 分支没改，
于是那条用例仍然「凭据一到就跑」，或者开关被改了个名字却没人发现（**skip 不算红**，
所以「跑不成」在默认门上是不可见的）。

四条判据各压一件事，都能单独按红：

1. **名字只有一个声明点**（产品常量）+ 提到这个常量的文件是**显式清单**（加一个就要写理由）；
2. **环境读取只有一个点**（`tests/e2e/live_switch_support.py`）——产品层 `packages/application/**`
   保持 env-free，开关的**名字**是产品常量、**值**在操作者边界读；
3. **每个 live 模块都走到同一道开门逻辑**：带 `requires_live_llm` 的模块必须要么经
   `evaluate_live_run_gate(..., live_switch=...)`、要么调用 `live_e2e_switch_enabled()`；
   模块清单**逐条列出**（新加一个 live 模块就得在这里露头）；
4. **开关不被持久化**：`examples/**` 与仓库根的 `.env*` 里**不许**出现它的赋值
   ——否则「默认离线」会被一份配置文件悄悄掀掉。

另加两条同源断言：runbook §4 必须写**同一个名字**（改常量名/改名而不同步 ⇒ 红），
以及 `tests/egress_guard.py` **不得**提到这个开关（D-11 只改「进不进 run」，
**不许**改动出网放行面——放行面仍是 `requires_live_llm` 一个 marker）。
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path

from packages.application.model_relay.live_run_gate import LIVE_RUN_SWITCH
from tests.e2e.live_switch_support import live_e2e_switch_enabled

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNBOOK = REPO_ROOT / "docs/integration/LIVE_MODEL_RUNBOOK.md"
EGRESS_GUARD = REPO_ROOT / "tests/egress_guard.py"
GATE_MODULE = "packages/application/model_relay/live_run_gate.py"
#: 开关的**环境读取点**：单一职责的小模块（`live_run_support.py` 贴着 450 行硬上限，
#: 开关放进去会越界——见该模块 docstring）。
SWITCH_PREDICATE_MODULE = "tests/e2e/live_switch_support.py"
SELF = "tests/architecture/python/test_live_switch_is_single_source.py"

#: 操作者契约：这个名字是**操作者要敲进终端**的东西 ⇒ 判据里钉成字面量。
#: 改它 = 改操作者契约（runbook / 各 live 模块的 docstring 口令一起改）。
_OPERATOR_NAME = "RESEARCHOS_LIVE_E2E"
#: 常量的**标识符**（声明那一行由 `_DECLARATION` 钉住：名字只此一处）。
_CONSTANT_NAME = "LIVE_RUN_SWITCH"

#: 扫描面（只看这几棵树，且不跟随符号链接——`node_modules` 里的悬空链接会让遍历炸掉）。
SCAN_ROOTS = ("apps", "adapters", "packages", "services", "tests", "examples", "tools")
_PRUNE = {"node_modules", "__pycache__", ".venv", "dist", ".git", ".mypy_cache", ".ruff_cache"}
_SOURCE_SUFFIXES = (".py", ".ts", ".tsx", ".sh", ".yaml", ".yml", ".json")

#: 提到**常量名** `LIVE_RUN_SWITCH` 的文件（显式清单，每条给理由）。
#: 加一条就要解释一条：多一处提及 = 多一处可能绕过「唯一读取点」的地方。
#: （本判据自己不计入——见 `_source_files` 的自命中说明。）
CONSTANT_MENTIONS: dict[str, str] = {
    GATE_MODULE: "唯一声明点 + 门的理由文案（`set LIVE_RUN_SWITCH=1 to open`）",
    SWITCH_PREDICATE_MODULE: "唯一的环境读取点（`live_e2e_switch_enabled`）",
    "tests/e2e/test_ec04_live_gate_offline.py": "离线判据按**常量**断言理由里点名了开关",
    "tests/e2e/test_ec04_live_first_run.py": (
        "离线判据按**常量**独立重算「哪几条开门条件未满足」并逐条核对理由"
    ),
    "tests/architecture/python/test_live_failure_paths_same_source.py": (
        "同源判据按**常量**置位/断言缺开关的 skip 理由"
    ),
}

#: 含**字面量** `RESEARCHOS_LIVE_E2E` 的文件（同上，显式清单）。
#: 产品侧只有一处：声明常量那一行。测试侧的其余出现都是**模块 docstring 里的操作者口令**
#: （给不 import 常量的模块看的）——它们不是读取点，只是文案。
#: 匹配用**词边界**（`\b`）：`RESEARCHOS_LIVE_E2E_ENDPOINT` / `_KEY` 是**另外两个**变量，
#: 子串匹配会把它们混进来（本判据第一版就这么红过）。
LITERAL_MENTIONS: dict[str, str] = {
    GATE_MODULE: '声明 `LIVE_RUN_SWITCH = "RESEARCHOS_LIVE_E2E"`',
    "tests/e2e/test_ec03_real_runtime_offline_chain.py": "模块 docstring 的操作者口令",
    "tests/e2e/test_live_model_absence.py": "模块 docstring 的操作者口令（两道门并列）",
    "tests/e2e/test_m12_usage_real_relay.py": "模块 docstring 的操作者口令",
    "tests/e2e/test_run_chain_retrieval_live.py": "模块 docstring 的操作者口令",
}

#: 带 `requires_live_llm` 的模块清单（**逐条列出**：新加一个就在这儿露头）。
LIVE_MODULES: tuple[str, ...] = (
    "tests/e2e/test_ec02_experiment_live.py",
    "tests/e2e/test_ec03_real_runtime_offline_chain.py",
    "tests/e2e/test_ec04_live_first_run.py",
    "tests/e2e/test_evidence_chain_source_live.py",
    "tests/e2e/test_live_failure_paths.py",
    "tests/e2e/test_live_model_absence.py",
    "tests/e2e/test_m12_usage_real_relay.py",
    "tests/e2e/test_real_control_plane_experiment_live.py",
    "tests/e2e/test_real_control_plane_retrieval_live.py",
    "tests/e2e/test_real_deliverable_contract_live.py",
    "tests/e2e/test_real_protocol_run_live.py",
    "tests/e2e/test_run_chain_retrieval_live.py",
)

#: 模块级或函数级 mark 都算（`pytestmark = ...` 或标注装饰器形态）。
_LIVE_MARK = re.compile(r"pytest\.mark\.requires_live_llm")
_DECLARATION = re.compile(r"^LIVE_RUN_SWITCH\s*=\s*\"([^\"]+)\"", re.MULTILINE)
_PERSISTED = re.compile(r"^\s*RESEARCHOS_LIVE_E2E\s*=", re.MULTILINE)
#: 字面量的**词边界**匹配（见 `LITERAL_MENTIONS` 的说明）。
_LITERAL = re.compile(rf"\b{_OPERATOR_NAME}\b")


def _source_files() -> list[Path]:
    """扫描面里的源码文件（不跟随符号链接，剪掉依赖目录）。

    **本判据自己（`SELF`）不在扫描面里**：它的正文里那些词是**判据的针**（被检查的字符串），
    不是读取点、也不是 marker —— 对自己做针扫描必然自命中（第一版实测：本文件把自己
    同时算成「读了环境」和「带了 live marker」）。
    """
    self_path = REPO_ROOT / SELF
    found: list[Path] = []
    for root in SCAN_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = [name for name in dirnames if name not in _PRUNE]
            for filename in filenames:
                path = Path(dirpath) / filename
                if filename.endswith(_SOURCE_SUFFIXES) and path != self_path:
                    found.append(path)
    return sorted(found)


def _relatives_matching(pattern: re.Pattern[str]) -> set[str]:
    return {
        path.relative_to(REPO_ROOT).as_posix()
        for path in _source_files()
        if pattern.search(path.read_text(encoding="utf-8", errors="replace"))
    }


def _relatives_containing(needle: str) -> set[str]:
    return _relatives_matching(re.compile(re.escape(needle)))


def _live_modules() -> set[str]:
    return {
        path.relative_to(REPO_ROOT).as_posix()
        for path in _source_files()
        if _LIVE_MARK.search(path.read_text(encoding="utf-8", errors="replace"))
    }


def _names_the_switch(node: ast.expr | None) -> bool:
    """这个表达式**指名**开关：常量名，或**恰好等于**字面量的字符串（不是子串）。"""
    if isinstance(node, ast.Constant) and node.value == _OPERATOR_NAME:
        return True
    if isinstance(node, ast.Name) and node.id == _CONSTANT_NAME:
        return True
    return isinstance(node, ast.Attribute) and node.attr == _CONSTANT_NAME


def _is_switch_read(node: ast.AST) -> bool:
    """按开关名取映射项：`m.get(开关)` / `os.getenv(开关)` / `m[开关]`。"""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "getenv" and node.args and _names_the_switch(node.args[0]):
            return True
        if node.func.attr == "get" and node.args and _names_the_switch(node.args[0]):
            return True
    return isinstance(node, ast.Subscript) and _names_the_switch(node.slice)


def _switch_readers() -> set[str]:
    readers: set[str] = set()
    for path in _source_files():
        if path.suffix != ".py":
            continue
        module = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        if any(_is_switch_read(node) for node in ast.walk(module)):
            readers.add(path.relative_to(REPO_ROOT).as_posix())
    return readers


class TestTheNameHasASingleDeclaration:
    def test_the_product_constant_is_the_operator_name(self) -> None:
        assert LIVE_RUN_SWITCH == _OPERATOR_NAME, (
            "the switch is an operator-typed name; renaming it is a contract change and the "
            "runbook plus every live module's docstring command must change with it"
        )

    def test_the_literal_is_assigned_exactly_once_in_product_code(self) -> None:
        """产品代码里**只有一处**给这个名字赋值（`live_run_gate.py`）。"""
        declaring = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in _source_files()
            if _DECLARATION.search(path.read_text(encoding="utf-8", errors="replace"))
        ]
        assert declaring == [GATE_MODULE], (
            f"the switch name must be declared exactly once, in the product layer: {declaring}"
        )

    def test_mentions_of_the_constant_are_the_explicit_list(self) -> None:
        """提到常量的文件 = 显式清单 ⇒ 新增一处提及必须来这张表里写理由。"""
        actual = _relatives_containing("LIVE_RUN_SWITCH")
        assert actual == set(CONSTANT_MENTIONS), (
            "the set of files mentioning the switch constant changed — a new mention is a new "
            "place the switch could be read or re-decided: "
            f"added={sorted(actual - set(CONSTANT_MENTIONS))} "
            f"removed={sorted(set(CONSTANT_MENTIONS) - actual)}"
        )
        for rel, reason in CONSTANT_MENTIONS.items():
            assert reason, f"{rel} 的清单条目没有理由"

    def test_occurrences_of_the_literal_are_the_explicit_list(self) -> None:
        actual = _relatives_matching(_LITERAL)
        assert actual == set(LITERAL_MENTIONS), (
            "the literal switch name appeared somewhere new — if that place *reads* the "
            "environment, the single-read-point property is broken: "
            f"added={sorted(actual - set(LITERAL_MENTIONS))} "
            f"removed={sorted(set(LITERAL_MENTIONS) - actual)}"
        )


class TestTheEnvironmentIsReadInOnePlaceOnly:
    def test_the_predicate_module_is_the_only_reader(self) -> None:
        """**谁真的从某个映射里取开关**——按 AST 判，不按文本判。

        文本判据在这里不够用（实测第一版两处都错）：模块 docstring 里写着
        `RESEARCHOS_LIVE_E2E=1` 的**操作者口令**并不读环境，而
        `_os.environ.get('RESEARCHOS_LIVE_E2E')` 才是读——两者可以在**同一个文件**里同时
        出现（于是文本判据把四个模块误报成读取点，却把真正的第二读取点漏过去：
        那次按压用 `_os.environ.get(...)` + 别名，文本判据看着绿）。

        判定面 = 「**按开关名取映射项**」的表达式：`os.environ.get(X)` / `os.environ[X]` /
        `os.getenv(X)` / `<mapping>.get(X)`，其中 `X` 是常量名或**恰好等于**字面量的字符串。
        """
        assert _switch_readers() == {SWITCH_PREDICATE_MODULE}, (
            "the switch must be read from the environment in exactly one module: "
            f"{_switch_readers()}"
        )

    def test_the_application_layer_stays_environment_free(self) -> None:
        """产品层 `packages/application/**` **零**环境读取：名字是常量，值是**参数**。

        这是本实现形态的立论依据（也是 D-11 边界 (d) 的一部分）：门的开关由调用方传入，
        应用层不替操作者决定。全层零命中 ⇒ 这条判据是可以绝对断言的（不是抽样）。
        """
        offenders: list[str] = []
        application = REPO_ROOT / "packages/application"
        for dirpath, dirnames, filenames in os.walk(application, followlinks=False):
            dirnames[:] = [name for name in dirnames if name not in _PRUNE]
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                path = Path(dirpath) / filename
                text = path.read_text(encoding="utf-8", errors="replace")
                if "os.environ" in text or "getenv" in text:
                    offenders.append(path.relative_to(REPO_ROOT).as_posix())
        assert not offenders, (
            "the application layer must not read the environment — the operator boundary is "
            f"outside it; offenders: {sorted(offenders)}"
        )
        gate_text = (REPO_ROOT / GATE_MODULE).read_text(encoding="utf-8")
        assert "live_switch: bool" in gate_text, (
            "the gate must take the switch as a required argument (omission is a TypeError, "
            "never a silent open)"
        )

    def test_the_switch_value_must_be_exactly_one(self) -> None:
        """语义一眼可判：只有 `1` 算开；`true` / `yes` / `0` / 空白 一律算关。"""
        assert live_e2e_switch_enabled({LIVE_RUN_SWITCH: "1"}) is True
        for value in ("", "0", "true", "True", "yes", "on", " 1", "1 "):
            assert live_e2e_switch_enabled({LIVE_RUN_SWITCH: value}) is False, (
                f"{value!r} must not open the live run switch — the switch is not a truthiness test"
            )
        assert live_e2e_switch_enabled({}) is False


class TestEveryLiveModuleReachesTheSameOpeningLogic:
    def test_the_live_module_inventory_is_explicit(self) -> None:
        """带 marker 的模块 = 显式清单（新加一个就红，逼作者想清楚它的开门逻辑）。"""
        assert _live_modules() == set(LIVE_MODULES), (
            "the set of modules carrying requires_live_llm changed: "
            f"added={sorted(_live_modules() - set(LIVE_MODULES))} "
            f"removed={sorted(set(LIVE_MODULES) - _live_modules())}"
        )

    def test_every_live_module_consults_the_same_switch(self) -> None:
        """**无第二判据**：每个 live 模块要么经门（`live_switch=`）、要么调同一谓词。"""
        offenders: list[str] = []
        for rel in LIVE_MODULES:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            via_gate = "evaluate_live_run_gate(" in text and "live_switch=" in text
            via_predicate = "live_e2e_switch_enabled(" in text
            if not (via_gate or via_predicate):
                offenders.append(rel)
        assert not offenders, (
            "these live modules never consult the explicit switch, so credentials alone would "
            f"still start them: {offenders}"
        )

    def test_the_switch_predicate_has_exactly_one_definition(self) -> None:
        definitions = _relatives_containing("def live_e2e_switch_enabled")
        assert definitions == {SWITCH_PREDICATE_MODULE}, (
            f"the switch predicate must be defined once: {definitions}"
        )


class TestTheSwitchIsNeverPersisted:
    def test_no_config_surface_presets_the_switch(self) -> None:
        """`examples/**` 与仓库根的 `.env*` 里不许预设这个开关（默认必须离线）。"""
        surfaces: list[Path] = []
        examples = REPO_ROOT / "examples"
        for dirpath, dirnames, filenames in os.walk(examples, followlinks=False):
            dirnames[:] = [name for name in dirnames if name not in _PRUNE]
            surfaces.extend(Path(dirpath) / name for name in filenames)
        surfaces.extend(path for path in REPO_ROOT.glob(".env*") if path.is_file())
        presetting = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in surfaces
            if _PERSISTED.search(path.read_text(encoding="utf-8", errors="replace"))
        ]
        assert not presetting, (
            "the live switch is being persisted in a config surface — the default posture must "
            f"stay offline and the switch must be typed per run: {presetting}"
        )


class TestTheRunbookNamesTheSameSwitch:
    def _section_four(self) -> str:
        text = RUNBOOK.read_text(encoding="utf-8")
        start = text.find("\n## 4. Fake ↔ 真实：切换与回退")
        assert start != -1, "runbook 的 §4（Fake ↔ 真实：切换与回退）不见了"
        rest = text[start + 1 :]
        end = rest.find("\n## ", 3)
        return rest if end == -1 else rest[:end]

    def test_section_four_carries_the_switch_command(self) -> None:
        section = self._section_four()
        assert f"{LIVE_RUN_SWITCH}=1" in section, (
            "§4 must show the switch in an operator command line — same name, verbatim"
        )

    def test_the_runbook_switch_name_is_the_product_constant(self) -> None:
        """改常量名而不同步 runbook ⇒ 红（反向也一样：runbook 写过时的名字）。"""
        section = self._section_four()
        assert _OPERATOR_NAME in section, (
            "the runbook must name the switch exactly as the product constant declares it"
        )
        others = {
            token
            for token in re.findall(r"`([A-Z][A-Z0-9_]{3,})`", section)
            if token.endswith("_E2E") and token != _OPERATOR_NAME
        }
        assert not others, f"runbook §4 写了别的开关名：{sorted(others)}"


class TestTheReleaseSurfaceIsUnchanged:
    def test_the_egress_guard_does_not_know_the_switch(self) -> None:
        """D-11 **只**决定「进不进 run」：出网放行面仍是 `requires_live_llm` 一个 marker。"""
        guard = EGRESS_GUARD.read_text(encoding="utf-8")
        assert "LIVE_RUN_SWITCH" not in guard
        assert _OPERATOR_NAME not in guard, (
            "the egress guard must not learn the live switch — adding a second release "
            "criterion there would widen the outbound surface"
        )
