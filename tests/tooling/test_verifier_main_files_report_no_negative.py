"""GOAL-20261030-101 EC-02 判据：**验证器主文件里的断言也要在负判扫描面内**。

**它补哪一格**（本 GOAL 建档时实测到的真缺陷，第四轮同一族）：

`tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的三条判负扫描
（`test_every_named_assertion_set_reports_no_negative_on_this_tree` 等）**只跑断言集模块**
（`goal0NN_closeout_assertions.py`），而 `progress-records-this-goal` /
`progress-row-names-the-recheck` 这两条断言住在 `verify_goal0NN_closeout.py` 的**主文件**里
⇒ 它们的判负**从来不在任何判据的射程内**。

**实测后果**：14 个验证器各 **2 条假负**（进展行早已按归档惯例移入 `archive/`，而断言
只读活跃面），合计 **28 条**判负躺在**全绿**的树里。修之前跑一遍就能看见：

```text
$ uv run --frozen --no-sync python -B tools/verify_goal082_closeout.py --root . --verdict-only
FAIL progress-records-this-goal -> 宪章「进展记录」必须有本 GOAL 的一行（EC-05 契约逐字要求）
FAIL progress-row-names-the-recheck -> 进展记录那一行的 RECHECK 列必须指向本轮的复检文件
```

**为什么单列一个文件**（而不是加进那个判据文件）：那边贴着 450 行硬上限（规模门），
而「主文件侧面」是**可独立读**的一件事（判的是主文件，不是断言集）。同时那个文件里
有历史断言按**文件名**读它的 `_VERIFIERS` 清单（`goal046` 的
`verifier-scope-declares-this-rounds-scripts`）⇒ 把清单搬走会让它失配。故：**清单留在
原处**，本文件 `import` 它。

**判什么**（缺一即判红）：
1. 每个受判验证器的主文件在本树上 `record_verdicts(root)` **零判负**；
2. 射程非空（跑出判词的验证器个数有下界 —— 射程被清空时不许假绿）。

**两向反证**（`TestTheMainFileCriterionBites`）：在**最小合成树**上跑真验证器的
`record_verdicts`，证明两件事——
① 该 GOAL 的进展行**只在归档里** ⇒ 进展断言**全绿**（这是本 GOAL 修掉的假负形态）；
② 把归档里那一行也删掉 ⇒ 判据**必须报红并点名那两条**（不是「永远绿」）。

**射程边界（如实登记）**：本文件只调 `record_verdicts`（记录面），**不**调 `main()`
—— 那会重跑标准断言集与本轮断言集（原判据文件已覆盖），再跑一遍只是把时间翻倍，且会
掩盖「哪一侧坏了」。主文件里**没有** `record_verdicts` 的早期一代验证器由原文件的
`LEGACY_INLINE` 排除在射程外。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.tooling.test_closeout_verifiers_run_their_own_assertions import (
    _TOOLS,
    _VERIFIERS,
    _load_module,
)

_ROOT = Path(__file__).resolve().parents[2]

#: 主文件判据的射程下界（实测 73 个验证器有 `record_verdicts`；下界取 60 —— 只防「射程被
#: 清空」这一类，不钉精确条数：早期一代确实没有这一面，那是形态不同不是遗漏）。
_MIN_MAIN_FILES = 60

#: 「走共享 helper」的验证器下界（实测 16 个；下界取 14 —— 只防判据空转）。
_MIN_ON_HELPER = 14

#: **早期一代**里确实带 `record_verdicts` 的三个验证器（GOAL-20261101-103 EC-06）。
#:
#: 为什么单列：它们在 `LEGACY_INLINE` 里（没有外部断言集），因此**不在 `_VERIFIERS`**
#: —— 而 `_VERIFIERS` 是主文件判负扫描的唯一射程 ⇒ 这一代的主文件断言**从来不在任何
#: 判据的射程内**。GOAL-101 EC-02 修的是"`_VERIFIERS` 里的主文件没被扫"，本轮补的是
#: "有一整代根本不在 `_VERIFIERS` 里"。
#:
#: 三个都跑得动，但**签名不同**：026 是 `record_verdicts(root, factory)`（它从标准断言集
#: 取 `Verdict` 来造判词），028/029 是后来的一代 `record_verdicts(root)`。
#: 逐条登记签名而不是"统一调用"，因为把它们改成同一签名等于改历史资产的形状。
_EARLY_RECORD_VERIFIERS: tuple[str, ...] = (
    "tools/verify_goal026_closeout.py",
    "tools/verify_goal028_closeout.py",
    "tools/verify_goal029_closeout.py",
)

#: 需要 `(root, factory)` 两参签名的那些（逐条登记理由）。
_TWO_ARG_RECORD_VERIFIERS: frozenset[str] = frozenset({"tools/verify_goal026_closeout.py"})

#: 早期一代的射程下界（三个可跑；下界取 3 = 全部，因为这个名单本身是**闭集且经实测**）。
_MIN_EARLY_FILES = 3


def _verdict_factory(module: Any) -> Any:
    """从验证器**自己加载的标准断言集**里取 `Verdict` 工厂（与它 `main()` 同一条取法）。

    为什么不能自己造一个：判词对象的 `ok`/`name` 字段形状由那套标准断言集定义；造一个
    "长得像"的对象等于让本判据在**自己的替身**上判绿。026 的 `main()` 就是这么取的
    （`getattr(standard, "Verdict")`），本函数照抄。
    """
    path = _ROOT / getattr(module, "STANDARD", "tools/closeout_recheck_assertions.py")
    standard = _load_module(path, f"goal103_standard_for_{id(module)}")
    return getattr(standard, "Verdict")


def _early_record_verdicts(relative: str, root: Path) -> list[Any]:
    """跑一个**早期一代**验证器主文件的判词（按它自己的签名调用）。"""
    path = _ROOT.joinpath(*relative.split("/"))
    digits = relative.split("verify_goal", 1)[1].split("_", 1)[0]
    module = _load_module(path, f"goal103_early_{digits}")
    record = getattr(module, "record_verdicts", None)
    if record is None:
        return []
    if relative in _TWO_ARG_RECORD_VERIFIERS:
        return list(record(root, _verdict_factory(module)))
    return list(record(root))


def _main_record_verdicts(relative: str, root: Path) -> list[Any]:
    """跑某个验证器**主文件**的 `record_verdicts(root)`，返回它的判词。"""
    path = _ROOT.joinpath(*relative.split("/"))
    digits = relative.split("verify_goal", 1)[1].split("_", 1)[0]
    module = _load_module(path, f"goal101_main_{digits}")
    record = getattr(module, "record_verdicts", None)
    if record is None:
        return []
    verdicts: list[Any] = record(root)
    return list(verdicts)


def test_every_verifier_main_file_reports_no_negative_on_this_tree() -> None:
    """**验证器主文件**在本树上不得有判负（扫描面 = 主文件 ∪ 断言集，**两侧都跑**）。

    与 `test_every_named_assertion_set_reports_no_negative_on_this_tree` 成对：那条管
    断言集，这条管主文件。**两条合起来**才是「收口复检的判词集合里没有假负」。

    修复前实测 **28 条**假负（14 个验证器 × 2），而整棵树是绿的 —— 因为扫描面**不含**
    主文件。修法：读取面提为共享 helper（`tools/charter_progress.py`，活跃面或归档），
    再把主文件判负纳入射程（**先修后扩**，否则扩面即全红）。
    """
    negative: list[str] = []
    ran = 0
    for relative in _VERIFIERS:
        verdicts = _main_record_verdicts(relative, _ROOT)
        if verdicts:
            ran += 1
        failed = [item.name for item in verdicts if not item.ok]
        if failed:
            negative.append(f"{relative}: {failed}")
    assert ran >= _MIN_MAIN_FILES, (
        f"只有 {ran} 个验证器的主文件产出了判词（下界 {_MIN_MAIN_FILES}）⇒ 射程疑似被清空"
    )
    assert not negative, (
        "这些验证器**主文件**在本树上有判负 ⇒ 记录面断言失配（资产坏了，不是产品缺陷）",
        negative,
    )


def test_the_early_generation_verifiers_report_no_negative_too() -> None:
    """**早期一代**（`LEGACY_INLINE` 里带 `record_verdicts` 的那三个）也不得判负。

    它补的是 GOAL-101 EC-02 留下的那一格：那边把**`_VERIFIERS` 清单内**的主文件纳入
    射程，而 `LEGACY_INLINE` 登记的 9 个早期验证器**不在 `_VERIFIERS` 里** ⇒ 其中确实
    带 `record_verdicts` 的三个（026 / 028 / 029）**从来不在任何判据的射程内**。
    名单是**闭集**：新增早期验证器要显式加进来（与 `IN_SCOPE` 同一纪律）。
    """
    negative: list[str] = []
    ran = 0
    for relative in _EARLY_RECORD_VERIFIERS:
        verdicts = _early_record_verdicts(relative, _ROOT)
        if verdicts:
            ran += 1
        failed = [item.name for item in verdicts if not item.ok]
        if failed:
            negative.append(f"{relative}: {failed}")
    assert ran >= _MIN_EARLY_FILES, (
        f"只有 {ran} 个早期验证器产出了判词（下界 {_MIN_EARLY_FILES}）⇒ 射程疑似被清空"
    )
    assert not negative, (
        "这些**早期一代**验证器的主文件在本树上有判负 ⇒ 记录面断言失配",
        negative,
    )


def _synthetic_charter_tree(tmp_path: Path, *, goal_id: str, recheck_id: str) -> Path:
    """最小合成树：宪章（该 GOAL 只出现在阶梯里）+ 归档（进展行）+ GOAL 记录 + 探针记录。

    归档那份**不带** `## 进展记录` 小节标题 —— 历史归档确实有这种写法（实测 082…087
    四份），读取面必须按**行的形状**认（第二格是 GOAL id），不按小节标题认。
    """
    plans = tmp_path / ".cursor" / "plans"
    goals = plans / "goals"
    archive = goals / "archive"
    archive.mkdir(parents=True)
    (plans / "tasks").mkdir(parents=True)
    (plans / "rechecks").mkdir(parents=True)
    charter = (
        "# MAINLINE\n\n## 科研能力阶梯\n\n| 域 | 当前级 | 依据 GOAL | 下一级是什么 |\n"
        "| --- | --- | --- | --- |\n"
        f"| 迭代 | x | {goal_id} | y |\n\n"
        "## 进展记录\n\n| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 2026-01-02 | GOAL-20260102-902 | later round | 迭代 | [R](../../rechecks/R.md) |\n"
    )
    (goals / "MAINLINE.md").write_bytes(charter.encode("utf-8"))
    (archive / "MAINLINE-2026-01-01-probe.md").write_bytes(
        (
            "# MAINLINE 进展记录归档\n\n"
            f"| 2026-01-01 | {goal_id} | probe row | 迭代 | "
            f"[{recheck_id}](../../rechecks/{recheck_id}.md) |\n"
        ).encode("utf-8")
    )
    (goals / "GOAL-20260101-901-probe.md").write_bytes(
        (
            f"---\nid: {goal_id}\nstatus: ACHIEVED\n---\n\n## 残余与未覆盖范围\n\n- `W-1`｜probe\n"
        ).encode("utf-8")
    )
    for relative in (
        "tasks/PLAN-20260101-901-probe.md",
        "rechecks/RECHECK-20260101-901-probe.md",
    ):
        (plans / relative).write_bytes(b"# probe\n")
    return tmp_path


def _probe_verifier() -> Any:
    """装一个只认 `LADDER_GOAL` / `RECHECK_ID` 两个常量的验证器（092）。

    为什么不是 082：它的 RECHECK id 是**内联字面量**，改不动；092 把两个都提成了模块级
    常量 ⇒ 反证臂可以把它们指向合成树。
    """
    module = _load_module(_ROOT / "tools" / "verify_goal092_closeout.py", "goal101_probe_verifier")
    module.LADDER_GOAL = "GOAL-20260101-901"
    module.RECHECK_ID = "RECHECK-20260101-901"
    return module


class TestTheMainFileCriterionBites:
    """两向反证：主文件判据在**真缺陷**上必须报红，在**归档后的正常状态**上必须不报红。"""

    def test_a_row_only_in_the_archive_is_not_a_negative(self, tmp_path: Path) -> None:
        """① **假负的反面**：进展行只在归档里 ⇒ 两条进展断言全绿。

        这是本 GOAL 修掉的形态：归档是**正常结果**，不是断言失败。若这条判红，
        就说明读取面又退回「只读活跃面」了。
        """
        tree = _synthetic_charter_tree(
            tmp_path, goal_id="GOAL-20260101-901", recheck_id="RECHECK-20260101-901"
        )
        module = _probe_verifier()
        progress = [
            item for item in module.record_verdicts(tree) if item.name.startswith("progress-")
        ]
        assert [item.name for item in progress] == [
            "progress-records-this-goal",
            "progress-row-names-the-recheck",
        ], "合成树里没跑到那两条进展断言 ⇒ 反证没有对象"
        assert all(item.ok for item in progress), (
            "行在**归档**里时进展断言必须全绿（这正是本 GOAL 修掉的假负）",
            [(item.name, item.detail) for item in progress if not item.ok],
        )

    def test_a_row_missing_from_both_faces_is_named_red(self, tmp_path: Path) -> None:
        """② **判据真的咬得住**：活跃面与归档**都没有**那一行 ⇒ 点名那两条判红。"""
        tree = _synthetic_charter_tree(
            tmp_path, goal_id="GOAL-20260101-901", recheck_id="RECHECK-20260101-901"
        )
        module = _probe_verifier()
        arch = tree / ".cursor" / "plans" / "goals" / "archive" / "MAINLINE-2026-01-01-probe.md"
        archived = arch.read_text(encoding="utf-8")
        assert "GOAL-20260101-901" in archived, "反证的前提：归档里确实有那一行"
        arch.write_bytes(
            "\n".join(
                line for line in archived.splitlines() if "GOAL-20260101-901" not in line
            ).encode("utf-8")
        )
        failed = [
            item.name
            for item in module.record_verdicts(tree)
            if item.name.startswith("progress-") and not item.ok
        ]
        assert failed == ["progress-records-this-goal", "progress-row-names-the-recheck"], (
            "两处都没有那一行时必须点名这两条（判据真咬得住）",
            failed,
        )

    def test_the_shared_reader_is_the_only_implementation(self) -> None:
        """**共享 helper 在树**：读取面只有一处实现（17 处各写一遍必然漂移）。

        判法（精确到**漂移的那一句**，不是「出现过 splitlines 就红」）：每个带进展断言的
        验证器都**不得**再自己从活跃面小节里筛出**本 GOAL 的行**
        —— 那正是 14 份各自漂移的实现，必须走 `TOOLBOX.progress_rows`。

        为什么不用「出现过 `progress.splitlines()` 就红」：099 / 100 另有一处**合法**用法
        —— 它们把整张表读成 `[(日期, GOAL)]` 来判「本行是不是插在最上面」（位置断言要
        看**所有**行，不是只看自己那一行）。那条判据读的是
        `TOOLBOX.progress_context(...)` 给回的行所在正文，不构成第二个「本 GOAL 的行从哪来」
        的实现。
        """
        helper = _TOOLS / "charter_progress.py"
        assert helper.is_file(), "共享读取面不在树（tools/charter_progress.py）"
        assert "def progress_rows" in helper.read_text(encoding="utf-8")
        drift = 'for line in progress.splitlines() if line.startswith("| ") and LADDER_GOAL in line'
        offenders: list[str] = []
        for relative in _VERIFIERS:
            text = _ROOT.joinpath(*relative.split("/")).read_text(encoding="utf-8")
            if "progress-records-this-goal" not in text:
                continue
            if drift in text:
                offenders.append(relative)
        assert not offenders, (
            "这些验证器仍在**自己**筛本 GOAL 的进展行（应走共享 helper `TOOLBOX.progress_rows`）",
            offenders,
        )
        # 射程非空：至少**多数**带进展断言的验证器真的走了 helper（否则这条只是空转）。
        on_helper = sum(
            1
            for relative in _VERIFIERS
            if "TOOLBOX.progress_rows"
            in _ROOT.joinpath(*relative.split("/")).read_text(encoding="utf-8")
        )
        assert on_helper >= _MIN_ON_HELPER, (
            f"只有 {on_helper} 个验证器走共享 helper（下界 {_MIN_ON_HELPER}）⇒ 判据失去对象"
        )


class TestTheEarlyGenerationCriterionBites:
    """**反证臂**：早期一代的判负扫描真的会红（不是"名单里有三个就完事"）。

    做法与 GOAL-101 的反证臂同形（最小合成树 + 真验证器），但对象换成早期一代：
    028 的 `record_verdicts(root)` 读的是 **GOAL 记录正文**里的固定标记
    （`UNCOVERED_MARKERS` / `RESIDUAL_MARKERS` / EC 状态行）。把合成树里 GOAL 正文的
    这些标记**全部去掉** ⇒ 它必须报出多条判负；把这些标记写回去 ⇒ 必须全绿。

    这一条钉的是「射程真的伸到了早期一代」：如果 `_early_record_verdicts` 因为签名不匹配
    而静默返回空列表，`ran >= 3` 会红 —— 但**只有**这一条反证能证明"返回的判词真的
    带着它自己的断言"。
    """

    def test_the_early_verifier_reports_red_when_its_markers_are_gone(self, tmp_path: Path) -> None:
        module = _load_module(
            _ROOT / "tools" / "verify_goal028_closeout.py", "goal103_early028_probe"
        )
        goal_path = tmp_path / getattr(module, "GOAL")
        goal_path.parent.mkdir(parents=True, exist_ok=True)
        goal_path.write_bytes(b"# empty goal record\n")

        verdicts = list(module.record_verdicts(tmp_path))
        assert verdicts, "空记录上必须产出判词（否则这一代的主文件面是空转）"
        assert any(not item.ok for item in verdicts), (
            "GOAL 正文里什么标记都没有时，早期一代的判据必须判红",
            [(item.name, item.ok) for item in verdicts],
        )

    def test_the_early_verifier_is_green_on_a_record_carrying_its_markers(
        self, tmp_path: Path
    ) -> None:
        """反向：把该验证器自己声明的标记**原样**写进记录 ⇒ 判词全绿。

        与上一条成对：只判"红"会让"永远红"也通过。
        """
        module = _load_module(
            _ROOT / "tools" / "verify_goal028_closeout.py", "goal103_early028_probe_green"
        )
        markers = [
            *getattr(module, "UNCOVERED_MARKERS", ()),
            *getattr(module, "RESIDUAL_MARKERS", ()),
        ]
        assert markers, "该验证器必须声明它要的标记（否则本反证没有对象）"
        goal_path = tmp_path / getattr(module, "GOAL")
        goal_path.parent.mkdir(parents=True, exist_ok=True)
        goal_path.write_bytes(("\n".join(markers) + "\n").encode("utf-8"))

        verdicts = list(module.record_verdicts(tmp_path))
        failed = [(item.name, item.ok) for item in verdicts if not item.ok]
        # EC 状态行不在标记集里 ⇒ 那几条仍会红；本判据只要求**标记类**断言转绿。
        marker_names = {name for name, _ok in failed}
        marked = ("uncovered-enumerated", "residuals-enumerated")
        assert not any(name in marker_names for name in marked), (
            "标记写回后，标记类断言必须转绿（否则判据没有真的读那些标记）",
            failed,
        )
