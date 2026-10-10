#!/usr/bin/env python3
"""GOAL-20261010-049 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…048 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal049_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-049 特有的断言**。

三条主轴（逐条对 GOAL-049 的 EC）：

1. **EC-02 查询面**：`MemoryStore.query` 有**可选的 `scope` 维**（Port + **三适配器同契约**）；
   缺省不筛（两维都 None ⇒ 全部）；两维**可并存**。
2. **EC-03 消费面**：`memory_read` 可传 `scope` 且载荷**点名**声明范围与 `filtered_out`；
   **未知范围 ⇒ 点名**；**缺省路径不出现那两键**（逐字不变）；HTTP 读面用**两个显式 DTO 形态**
   （**不**用会递归抹掉 `null` 的 `response_model_exclude_none`）。
3. **EC-04 两向**：判据在树，四条按压（筛了不生效 / 没筛却筛掉 / 未知范围静默空集 /
   筛掉数不点名）逐条对得上用例；归档进树。

**两条纪律**（承 GOAL-027…048 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
  **本文件自身也遵守「判关系不判位置」**（承 `MEM-20261010-215`）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/adapters/canonical/test_memory_read_dispositions.py", 22),
    ("tests/adapters/sqlite/test_memory_scope_and_validity.py", 14),
    ("tests/postgres/test_memory_scope_pg.py", 3),
    ("tests/api/test_memory_api.py", 10),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/contracts/test_openapi_snapshot.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-02 落点（Port + 三适配器）。
PORT = "packages/application/ports/memory_store.py"
ADAPTERS: tuple[str, ...] = (
    "adapters/sqlite/memory_store.py",
    "adapters/postgres/memory_store.py",
    "adapters/fakes/memory_store.py",
)

#: EC-03 落点（读面 + DTO + 路由）。
READ_FACE = "adapters/canonical/memory_read.py"
DTOS = "services/api/dto/memory.py"
ROUTER = "services/api/routers/memory.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: EC-03 必须点名的形态（逐条；缺一即判红）。
NAMED_FORMS: tuple[str, ...] = (
    "is not a known scope",
    "filtered_out",
)

#: EC-04 判据文件（逐条点名按压各自的用例）。
STORE_JUDGE = "tests/adapters/sqlite/test_memory_scope_and_validity.py"
READ_JUDGE = "tests/adapters/canonical/test_memory_read_dispositions.py"
API_JUDGE = "tests/api/test_memory_api.py"

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal049_closeout.py"
ASSERTIONS = "tools/goal049_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261010-049-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261010-049-verdict-clean.txt"

#: 本轮的两向反证归档（按压读数）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261010-049-press-two-way.txt"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _joined(root: Path, relatives: tuple[str, ...]) -> str:
    """多落点的合并文本（判关系不判位置）。"""
    return "\n".join(_text(root, relative) for relative in relatives)


def _function_names(source: str) -> set[str]:
    """模块里定义的函数名（AST 读，不靠文本巧合）。"""
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(parsed)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def _query_signatures(source: str) -> list[str]:
    """`def query(...)` 的**参数名序列**（AST 读 ⇒ 判「有没有 scope 维」而不判写法）。"""
    if not source:
        return []
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return []
    found: list[str] = []
    for node in ast.walk(parsed):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == "query":
            args = [a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)]
            found.append(",".join(args))
    return found


def _calls_named(source: str, keyword: str) -> int:
    """源码里**以该名字作关键字实参**的调用数（AST 读 ⇒ **不**把注释/字符串里的提及算进来）。

    **本判据当场兑现价值**：初版用 `keyword not in source` ⇒ 路由里那句**解释为什么不用它**的
    注释被判成违规而**假红**（实测）。判「用没用」要读 AST（承 `MEM-20261010-215`）。
    """
    if not source:
        return 0
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, ast.Call) and any(kw.arg == keyword for kw in node.keywords)
    )


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    parsed = ast.parse(source)
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    )


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：Port 与**三个**适配器都有可选的 `scope` 维（同契约）。"""
    port_sigs = _query_signatures(_text(root, PORT))
    adapter_sigs = {relative: _query_signatures(_text(root, relative)) for relative in ADAPTERS}
    verdicts: list[Any] = [
        toolbox.verdict(
            "ec02-the-port-declares-the-scope-dimension",
            bool(port_sigs) and all("scope" in sig for sig in port_sigs),
            ",".join(port_sigs),
        )
    ]
    for relative, sigs in adapter_sigs.items():
        verdicts.append(
            toolbox.verdict(
                f"ec02-{Path(relative).parent.name}-carries-the-scope-dimension",
                bool(sigs) and all("scope" in sig for sig in sigs),
                ",".join(sigs),
            )
        )
    # 三适配器**同契约**：签名参数序列一致（同一条纪律会在每个适配器各犯一次）
    signatures = {sig for sigs in adapter_sigs.values() for sig in sigs}
    verdicts.append(
        toolbox.verdict(
            "ec02-the-three-adapters-share-one-signature",
            len(signatures) == 1,
            ",".join(sorted(signatures)),
        )
    )
    return verdicts


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：消费面（点名范围与筛掉数 + 未知范围点名 + 缺省不出现那两键 + 两个 DTO 形态）。"""
    read_face = _text(root, READ_FACE)
    dtos = _text(root, DTOS)
    router = _text(root, ROUTER)
    return [
        toolbox.verdict(
            "ec03-the-read-face-accepts-a-scope",
            'args.get("scope")' in read_face,
        ),
        toolbox.verdict(
            "ec03-every-missing-form-is-named",
            all(marker in read_face for marker in NAMED_FORMS),
            ",".join(item for item in NAMED_FORMS if item not in read_face),
        ),
        toolbox.verdict(
            "ec03-the-default-payload-omits-the-two-keys",
            # 只**在做条件分支**里加那两键：`if scope is not None:` 之内
            "if scope is not None:" in read_face and 'payload["scope"] = scope' in read_face,
            "缺省路径不得多出键（判据名上的两键只在传了 scope 时出现）",
        ),
        toolbox.verdict(
            "ec03-the-http-face-uses-two-explicit-shapes",
            "MemoryFilteredListViewDto" in dtos
            and "MemoryFilteredListViewDto(MemoryListViewDto)" in dtos,
            "用**继承**的两个显式形态，而不是会递归抹掉 null 的 exclude_none",
        ),
        toolbox.verdict(
            "ec03-the-recursive-switch-is-not-used",
            _calls_named(router, "response_model_exclude_none") == 0,
            "**不得调用**该开关（它会递归到嵌套模型，抹掉有意义的 null —— 实测）；"
            "注释里提到它不算调用（文本判据会把说明当违规 ⇒ 用 AST 数关键字实参）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-the-new-parameter",
            "scope" in _text(root, SNAPSHOT) and "filtered_out" in _text(root, SNAPSHOT),
            "OpenAPI 快照必须含新入参/字段（承 MEM-20261010-216 的下游同步纪律）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的用例逐条点名 + 归档形态。"""
    store = _text(root, STORE_JUDGE)
    read = _text(root, READ_JUDGE)
    api = _text(root, API_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-filter-is-asserted-at-the-store",
            "test_the_declared_scope_becomes_selectable_at_the_query_face" in store,
        ),
        toolbox.verdict(
            "ec04-the-second-tier-guard-is-asserted",
            "MemoryTier.SESSION" in store,
            "缺省被改动的反证臂需要**跨 tier** 的数据才区分得出来（本轮实测到的假绿）",
        ),
        toolbox.verdict(
            "ec04-the-default-payload-case-is-asserted",
            "test_the_default_payload_carries_no_scope_keys" in read,
        ),
        toolbox.verdict(
            "ec04-the-unknown-scope-case-is-asserted",
            "test_an_unknown_scope_is_named_not_read_as_empty" in read,
        ),
        toolbox.verdict(
            "ec04-the-two-dimensions-coexist-case-is-asserted",
            "test_the_scope_and_tier_dimensions_coexist" in read,
        ),
        toolbox.verdict(
            "ec04-the-http-face-case-is-asserted",
            "test_the_list_face_can_be_filtered_by_scope" in api,
        ),
        toolbox.verdict(
            "ec04-every-press-is-red-in-the-archive",
            press.count("按压 RED") >= 4 and "all_red_and_restored=True" in press,
            "四条的读数必须全红且复原一致",
        ),
    ]


