"""GOAL-20260928-023 EC-03 判据：受判射程的**边界**是机械事实，不是散文。

**判什么**（**只判边界，不判射程内记录的实质质量** —— 由
`test_the_boundary_judgement_is_indifferent_to_record_quality` 以行为证明）：

1. **受判起点**：既有判据 `test_declared_recheck_paths_have_evidence.py` 的 `CUTOFF`
   逐字等于 `2026-09-28`，slug 约定与「至少几路」的下界也与绑定值一致；
2. **射程外清单恰好是四条历史收口复检**（逐条点名 `goal-018` / `019` / `020` / `021`），
   **没有第五个**；
3. **射程内计数** ≥ 1，且与射程外**互斥**；
4. **两向反证**（hermetic，`tmp_path`）：
   ① 一条**新**收口复检被回填到起点**之前** ⇒ 判红（防 **backdate 逃逸**）；
   ② 一条**历史**记录被改成**在射程内** ⇒ 判红（防**回填历史**）。

**为什么**：`RECHECK-20260928-218` 的 `W-1` 说「四条历史收口复检在射程外」——
那当时只是**散文**。散文不会自己失效，失效的是**它描述的事实**：一条新记录一旦被回填，
或一条历史记录一旦被改写，射程边界就**静默改变**了，而没有任何东西会说话。
本判据把边界钉成可复核事实；**不修改**既有那条判据，只读它的公开面（`CUTOFF` /
`CLOSEOUT_SLUG_SUFFIX` / `MIN_DECLARED_PATHS` / `is_obligated` / `closeout_records`）。
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
RECHECKS_DIR = ROOT / ".cursor" / "plans" / "rechecks"
PATHS_JUDGE = (
    ROOT / "tests" / "architecture" / "python" / "test_declared_recheck_paths_have_evidence.py"
)

#: 受判起点（由既有判据的 `CUTOFF` 提供；这里绑定**期望值**以便它漂移时判红）。
EXPECTED_CUTOFF = date(2026, 9, 28)

#: 收口复检的 slug 后缀（既有约定）。
EXPECTED_SUFFIX = "closeout-recheck"

#: 收口复检至少要声明几路（规范页「必须两树」推出的下界）。
EXPECTED_MIN_PATHS = 2

#: **射程外清单**：恰好这四条历史收口复检（逐条点名，多一条少一条都判红）。
EXPECTED_OUT_OF_SCOPE: tuple[str, ...] = (
    "RECHECK-20260926-189-goal-018-closeout-recheck.md",
    "RECHECK-20260926-195-goal-019-closeout-recheck.md",
    "RECHECK-20260926-200-goal-020-closeout-recheck.md",
    "RECHECK-20260927-210-goal-021-closeout-recheck.md",
)

#: 射程内至少要有几条（`goal-022` 的收口复检建档当日进入射程）。
MIN_IN_SCOPE = 1

_FIXTURE_ID = "RECHECK-20260101-901"
_FIXTURE_TEXT = "\n".join([
    "---",
    f"id: {_FIXTURE_ID}",
    "slug: goal-901-closeout-recheck",
    "status: COMPLETED",
    "result: PASS",
    "created_at: {created}",
    "completed_at: {created}",
    "owners:",
    "  - root-agent",
    "---",
    "",
    "# fixture",
    "",
])


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"无法加载模块: {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def boundary_module() -> ModuleType:
    """既有那条判据（**只读**其公开面；本判据不改它一个字）。"""
    assert PATHS_JUDGE.is_file(), f"既有判据不在树：{PATHS_JUDGE}"
    return _load(PATHS_JUDGE, "goal023_paths_judge")


def partition(directory: Path) -> tuple[list[str], list[str]]:
    """把一个目录里的收口复检按**既有判据的** `is_obligated` 分成 (射程内, 射程外)。"""
    module = boundary_module()
    inside: list[str] = []
    outside: list[str] = []
    for path, metadata, _body in sorted(module.closeout_records(directory)):
        (inside if module.is_obligated(metadata) else outside).append(path.name)
    return inside, outside


def boundary_problems(directory: Path) -> list[str]:
    """边界问题清单（空 = 边界成立）。**只看边界**，不看记录写得怎么样。"""
    inside, outside = partition(directory)
    problems: list[str] = []
    expected = set(EXPECTED_OUT_OF_SCOPE)
    found = set(outside)
    for name in sorted(expected - found):
        problems.append(f"{name} 不再落在射程外（被回填进了射程）")
    for name in sorted(found - expected):
        problems.append(f"{name} 落在射程外，但它不在登记的射程外清单里（疑似 backdate）")
    if len(inside) < MIN_IN_SCOPE:
        problems.append(f"射程内只有 {len(inside)} 条，下界是 {MIN_IN_SCOPE}")
    overlap = sorted(set(inside) & set(outside))
    if overlap:
        problems.append(f"同一条记录同时落在射程内外：{overlap}")
    return problems


def _write_record(directory: Path, name: str, created: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    target.write_text(_FIXTURE_TEXT.format(created=created), encoding="utf-8", newline="")
    return target


def _expected_fixtures(directory: Path) -> None:
    """四条历史收口复检（全部早于受判起点）。"""
    for name in EXPECTED_OUT_OF_SCOPE:
        _write_record(directory, name, "2026-09-26")


def test_the_existing_judge_still_pins_the_boundary_constants() -> None:
    """受判起点 / slug 约定 / 路数下界：既有判据的公开面仍与绑定值一致。"""
    module = boundary_module()
    assert module.CUTOFF == EXPECTED_CUTOFF, f"受判起点变了：{module.CUTOFF!r}"
    assert module.CLOSEOUT_SLUG_SUFFIX == EXPECTED_SUFFIX, (
        f"收口复检的 slug 约定变了：{module.CLOSEOUT_SLUG_SUFFIX!r}"
    )
    assert module.MIN_DECLARED_PATHS == EXPECTED_MIN_PATHS, (
        f"路数下界变了：{module.MIN_DECLARED_PATHS!r}"
    )


def test_the_out_of_scope_four_are_exactly_these_and_nothing_else() -> None:
    """**边界本身**：射程外恰好是那四条历史收口复检。"""
    inside, outside = partition(RECHECKS_DIR)
    assert sorted(outside) == sorted(EXPECTED_OUT_OF_SCOPE), (
        f"射程外清单变了：{sorted(outside)} != {sorted(EXPECTED_OUT_OF_SCOPE)}"
    )
    assert len(inside) >= MIN_IN_SCOPE, f"射程内只有 {len(inside)} 条 ⇒ 受判集合疑似为空"
    assert not set(inside) & set(outside), "同一条记录同时落在射程内外"
    assert not boundary_problems(RECHECKS_DIR), "; ".join(boundary_problems(RECHECKS_DIR))


def test_the_scan_face_covers_both_sides() -> None:
    """扫描面 = 射程内 + 射程外；任一边为空 ⇒ 本判据的断言失去意义。"""
    inside, outside = partition(RECHECKS_DIR)
    assert inside, "射程内为空 ⇒ 本判据对射程内没有任何受判对象"
    assert outside, "射程外为空 ⇒ 疑似有人把历史记录回填进了射程"


def test_a_backdated_new_closeout_recheck_is_caught(tmp_path: Path) -> None:
    """**反证 ①**：新收口复检被回填到起点之前 ⇒ 判红（防 backdate 逃逸）。"""
    _expected_fixtures(tmp_path)
    newcomer = "RECHECK-20260928-902-goal-900-closeout-recheck.md"
    _write_record(tmp_path, newcomer, "2026-09-28")
    assert not boundary_problems(tmp_path), "合法的边界不应判红"
    _write_record(tmp_path, newcomer, "2026-09-27")
    problems = boundary_problems(tmp_path)
    assert any(newcomer in item for item in problems), problems


def test_a_backfilled_historical_record_is_caught(tmp_path: Path) -> None:
    """**反证 ②**：历史记录被改成在射程内 ⇒ 判红（防回填历史）。"""
    _expected_fixtures(tmp_path)
    _write_record(tmp_path, "RECHECK-20260928-903-goal-903-closeout-recheck.md", "2026-09-28")
    target = EXPECTED_OUT_OF_SCOPE[0]
    assert not boundary_problems(tmp_path), "合法的边界不应判红"
    _write_record(tmp_path, target, "2026-09-28")
    problems = boundary_problems(tmp_path)
    assert any(target in item for item in problems), problems


def test_the_boundary_judgement_is_indifferent_to_record_quality(tmp_path: Path) -> None:
    """**只判边界，不判质量**（行为证明）：质量全坏的记录，只要边界对，就不判红。

    这条同时是「本判据不冒充质量判据」的登记：射程内记录的实质质量仍由
    `test_declared_recheck_paths_have_evidence.py` 承载，**不**由本判据承载。
    """
    _expected_fixtures(tmp_path)
    _write_record(tmp_path, _FIXTURE_ID + "-goal-900-closeout-recheck.md", "2026-09-28")
    assert not boundary_problems(tmp_path), (
        "本判据对记录质量说话了 ⇒ 它越权了（质量判据是既有那条）"
    )
