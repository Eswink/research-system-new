"""记录面**受门覆盖**的机器判据（GOAL-20260926-020 EC-02）。

判什么（缺一不可）：

1. **记录面非空** —— 否则后面的「扫得到」都会退化成空断言；
2. **每个记录面都被至少一条门判据覆盖**，且覆盖是**按符号 / 按行为**取证的，
   不是靠文档里的一句话：
   - `test_reproducibility_wording.py` 的 `_SCAN_ROOTS`（**符号值**）；
   - 该判据自己的 walker `_scan_files()` 的**实际产出**（行为：光有常量不算覆盖）；
   - `tools/credential_audit.py` 的 `RECORDS_DIR`（符号值）；
   - 治理 `validate.py` 的 `iter_cursor_text_files()` 的**实际产出**（行为，
     它是 `.cursor/**` 的链接 / 凭据扫描面）；
3. **未覆盖面被如实登记** —— 本仓实测：`.cursor/memory/entries` **不在**话术判据与
   凭据审计的记录面里（它只由治理与版本 / 链接扫描覆盖）。这条**如实断言**，
   免得「已覆盖」被读成比事实更强；将来有人补上覆盖，这里会红并提示更新记录；
4. **这些判据在门里** —— 由 runner 的**实际常量**推「它们属于门选中的 check」；
5. **SOP 的顺序条款点名一个存在的判据文件** —— 改名即判红，条款不得悬空。

为什么需要它（缺陷的真实形状）：记录面**并非从未被扫**——`python/tests` 与 framework 组
本来就会扫 `.cursor/plans`。真正的缺陷是**时间性**的：本地旧 SOP 把全量门跑在
**记录写入之前** ⇒ 那次结论对「当时还不存在的记录内容」不成立（GOAL-019 的记录提交
`75155b2` 因此只在 CI 判红）。所以本判据的职责是：**让「记录面在受判集合内、且由哪些判据
覆盖」在每一次门运行里都是被机器复核过的事实**——任何人删掉扫描根、换掉 walker、
或把记录面判据挪出门的收集面，这里都会红。
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[3]

WORDING_JUDGE = REPO_ROOT / "tests" / "architecture" / "python" / "test_reproducibility_wording.py"
CREDENTIAL_AUDIT = REPO_ROOT / "tools" / "credential_audit.py"
GOVERNANCE = REPO_ROOT / ".cursor" / "skills" / "governance-check" / "scripts" / "validate.py"
RUNNER = (
    REPO_ROOT / ".cursor" / "skills" / "cursor-framework-check" / "scripts" / "run_all_checks.py"
)
PROTOCOL_DOC = REPO_ROOT / "docs" / "architecture" / "LOCAL_GATE_PROTOCOL.md"

#: 记录面根（内容受判的目录）。**两个**：计划与复检、工程记忆。
RECORD_FACE_ROOTS: tuple[str, ...] = (".cursor/plans", ".cursor/memory/entries")

#: 本仓**实测**的未覆盖面：这两条门**不**覆盖工程记忆面（如实断言，不是待办）。
#: 若将来补上覆盖，下面的用例会判红 ⇒ 提示把记录更新到与事实一致。
UNCOVERED_BY: dict[str, str] = {
    "test_reproducibility_wording.py": ".cursor/memory/entries",
    "credential_audit.py": ".cursor/memory/entries",
}

#: SOP 里「记录面覆盖」条款必须点名的**判据文件名**（改名即判红 ⇒ 条款不得悬空）：
#: ①受判的记录面判据（覆盖的对象）；②本判据自己（覆盖的**机械保证**）。
SOP_NAMED_CRITERIA: tuple[str, ...] = (
    "test_reproducibility_wording.py",
    "test_record_face_is_covered_by_the_gate.py",
)

#: 承载顺序条款的小节标题（该节**之内**必须点名上面两个判据；节外提及不算）。
SOP_SECTION = "### 记录面覆盖（GOAL-020 EC-02）：门必须在记录写入**之后**跑"


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"无法加载模块: {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _scan_roots() -> tuple[str, ...]:
    roots = getattr(_load(WORDING_JUDGE, "goal020_wording_judge"), "_SCAN_ROOTS", None)
    assert isinstance(roots, tuple), "_SCAN_ROOTS 不再是元组 —— 判据形状假设失效"
    return roots


def _yielded_paths(producer: object, label: str) -> list[Path]:
    assert callable(producer), f"{label} 不可调用 —— 无法验证「真的扫到了」"
    produced = producer()
    assert isinstance(produced, (Iterator, Sequence)), f"{label} 不再是可迭代产出"
    return [Path(item) for item in produced]


def _faces_hit(paths: Sequence[Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for face in RECORD_FACE_ROOTS:
        counts[face] = sum(1 for path in paths if face in path.as_posix())
    return counts


def test_record_faces_are_not_empty_so_coverage_assertions_are_not_vacuous() -> None:
    for face in RECORD_FACE_ROOTS:
        base = REPO_ROOT / face
        assert base.is_dir(), f"记录面目录不存在: {face}"
        assert any(base.rglob("*.md")), f"记录面为空: {face}"


def test_the_wording_judge_names_the_plan_record_face_in_its_scan_roots() -> None:
    """符号值取证：计划 / 复检面必须在话术判据的扫描根里。"""
    roots = _scan_roots()
    assert ".cursor/plans" in roots, f"计划面不在 _SCAN_ROOTS 里：{roots}"


def test_the_wording_judge_actually_yields_files_from_the_plan_record_face() -> None:
    """行为取证：有扫描根常量还不够，walker 必须真的产出记录面文件。"""
    module = _load(WORDING_JUDGE, "goal020_wording_judge_walk")
    yielded = _yielded_paths(getattr(module, "_scan_files", None), "_scan_files")
    assert yielded, "_scan_files() 没有产出任何文件 —— 判据扫描面失效"
    hits = _faces_hit(yielded)
    assert hits[".cursor/plans"] > 0, (
        "_scan_files() 一个计划面文件都没扫到；覆盖只是名义上的。"
        f"产出示例：{[p.as_posix() for p in yielded[:5]]}"
    )


def test_the_credential_audit_names_the_plan_record_face() -> None:
    records_dir = getattr(_load(CREDENTIAL_AUDIT, "goal020_credential_audit"), "RECORDS_DIR", None)
    assert isinstance(records_dir, str), "credential_audit.RECORDS_DIR 不再是字符串"
    assert records_dir == ".cursor/plans", (
        f"凭据审计的记录面已变（{records_dir!r}）⇒ 需复核本判据登记的覆盖面"
    )


def test_the_governance_scan_reaches_both_record_faces() -> None:
    """治理的 `.cursor/**` 文本扫描面必须**实际**够到两个记录面（行为取证）。"""
    module = _load(GOVERNANCE, "goal020_governance_validate")
    yielded = _yielded_paths(
        getattr(module, "iter_cursor_text_files", None), "iter_cursor_text_files"
    )
    assert yielded, "iter_cursor_text_files() 没有产出任何文件 —— 治理扫描面失效"
    hits = _faces_hit(yielded)
    for face in RECORD_FACE_ROOTS:
        assert hits[face] > 0, f"治理扫描面没够到 {face}（命中 {hits[face]} 个文件）"


def test_the_recorded_uncovered_ranges_are_still_accurate() -> None:
    """未覆盖面**如实登记**：这两条门今天**不**覆盖工程记忆面。

    本用例是「记录与事实一致」的守卫，不是待办：若有人给它们补上覆盖，
    这里会判红，提示把 `UNCOVERED_BY` 与本文件的说明更新到与事实一致。
    """
    memory_face = ".cursor/memory/entries"
    assert memory_face not in _scan_roots(), (
        f"话术判据现在覆盖了 {memory_face} ⇒ 请更新 UNCOVERED_BY 与文档里的未覆盖范围"
    )
    records_dir = getattr(
        _load(CREDENTIAL_AUDIT, "goal020_credential_audit_uncovered"), "RECORDS_DIR", ""
    )
    assert records_dir != memory_face, (
        f"凭据审计现在覆盖了 {memory_face} ⇒ 请更新 UNCOVERED_BY 与文档里的未覆盖范围"
    )
    assert set(UNCOVERED_BY.values()) == {memory_face}, "登记的未覆盖面与断言不一致"
    for face in RECORD_FACE_ROOTS:
        assert face.strip(), f"记录面常量不得为空: {face!r}"


def test_the_record_face_judges_are_inside_the_gate_collection_surface() -> None:
    """由 runner 的**实际常量**推「这些判据在门里」，不靠声明。"""
    runner = _load(RUNNER, "goal020_runner")
    ignored = _runner_ignored_test()
    assert ignored.endswith("test_dependency_boundaries.py"), f"被 ignore 的不是边界判据: {ignored}"
    assert not any(name in ignored for name in SOP_NAMED_CRITERIA), (
        "记录面判据自身被排除在门的收集面之外"
    )
    framework_scripts = getattr(runner, "FRAMEWORK_SCRIPTS", None)
    assert isinstance(framework_scripts, tuple) and framework_scripts, "FRAMEWORK_SCRIPTS 失效"
    joined = " ".join(framework_scripts)
    for needle in ("validate_bundle.py", "governance-check"):
        assert needle in joined, f"读记录面的 framework 判据不在门里: {needle}"


def _runner_ignored_test() -> str:
    """从 runner 源码里取 `python/tests` 实际 ignore 的那个判据路径（AST，不执行）。"""
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "boundary_test":
                value = node.value
                assert isinstance(value, ast.Constant) and isinstance(value.value, str)
                return value.value
    raise AssertionError("runner 里找不到 boundary_test 定义 —— 判据形状假设失效")


def _sop_section_text() -> str:
    """取 SOP 里承载顺序条款的**那一节**（到下一个同级标题为止）。节外提及不算数。"""
    text = PROTOCOL_DOC.read_text(encoding="utf-8")
    assert SOP_SECTION in text, (
        f"{PROTOCOL_DOC.name} 缺少顺序条款小节 {SOP_SECTION!r} —— 条款不得悬空"
    )
    start = text.index(SOP_SECTION)
    rest = text[start + len(SOP_SECTION) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_the_sop_order_clause_names_criteria_that_exist() -> None:
    """顺序条款**所在小节内**必须点名两个判据文件，且它们都真的存在（条款不得悬空）。

    判据读的是**小节内文本**而不是整篇文档：文件名在别处出现（例如本文档第 1 节的
    支持跑法表）**不算**条款履行——这正是本条第一次按压没红的原因。
    """
    section = _sop_section_text()
    for name in SOP_NAMED_CRITERIA:
        assert name in section, f"顺序条款小节未点名记录面判据 {name} —— 条款悬空（节外提及不算）"
        named = REPO_ROOT / "tests" / "architecture" / "python" / name
        assert named.is_file(), f"条款点名的判据不存在: {named.relative_to(REPO_ROOT)}"
