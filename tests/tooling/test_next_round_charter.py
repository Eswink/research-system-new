"""GOAL-20261021-092 EC-01…EC-04 判据：**「上一轮输出 → 下一轮 charter」是读取，不是记忆**。

**它补哪一格**：此前这条衔接**靠人**——驱动方读完 GOAL 报告，把「残余与未覆盖范围」抄进
下一轮提示词。漏一条就丢了，而且没有任何东西会说话。`tools/next_round_charter.py` 把它变成
确定性读取；本判据钉住五件事（逐条对应提示词的判据 1…5）：

1. **不丢不增**：对**真文件**（GOAL-091）跑，产出的 `W` 列表与正文逐条一致 —— 逐条原文
   相同、条数相同、顺序相同；
2. **反证（少一条）**：在**合成树**里删掉整条 `W-7` ⇒ 产出随之少一条（证明是读出来的，
   不是硬编码）；
3. **反证（非终态）**：`status` 改成非终态 ⇒ 点名拒绝（`GOAL_NOT_TERMINAL`）；
4. **反证（RECHECK 不存在）**：`latest_recheck` 指向不存在的文件 ⇒ 点名拒绝；
5. **确定性**：同输入跑两次 ⇒ 逐字节相同（`sha256` 相等），且与平台行尾无关。

另有三条边界（都不是「顺手加的」）：

* **拒绝不写盘**：`--out` 在失败时**不创建文件**（半成品比不写更有害：它会被当成完整输入）；
* **断号也拒**：`W-1 / W-3` 这种形态必须判拒 —— 有人删了一条却没改编号时，
  「产物少一条」与「读对了」在旧形态下不可区分；
* **口径与宪章判据同源**：阶梯表与进展记录的读数与
  `test_mainline_research_ladder_advances.py` 对同一份宪章逐条一致。

**射程边界（如实登记）**：

* 本判据**不**判「下一轮该做什么」—— objective / EC 是判断，读取器显式留空
  （`<待填：判断>`），末节用例断言那一格**确实**是空的（防它偷偷开始做判断）；
* CI 台账的读数只验**机械分类**（`success` / 无 run / 判红），不独立取证 CI 本身；
* 真文件那条读的是**当前** GOAL-091：判据只用它的 `status` / `W` 面 / CI 台账，不依赖散文。
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "next_round_charter.py"
PARSE_TOOL = ROOT / "tools" / "charter_parse.py"
LADDER_JUDGE = ROOT / "tests" / "tooling" / "test_mainline_research_ladder_advances.py"

GOAL_091 = ".cursor/plans/goals/GOAL-20261020-091-two-models-judge-the-same-artifact.md"
RECHECK_091 = (
    ".cursor/plans/rechecks/RECHECK-20261020-091-goal-091-two-models-judge-the-same-artifact.md"
)
CHARTER = ".cursor/plans/goals/MAINLINE.md"
RESIDUAL_HEADING = "## 残余与未覆盖范围"

NEXT_ID = "GOAL-20261021-902"

#: 判据**自己的**读法（独立于被测实现）：一条 = `- **`W-N`**` 起头 + 其后的缩进续行。
_ITEM = re.compile(r"^- \*\*`W-(\d+)`\*\*")
_INDENTED = re.compile(r"^[ \t]+\S")


def _load(path: Path, name: str) -> ModuleType:
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"无法加载 {path}"
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def _reader() -> ModuleType:
    return _load(TOOL, "goal092_next_round_charter")


def _parse() -> ModuleType:
    return _load(PARSE_TOOL, "goal092_charter_parse")


def _goal_text() -> str:
    return (ROOT / GOAL_091).read_text(encoding="utf-8")


def _section(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    start = next((index + 1 for index, line in enumerate(lines) if line.startswith(heading)), None)
    assert start is not None, f"没有小节 {heading!r} ⇒ 本判据失去对象"
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return body


def _expected_items(text: str) -> list[tuple[int, str]]:
    """`[(编号, 逐条原文), …]` —— 判据自己的切分，**不调被测实现**。

    一条 = 一个 `- **`W-N`**` 起头 + 紧随的缩进续行；**任何非缩进行都结束当前条**
    （残余节后面还跟着 `R-1…R-3` 那一组，它的续行同样是缩进的 —— 不在此处截断会把它们
    算进最后一条，本判据的第一版正是这么错的）。
    """
    items: list[tuple[int, list[str]]] = []
    for line in _section(text, RESIDUAL_HEADING):
        match = _ITEM.match(line)
        if match is not None:
            items.append((int(match.group(1)), [line]))
        elif items and line.strip() and _INDENTED.match(line):
            items[-1][1].append(line)
        elif not line.strip():
            continue
        else:
            items.append((0, ["<end>"]))
    return [(number, "\n".join(raw)) for number, raw in items if number != 0]


def _without_bullet(text: str, number: int) -> str:
    """删掉**整条** `W-<number>`（首行 + 全部续行），其余一行不动。"""
    kept: list[str] = []
    skipping = False
    for line in text.splitlines():
        match = _ITEM.match(line)
        if match is not None:
            skipping = int(match.group(1)) == number
        elif not line.strip() or not _INDENTED.match(line):
            skipping = False
        if not skipping:
            kept.append(line)
    return "\n".join(kept) + "\n"


def _synthetic_tree(tmp_path: Path, *, goal_text: str | None = None) -> Path:
    """一棵最小树：真宪章 + 真 GOAL-091 + 真复检（只在需要处改一份副本）。"""
    plans = tmp_path / ".cursor" / "plans"
    (plans / "goals").mkdir(parents=True)
    (plans / "rechecks").mkdir(parents=True)
    shutil.copyfile(ROOT / CHARTER, plans / "goals" / "MAINLINE.md")
    shutil.copyfile(ROOT / RECHECK_091, plans / "rechecks" / Path(RECHECK_091).name)
    body = _goal_text() if goal_text is None else goal_text
    (plans / "goals" / Path(GOAL_091).name).write_bytes(body.encode("utf-8"))
    return tmp_path


def _run(tree: Path, *, out: Path | None = None) -> tuple[int, str]:
    """按**命令行形态**跑读取器（判据测的是入口，不是内部函数）。"""
    argv = ["--root", str(tree), "--goal", GOAL_091, "--next-goal-id", NEXT_ID]
    if out is not None:
        argv += ["--out", str(out)]
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = _reader().main(argv)
    return code, buffer.getvalue()


# ---------------------------------------------------------------- 判据 1：不丢不增


def test_the_w_list_matches_the_goal_body_verbatim() -> None:
    """对真文件跑：产出的 `W` 列表与 GOAL-091 正文**逐条一致**（不丢、不增、不改序）。"""
    text = _reader().build_skeleton(ROOT, GOAL_091, NEXT_ID)
    produced = _parse().residual_section(_goal_text())
    expected = _expected_items(_goal_text())
    assert len(expected) == 7, f"GOAL-091 有 7 条未覆盖范围，判据读到 {len(expected)} 条"
    assert [(item.number, item.raw) for item in produced] == expected, (
        "读出来的残余与正文不一致（丢 / 增 / 改序 / 改字都会被这条抓到）"
    )
    for _number, raw in expected:
        assert raw in text, f"这条原文没有原样进产物：{raw[:60]!r}"


def test_the_produced_text_carries_every_residual_and_no_summary() -> None:
    """产物里逐条原文在场（不是摘要），且编号 1…7 一个不少。"""
    text = _reader().build_skeleton(ROOT, GOAL_091, NEXT_ID)
    for number, raw in _expected_items(_goal_text()):
        assert f"`W-{number}`" in text, f"产物漏了编号 `W-{number}`"
        assert raw in text, f"产物里没有这条的原文：{raw[:60]!r}"
    assert "共 7 条" in text, "产物必须报出条数（读者要能立刻发现少了一条）"


# ---------------------------------------------------------------- 判据 5：确定性


def test_two_runs_on_the_same_input_are_byte_identical() -> None:
    """同输入跑两次 ⇒ 逐字节相同（比 `sha256`），且产物里没有 `\\r`。"""
    module = _reader()
    first = module.build_skeleton(ROOT, GOAL_091, NEXT_ID)
    second = module.build_skeleton(ROOT, GOAL_091, NEXT_ID)
    assert _parse().sha256_text(first) == _parse().sha256_text(second)
    assert "\r" not in first, "产物含 CR ⇒ 行尾依赖平台（确定性被打折）"


def test_writing_through_the_cli_is_binary_and_reproducible(tmp_path: Path) -> None:
    """`--out` 落盘两次 ⇒ 两个文件的**原始字节**相同（`read_bytes` 比对，不比文本）。"""
    first = tmp_path / "a.md"
    second = tmp_path / "b.md"
    for target in (first, second):
        code, output = _run(ROOT, out=target)
        assert code == 0, output
    assert b"\r" not in first.read_bytes(), "落盘用了文本模式（Windows 会写 CRLF）"
    assert first.read_bytes() == second.read_bytes(), "同输入两次落盘的字节不同"


# ---------------------------------------------------------------- 判据 2：少一条


def test_removing_the_last_residual_makes_the_output_one_shorter(tmp_path: Path) -> None:
    """**反证**：删掉整条 `W-7`（编号仍连续）⇒ 产出恰好少那条（不是硬编码）。"""
    source = _goal_text()
    stripped = _without_bullet(source, 7)
    assert stripped != source, "反证的前提：W-7 确实在 GOAL 里"
    module = _reader()
    baseline = module.build_skeleton(ROOT, GOAL_091, NEXT_ID)
    trimmed = module.build_skeleton(
        _synthetic_tree(tmp_path, goal_text=stripped), GOAL_091, NEXT_ID
    )
    victim = next(raw for number, raw in _expected_items(source) if number == 7)
    assert victim in baseline, "基线里应当有它（否则反证没有对照）"
    assert victim not in trimmed, "删掉的那条仍然出现在产物里 ⇒ 它是硬编码的"
    assert "共 6 条" in trimmed and "共 7 条" in baseline, (
        "条数必须跟着内容走（产物自报条数就是为了让读者一眼看出少了一条）"
    )


def test_output_follows_the_content_not_a_cached_list(tmp_path: Path) -> None:
    """反证（第二向）：改写一条残余的**正文** ⇒ 产物里的那一条随之改写。"""
    source = _goal_text()
    marker = "只证明两位**判出了不同结论**，不证明谁的判断更对。"
    assert marker in source, "反证的前提：这句原文在 GOAL 里"
    rewritten = source.replace(marker, "PROBE-REWRITTEN-BODY", 1)
    text = _reader().build_skeleton(
        _synthetic_tree(tmp_path, goal_text=rewritten), GOAL_091, NEXT_ID
    )
    assert "PROBE-REWRITTEN-BODY" in text, "改写后的正文没有进产物 ⇒ 产物不是从文件读的"
    assert marker not in text, "旧正文仍在产物里 ⇒ 有一条硬编码的副本"


# ---------------------------------------------------------------- 判据 3 / 4：点名拒绝


def _status_rewritten(status: str) -> str:
    source = _goal_text()
    assert "\nstatus: ACHIEVED\n" in source, "GOAL-091 的 status 行形态变了（反证需同步）"
    return source.replace("\nstatus: ACHIEVED\n", f"\nstatus: {status}\n", 1)


@pytest.mark.parametrize("status", ["ACTIVE", "DRAFT", "PAUSED"])
def test_a_non_terminal_goal_is_refused_by_name(tmp_path: Path, status: str) -> None:
    """**反证**：`status` 非终态 ⇒ 点名拒绝（`exit 2` 且**不写** `--out`）。"""
    tree = _synthetic_tree(tmp_path, goal_text=_status_rewritten(status))
    target = tmp_path / "skeleton.md"
    code, output = _run(tree, out=target)
    assert code == 2, f"非终态必须拒绝（exit 2），实际 {code}：{output}"
    assert "REFUSED GOAL_NOT_TERMINAL" in output, output
    assert status in output, "拒绝理由要点名读到的那个 status"
    assert not target.exists(), "拒绝时不得写盘（半成品会被当成完整输入）"


def test_a_missing_recheck_is_refused_by_name(tmp_path: Path) -> None:
    """**反证**：`latest_recheck` 指向不存在的文件 ⇒ 点名拒绝。"""
    tree = _synthetic_tree(tmp_path)
    (tree / ".cursor" / "plans" / "rechecks" / Path(RECHECK_091).name).unlink()
    target = tmp_path / "skeleton.md"
    code, output = _run(tree, out=target)
    assert code == 2, output
    assert "REFUSED RECHECK_MISSING" in output, output
    assert not target.exists(), "拒绝时不得写盘"


def test_a_recheck_for_another_goal_is_refused(tmp_path: Path) -> None:
    """`latest_recheck` 存在但属于**别的** GOAL ⇒ 拒绝（存在性不等于归属）。"""
    tree = _synthetic_tree(tmp_path)
    recheck_path = tree / ".cursor" / "plans" / "rechecks" / Path(RECHECK_091).name
    original = recheck_path.read_text(encoding="utf-8")
    assert "parent_goal: GOAL-20261020-091" in original, "反证的前提"
    recheck_path.write_bytes(
        original.replace(
            "parent_goal: GOAL-20261020-091", "parent_goal: GOAL-20261020-090", 1
        ).encode("utf-8")
    )
    code, output = _run(tree, out=tmp_path / "skeleton.md")
    assert code == 2, output
    assert "REFUSED RECHECK_NOT_THIS_GOAL" in output, output


def test_a_failing_recheck_is_refused(tmp_path: Path) -> None:
    """复检结论不是通过取值（`REVISE`）⇒ 拒绝：上一轮没有真的收口。"""
    tree = _synthetic_tree(tmp_path)
    recheck_path = tree / ".cursor" / "plans" / "rechecks" / Path(RECHECK_091).name
    original = recheck_path.read_text(encoding="utf-8")
    assert "\nresult: PASS\n" in original, "反证的前提"
    recheck_path.write_bytes(original.replace("\nresult: PASS\n", "\nresult: REVISE\n", 1).encode())
    code, output = _run(tree, out=tmp_path / "skeleton.md")
    assert code == 2, output
    assert "REFUSED RECHECK_NOT_PASSING" in output, output


def test_a_gap_in_the_w_numbering_is_refused(tmp_path: Path) -> None:
    """断号（`W-1 / W-3`）⇒ 拒绝并点名两个序列（删一条却忘改编号是可辨的）。"""
    tree = _synthetic_tree(tmp_path, goal_text=_without_bullet(_goal_text(), 2))
    code, output = _run(tree, out=tmp_path / "skeleton.md")
    assert code == 2, output
    assert "REFUSED RESIDUAL_GAP" in output, output
    assert "读到 [1, 3, 4, 5, 6, 7]" in output, "拒绝理由要报出**读到**的编号序列"


def test_a_ladder_row_that_does_not_record_the_goal_is_refused(tmp_path: Path) -> None:
    """阶梯里没有任何域收录本 GOAL ⇒ 拒绝（「这一轮推进了科研」没有被记账）。"""
    tree = _synthetic_tree(tmp_path)
    charter = tree / ".cursor" / "plans" / "goals" / "MAINLINE.md"
    text = charter.read_text(encoding="utf-8")
    assert "GOAL-20261020-091" in text, "前提：宪章确实收录了它"
    charter.write_bytes(text.replace("GOAL-20261020-091", "GOAL-20261020-090").encode("utf-8"))
    code, output = _run(tree, out=tmp_path / "skeleton.md")
    assert code == 2, output
    assert "REFUSED LADDER_NOT_RECORDED" in output, output


def test_an_empty_residual_section_without_a_marker_is_refused(tmp_path: Path) -> None:
    """残余节被清空而没有「无残余」标记 ⇒ 拒绝（空节与忘写不可区分）。"""
    source = _goal_text()
    start = source.index(RESIDUAL_HEADING)
    end = source.find("\n## ", start + 1)
    tail = source[end:] if end != -1 else "\n"  # 残余节在 GOAL-091 里是最后一节
    tree = _synthetic_tree(tmp_path, goal_text=source[:start] + RESIDUAL_HEADING + "\n" + tail)
    code, output = _run(tree, out=tmp_path / "skeleton.md")
    assert code == 2, output
    assert "REFUSED RESIDUAL_EMPTY" in output, output


# ---------------------------------------------------------------- 边界与口径


def test_the_judgement_part_is_left_blank_not_guessed() -> None:
    """末节把**判断**留空：objective / EC 在骨架里是 `<待填：判断>`，不是猜出来的值。"""
    text = _reader().build_skeleton(ROOT, GOAL_091, NEXT_ID)
    assert "objective: <待填：判断>" in text, "objective 不得被自动填上"
    assert "exit_criteria: <待填：判断" in text, "exit_criteria 不得被自动填上"
    assert "## 六、不可自动推导的部分" in text, "必须显式列出「判断面」"


def test_the_ci_ledger_is_read_not_assumed() -> None:
    """CI 台账的读数来自文件：GOAL-091 的 6 行里 5 success + 1 无 run ⇒ 「全绿」。"""
    summary = _parse().ci_summary(_goal_text())
    assert (summary.green, summary.no_run, summary.red) == (5, 1, 0), summary
    assert summary.verdict == "全绿", summary.verdict
    synthetic = (
        "## CI 台账\n\n| 提交 | run | 结论 |\n| --- | --- | --- |\n"
        "| `a` | `1` | **八 job 全 success** |\n| `b` | `2` | **判红**（lint） |\n"
    )
    red = _parse().ci_summary(synthetic)
    assert red.red == 1 and red.verdict.startswith("有判红"), red


def test_the_parsing_agrees_with_the_charter_judges() -> None:
    """口径同源：与宪章判据对同一份宪章给出同一组阶梯行、同样多的进展行。"""
    judge = _load(LADDER_JUDGE, "goal092_ladder_judge")
    charter = (ROOT / CHARTER).read_text(encoding="utf-8")
    theirs = [(row[0], row[3]) for row in judge._ladder_rows()]
    ladder = _parse().section_lines(charter, "## 科研能力阶梯") or []
    ours = [(row[0], row[3]) for row in _parse().table_rows(ladder) if len(row) >= 4]
    assert ours == theirs, "两份实现对阶梯表的读数不同 ⇒ 口径漂了"
    progress = _parse().table_rows(_parse().section_lines(charter, "## 进展记录") or [])
    assert len(progress) == len(judge._progress_rows(charter)), "进展记录行数读数不同"


def test_the_tools_are_path_independent_and_do_not_read_the_clock() -> None:
    """两个脚本都不硬编码仓库根、不读时钟、不触网（确定性的一部分）。"""
    for relative in ("tools/next_round_charter.py", "tools/charter_parse.py"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for forbidden in ("datetime.now", "time.time", "date.today", "socket", "urllib"):
            assert forbidden not in text, f"{relative} 出现了 {forbidden} ⇒ 不再确定/离网"