def _judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据面：例数下界 + 既有判据仍在树（引用而非重复）。"""
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        count = _count_test_cases(root, relative)
        verdicts.append(
            toolbox.verdict(f"cases-{Path(relative).stem}", count >= floor, f"{count} < {floor}")
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(f"prior-judge-{Path(relative).stem}", (root / relative).is_file())
        )
    return verdicts


def _has_carriage_return(raw: bytes) -> bool:
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…048 的教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：判词归档形态（两份、非空、CR=0）。**不读内容做断言**（输入即输出）。"""
    verdicts: list[Any] = []
    for label, relative in (("current", ARCHIVE_CURRENT), ("clean", ARCHIVE_CLEAN)):
        path = root / relative
        raw = path.read_bytes() if path.is_file() else b""
        verdicts.append(
            toolbox.verdict(
                f"verdict-archive-{label}",
                bool(raw) and not _has_carriage_return(raw),
                "missing/empty" if not raw else "contains CR",
            )
        )
    press_path = root / PRESS_ARCHIVE
    press_raw = press_path.read_bytes() if press_path.is_file() else b""
    verdicts.append(
        toolbox.verdict(
            "press-archive-is-binary-safe",
            bool(press_raw) and not _has_carriage_return(press_raw),
            "missing/empty" if not press_raw else "contains CR",
        )
    )
    return verdicts


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """两处射程**纯收紧**：`IN_SCOPE`（四道门）与**射程分区清单**（判据面）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    verifier_text = _text(root, VERIFIER_JUDGE)
    return [
        toolbox.verdict("scope-declares-this-rounds-scripts", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-still-pins-the-entry",
            {"tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py"} <= declared,
        ),
        toolbox.verdict(
            "verifier-scope-declares-this-rounds-scripts",
            SELF in verifier_text,
            "GOAL-043 立的射程分区清单也必须登记本轮验证器",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（每条都能被单变量按压判红）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
