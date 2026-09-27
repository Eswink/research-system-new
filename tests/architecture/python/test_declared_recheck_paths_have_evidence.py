"""GOAL-20260928-022 EC-02 判据：声明的路数必须与各自的留档证据对得上。

**判什么**（把 GOAL-021 的 `W-0` 机械化）：**收口复检**（`slug` 以 `closeout-recheck`
结尾）**必须**在 frontmatter 里用 `verify_paths` 声明它跑过的**每一路**，
且**每一路各自**有一个留档证据引用：

1. 路数 **≥ 2**——因为规范页的条款写明「**收口复检必须两树**」
   （`docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md`）⇒ 「只跑一路就记 PASS」判红；
2. 每条证据引用**互不相同**（两路共用一份证据 = 实际只跑了一路）；
3. 每条证据引用**必须在记录正文里被引用过**（声明了却从不提及 = 悬空）；
4. 证据引用若指向仓库内路径（不以 `scratch/` 开头）则**必须存在**——
   `scratch/` 是 gitignored 的判词归档落点，允许只引用不随身（任务书口径）。

**判据绑的是结构化字段**（`slug` / `created_at` / `verify_paths`，加上正文里的
**引用字符串**），**不是**散文措辞 —— 承 `MEM-20260925-141`：用语法结构判，
不要用文本巧合判。`test_the_judgement_ignores_prose_wording` 就是这件事的实证：
把条款文字改写成别的说法、或反过来只在散文里声称跑了两路，**都不改变**判据结论。

**射程边界（如实登记）**：`created_at` 早于本 GOAL 建档日（2026-09-28）的历史收口复检
**不在**受判集合内 —— 那些记录是**不可变证据**，回填等于改写历史。
该剩余面由 `test_historical_closeout_rechecks_remain_out_of_scope` **逐条登记**，
**不得**读成「全仓已覆盖」。

夹具（合成 RECHECK）由本判据在 `tmp_path` 里运行时生成，不落进仓库。
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
RECHECKS_DIR = ROOT / ".cursor" / "plans" / "rechecks"
GOVERNANCE = ROOT / ".cursor" / "skills" / "governance-check" / "scripts" / "validate.py"

#: 收口复检的 slug 后缀（本仓既有约定：`goal-018-closeout-recheck` … `goal-021-closeout-recheck`）。
CLOSEOUT_SLUG_SUFFIX = "closeout-recheck"

#: 受判起点：本 GOAL 建档日。此前的记录是不可变证据 ⇒ 不回填、不追溯。
CUTOFF = date(2026, 9, 28)

#: 收口复检至少要声明几路 —— 由规范页的「收口复检必须两树」条款推出。
MIN_DECLARED_PATHS = 2

#: 允许「只引用、不随身」的证据落点前缀（gitignored 的判词归档目录）。
EPHEMERAL_PREFIX = "scratch/"


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"无法加载模块: {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _frontmatter(path: Path) -> tuple[dict[str, object], str]:
    module = _load(GOVERNANCE, "goal022_governance_parse")
    metadata, body = module.parse_frontmatter(path)
    assert isinstance(metadata, dict), f"frontmatter 不是对象: {path}"
    return metadata, body


def _created_at(metadata: dict[str, object]) -> date | None:
    raw = metadata.get("created_at")
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None
    return None


def is_closeout(metadata: dict[str, object]) -> bool:
    slug = metadata.get("slug")
    return isinstance(slug, str) and slug.endswith(CLOSEOUT_SLUG_SUFFIX)


def is_obligated(metadata: dict[str, object]) -> bool:
    """受判集合 = 收口复检 **且** 建档日不早于受判起点。"""
    created = _created_at(metadata)
    return is_closeout(metadata) and created is not None and created >= CUTOFF


def declared_path_problems(metadata: dict[str, object], body: str, root: Path) -> list[str]:
    """按**结构化字段**判该记录的「路数 × 证据」；返回问题清单（空 = 合格）。"""
    declared = metadata.get("verify_paths")
    if not isinstance(declared, list) or not declared:
        return ["缺少 verify_paths（收口复检必须声明它跑过的每一路）"]
    problems: list[str] = []
    if len(declared) < MIN_DECLARED_PATHS:
        problems.append(
            f"只声明了 {len(declared)} 路，收口复检至少要 {MIN_DECLARED_PATHS} 路（必须两树）"
        )
    seen: dict[str, int] = {}
    for index, entry in enumerate(declared, start=1):
        if not isinstance(entry, dict):
            problems.append(f"第 {index} 路不是映射（缺 path / evidence）")
            continue
        label = str(entry.get("path") or "").strip()
        evidence = str(entry.get("evidence") or "").strip()
        if not label:
            problems.append(f"第 {index} 路缺少具名 path")
        if not evidence:
            problems.append(f"第 {index} 路缺少 evidence 引用")
            continue
        seen[evidence] = seen.get(evidence, 0) + 1
        if evidence not in body:
            problems.append(f"第 {index} 路的证据 {evidence!r} 在正文里从未被引用（悬空）")
        if not evidence.startswith(EPHEMERAL_PREFIX) and not (root / evidence).exists():
            problems.append(f"第 {index} 路的证据 {evidence!r} 不存在")
    shared = sorted(item for item, count in seen.items() if count > 1)
    for item in shared:
        problems.append(f"多条路共用同一份证据 {item!r} ⇒ 实际只跑了一路")
    return problems


def closeout_records(directory: Path) -> Iterator[tuple[Path, dict[str, object], str]]:
    for path in sorted(directory.glob("*.md")):
        metadata, body = _frontmatter(path)
        if is_closeout(metadata):
            yield path, metadata, body


def outstanding_closeout_records() -> list[tuple[Path, list[str]]]:
    """受判集合里每一条记录的问题清单（空清单 = 合格）。"""
    outstanding: list[tuple[Path, list[str]]] = []
    for path, metadata, body in closeout_records(RECHECKS_DIR):
        if not is_obligated(metadata):
            continue
        problems = declared_path_problems(metadata, body, ROOT)
        if problems:
            outstanding.append((path, problems))
    return outstanding


def _fixture(directory: Path, name: str, *, paths: list[dict[str, str]], prose: str = "") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"id: RECHECK-20260928-{name}",
        "slug: goal-022-closeout-recheck",
        "status: COMPLETED",
        "result: PASS",
        "created_at: 2026-09-28",
        "completed_at: 2026-09-28",
        "owners:",
        "  - root-agent",
    ]
    if paths:
        lines.append("verify_paths:")
        for entry in paths:
            lines.append(f"  - path: {entry['path']}")
            lines.append(f"    evidence: {entry['evidence']}")
    lines.extend(["---", "", "# fixture", "", prose or "（无正文引用）", ""])
    target = directory / f"RECHECK-20260928-{name}.md"
    target.write_text("\n".join(lines), encoding="utf-8", newline="")
    return target


def _problems_of(path: Path) -> list[str]:
    metadata, body = _frontmatter(path)
    return declared_path_problems(metadata, body, ROOT)


def test_the_rechecks_directory_is_actually_scanned(tmp_path: Path) -> None:
    """非空断言：扫描面必须真的产出收口复检记录，否则后面的判据都是空断言。"""
    found = [path.name for path, _metadata, _body in closeout_records(RECHECKS_DIR)]
    assert found, f"{RECHECKS_DIR} 下一条收口复检都没扫到 ⇒ 扫描面失效（不是「都合格」）"
    assert RECHECKS_DIR.is_dir(), f"复检目录不存在: {RECHECKS_DIR}"


def test_historical_closeout_rechecks_remain_out_of_scope() -> None:
    """剩余面**如实登记**：建档日之前的历史收口复检不在受判集合内。

    这是「范围与事实一致」的守卫，不是待办：若有人给它们回填 `verify_paths`
    （改写历史证据），本用例会判红并提示更新登记。
    """
    historical = [
        path.name
        for path, metadata, _body in closeout_records(RECHECKS_DIR)
        if not is_obligated(metadata)
    ]
    obligated = [
        path.name
        for path, metadata, _body in closeout_records(RECHECKS_DIR)
        if is_obligated(metadata)
    ]
    assert historical, "一条历史收口复检都没有 ⇒ 扫描面或 slug 约定变了，需复核本判据"
    assert not set(historical) & set(obligated), "历史与受判集合不应重叠"
    for name in historical:
        _metadata = _frontmatter(RECHECKS_DIR / name)[0]
        assert not is_obligated(_metadata), f"{name} 不应落在受判集合内"


def test_no_obligated_closeout_recheck_has_a_declaration_gap() -> None:
    """受判集合内每一条记录都必须「路数 ≥ 2 且各自有独立、被引用的证据」。"""
    outstanding = outstanding_closeout_records()
    assert not outstanding, "有收口复检的「路数 × 证据」对不上：" + "; ".join(
        f"{path.name}: {problems}" for path, problems in outstanding
    )


def test_two_paths_sharing_one_evidence_are_rejected(tmp_path: Path) -> None:
    """**按压**：声明两路但共用同一份证据 ⇒ 判红（正是 GOAL-021 `W-0` 的形态）。"""
    record = _fixture(
        tmp_path,
        "001",
        paths=[
            {"path": "当前树", "evidence": "scratch/one-verdict.txt"},
            {"path": "干净 checkout", "evidence": "scratch/one-verdict.txt"},
        ],
        prose="见 scratch/one-verdict.txt。",
    )
    problems = _problems_of(record)
    assert any("共用同一份证据" in item for item in problems), problems


def test_a_single_declared_path_is_rejected(tmp_path: Path) -> None:
    """**「只跑一路」判红**：路数 < 2 ⇒ 判红（收口复检必须两树）。"""
    record = _fixture(
        tmp_path,
        "002",
        paths=[{"path": "当前树", "evidence": "scratch/only-one.txt"}],
        prose="见 scratch/only-one.txt。",
    )
    problems = _problems_of(record)
    assert any("至少要 2 路" in item for item in problems), problems


def test_two_paths_with_distinct_cited_evidence_pass(tmp_path: Path) -> None:
    """补齐两路各自独立、且在正文里被引用的证据 ⇒ 绿。"""
    record = _fixture(
        tmp_path,
        "003",
        paths=[
            {"path": "当前树", "evidence": "scratch/current.txt"},
            {"path": "干净 checkout", "evidence": "scratch/clean.txt"},
        ],
        prose="当前树判词见 scratch/current.txt；干净 checkout 见 scratch/clean.txt。",
    )
    assert _problems_of(record) == []


def test_uncited_evidence_is_rejected(tmp_path: Path) -> None:
    """声明了却从不提及 ⇒ 悬空 ⇒ 判红。"""
    record = _fixture(
        tmp_path,
        "004",
        paths=[
            {"path": "当前树", "evidence": "scratch/current.txt"},
            {"path": "干净 checkout", "evidence": "scratch/clean.txt"},
        ],
        prose="（正文没有引用任何证据）",
    )
    problems = _problems_of(record)
    assert any("从未被引用" in item for item in problems), problems


def test_a_missing_tracked_evidence_file_is_rejected(tmp_path: Path) -> None:
    """指向仓库内路径的证据必须真的存在（`scratch/` 归档落点豁免）。"""
    record = _fixture(
        tmp_path,
        "005",
        paths=[
            {"path": "当前树", "evidence": "docs/architecture/no-such-file.md"},
            {"path": "干净 checkout", "evidence": "scratch/clean.txt"},
        ],
        prose="见 docs/architecture/no-such-file.md 与 scratch/clean.txt。",
    )
    problems = _problems_of(record)
    assert any("不存在" in item for item in problems), problems


def test_the_judgement_ignores_prose_wording() -> None:
    """**未被字面量喂饱的实证**：判据读结构化字段，不读条款文字。

    两面各自可判：① 把条款文字**改写成别的说法**（正文完全不提「两树」）但字段齐全
    ⇒ 仍然通过；② 反过来**只在散文里声称**跑了两路、字段却只有一条 ⇒ 仍然判红。
    ⇒ 判据的结论**不随措辞改变**，只随声明改变（承 `MEM-20260925-141`）。
    """
    import tempfile

    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        structured = _fixture(
            directory,
            "006",
            paths=[
                {"path": "first", "evidence": "scratch/a.txt"},
                {"path": "second", "evidence": "scratch/b.txt"},
            ],
            prose="两条路的留档分别是 scratch/a.txt 与 scratch/b.txt。",
        )
        assert _problems_of(structured) == [], "字段齐全时不应因措辞不同而判红"
        prose_only = _fixture(
            directory,
            "007",
            paths=[{"path": "唯一一路", "evidence": "scratch/only.txt"}],
            prose="本轮在**当前树**与**干净 checkout** 两处各自实跑（只在散文里这么写）。",
        )
        problems = _problems_of(prose_only)
        assert problems, "只在散文里声称两路、字段却只有一条 ⇒ 必须判红（否则判据被措辞喂饱）"
        assert any("至少要 2 路" in item for item in problems), problems
