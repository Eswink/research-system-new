#!/usr/bin/env python3
"""GOAL-20261013-070 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…069 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-070 特有的断言**。

三条主轴（逐条对 GOAL-070 的 EC）：

1. **EC-02 声明出来**：`run_events` 的签名**声明** `cursor` / `poll`（`Query(` 形态）；
   **不再**从原始 `request.query_params` 读（本轮的靶子形态）；未知参数**被点名**
   （守卫自动接管的**行为**在判据面）；`Last-Event-ID` 头路径**仍在**（头优先）。
2. **EC-03 射程如实**：SSE 帧格式判据仍在树；序 37 的判据**仍在树**（本轮**未**改它
   的**断言**，只把受判面清单 9→10 **扩大** —— 该清单是「app 声明面投影」的**设计行为**）；
   快照**同轮**（+31/−1 如实登记为本轮**预期变化**）。
3. **EC-04 两向反证**：四条按压的受判面逐条在树（V-1…V-4 各自的用例名）；归档进树（`CR=0`）。

**五条纪律**（承 GOAL-027…069）：不读两树判词；判词行不含绝对路径；f-string 分片按**子串**；
`defines` 收**含类方法**的版本；**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/api/test_event_stream_declares_query_parameters.py", 7),
    ("tests/api/test_unknown_query_params_cover_every_declared_route.py", 11),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/api/test_runs_api.py",
    "tools/verify_goal069_closeout.py",
)

#: EC-02 / EC-03 落点。
ROUTER = "services/api/routers/run_events.py"
NEW_JUDGE = "tests/api/test_event_stream_declares_query_parameters.py"
PRIOR_JUDGE = "tests/api/test_unknown_query_params_cover_every_declared_route.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: 本轮引入的形态（**逐条点名**；缺一即判红）。
DECLARED = "Query("
PARAMS: tuple[str, ...] = ("cursor", "poll")
HEADER_PATH = "Last-Event-ID"

#: EC-04 归档落点。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261013-070-press-two-way.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal070_closeout.py"
ASSERTIONS = "tools/goal070_closeout_assertions.py"

#: V-1…V-4 各自的**受判面用例名**（判据面必须在树；按压读数由归档承担）。
_PRESS_JUDGES: tuple[tuple[str, str], ...] = (
    ("V-1", "test_the_stream_declares_the_parameters_it_consumes"),
    ("V-2", "test_the_stream_declares_the_parameters_it_consumes"),
    ("V-3", "test_the_known_forms_are_verbatim"),
    ("V-4", "test_the_header_path_is_untouched"),
)


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：声明（`Query(` + 两个参数名）+ **不再**原始读 + 头路径 + 判据面。"""
    router = _text(root, ROUTER)
    judge = _text(root, NEW_JUDGE)
    declared_names = [name for name in PARAMS if f"{name}: str" in router]
    return [
        toolbox.verdict(
            "ec02-the-params-are-declared-in-the-signature",
            DECLARED in router and len(declared_names) == len(PARAMS),
            ",".join(declared_names) or "两个参数都要以 `Query(` 声明进签名",
        ),
        toolbox.verdict(
            "ec02-the-raw-query-read-is-gone",
            # **判调用形态**（`.get(` / `[`），**不**判散文字符串 —— docstring 里
            # 点名「此前从它读」正是本轮要记的事（承序 36 的 `exclude_none` 教训：
            # 按短语判会被**解释为何不用它**的注释命中 ⇒ 假红）。
            "request.query_params.get(" not in router and "request.query_params[" not in router,
            "**不得**再从原始 `request.query_params` 读（本轮靶子形态：消费却不声明）",
        ),
        toolbox.verdict(
            "ec02-the-header-path-survives",
            HEADER_PATH in router,
            "`Last-Event-ID` 头路径必须仍在（头优先的 `or` 短路逐字保留）",
        ),
        toolbox.verdict(
            "ec02-the-unknown-param-is-named",
            "unknown query parameter" in judge.lower() or "po11" in judge,
            "未知参数的**点名**必须在判据面（守卫自动接管的可观测证据）",
        ),
        toolbox.verdict(
            "ec02-the-judge-pins-the-declared-default",
            "default" in judge and '"1"' in judge,
            "**声明缺省**必须被钉（`V-2` 首跑的判据缺口形态：缺省无人钉 ⇒ 按压假绿）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：SSE 帧判据 + 序 37 判据在树 + 快照同轮 + 清零的射程登记。"""
    judge = _text(root, NEW_JUDGE)
    prior = _text(root, PRIOR_JUDGE)
    return [
        toolbox.verdict(
            "ec03-the-sse-frame-judge-is-in-tree",
            "event: " in judge and "data: " in judge,
            "SSE 帧格式（`id:` / `event:` / `data:`）的判据必须在树（帧契约不动）",
        ),
        toolbox.verdict(
            "ec03-the-prior-judge-registers-the-new-route",
            "/runs/run-missing/events" in prior or "{run_id}/events" in prior,
            # 序 37 的受判面清单**扩大**到 10 条（app 声明面投影的设计行为）
            "序 37 的受判面清单必须含本轮新声明的路由（清单 = app 声明面投影）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-is-in-tree",
            (root / SNAPSHOT).is_file(),
            "快照必须仍在树（本轮**预期变化**并同轮提交）",
        ),
        toolbox.verdict(
            "ec03-the-snapshot-declares-both-params",
            all(f'"{name}"' in _text(root, SNAPSHOT) for name in PARAMS),
            "快照必须反映两个声明（`cursor` / `poll`）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态 + TIMEOUT 形态。"""
    judge = _text(root, NEW_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    verdicts: list[Any] = [
        toolbox.verdict(
            f"ec04-the-{label.lower()}-arm-is-asserted",
            name in judge,
            f"`{label}` 的受判面必须在树",
        )
        for label, name in _PRESS_JUDGES
    ]
    verdicts.extend([
        toolbox.verdict(
            "ec04-the-baseline-gate-is-in-the-archive",
            "BASELINE" in press and "GREEN" in press,
            "归档必须含**基线行**（未按压不得红 —— 一级纪律）",
        ),
        toolbox.verdict(
            "ec04-every-press-is-red-in-the-archive",
            press.count("按压 RED") >= 4 and "all_red_and_restored=True" in press,
            "四条的读数必须全红且复原一致",
        ),
        toolbox.verdict(
            "ec04-the-archive-records-byte-exact-restore",
            press.count("sha 复原一致=True") >= 4,
            "逐条 raw sha256 复原一致（二进制读写）",
        ),
        toolbox.verdict(
            "ec04-the-timeout-arm-is-registered",
            "TIMEOUT" in press,
            "`V-3` 的 RED 形态 = TIMEOUT（无限流挂死）必须如实登记在归档里",
        ),
    ])
    return verdicts


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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…069 的教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：按压判词归档形态（非空、`CR=0`）。**不读内容做断言**（输入即输出）。"""
    path = root / PRESS_ARCHIVE
    raw = path.read_bytes() if path.is_file() else b""
    return [
        toolbox.verdict(
            "press-archive-is-binary-safe",
            bool(raw) and not _has_carriage_return(raw),
            "missing/empty" if not raw else "contains CR",
        )
    ]


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """两处射程**纯收紧**：`IN_SCOPE`（四道门）与**射程分区清单**（判据面）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    verifiers = toolbox.module_literal(_text(root, VERIFIER_JUDGE), "_VERIFIERS")
    registered = isinstance(verifiers, tuple) and SELF in verifiers
    return [
        toolbox.verdict("scope-in-scope-pure-tightening", not missing, ",".join(missing)),
        toolbox.verdict("scope-verifier-registered", registered),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的特有断言（收口验证器唯一入口）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
