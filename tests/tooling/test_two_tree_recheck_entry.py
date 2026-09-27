"""GOAL-20260928-022 EC-01 判据：两树复检入口的**行为**契约。

判什么（缺一不可）：

1. **两树同结论 ⇒ 绿**：同一组断言、判词逐行相同、两份判词 `sha256` 相同、退出码 0；
2. **反证必须真的会红**：让第二棵树跑出**不同**结果 ⇒ 入口**非 0** 且**点名差异行**
   （不是「打印两份就完事」）；
3. **三条环境口径各有一条行为判据**：
   ① **共用解释器**（两棵树用的解释器相同，且等于调用入口的那个）；
   ② **输出纯度**（出现非判词行即拒绝，**不得**静默过滤）；
   ③ **路径无关**（判词嵌了本树绝对路径即拒绝，**不得**规范化后照常判绿）；
4. **只跑一路 ⇒ 非 0**：干净树拿不到时入口拒绝服务，**绝不**降级成「只跑当前树的 PASS」
   （这正是 GOAL-021 `W-0` 的形态）。

**绑定的是行为**，不是文档话术。唯一读文档的断言是 EC-01(c) 的「**条款不得悬空**」——
它判的是**小节标题**与**被点名文件是否存在**（承既有
`test_record_face_is_covered_by_the_gate.py` 的形态），不是条款的文字怎么写。

夹具（探针脚本）由本判据在 `tmp_path` 里**运行时生成**，不落进仓库。
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "tools" / "two_tree_recheck.py"
CONVENTIONS_DOC = ROOT / "docs" / "architecture" / "RECHECK_SCRIPT_CONVENTIONS.md"
SELF_RELATIVE = "tests/tooling/test_two_tree_recheck_entry.py"

#: EC-01(c) 的结构性锚点：承载「收口复检必须两树」条款的小节标题。
CLAUSE_SECTION = "## 收口复检必须两树"

#: 该条款内**必须点名**的文件（改名 / 移动即判红 ⇒ 条款不得悬空）。
CLAUSE_NAMED_FILES: tuple[str, ...] = ("tools/two_tree_recheck.py", SELF_RELATIVE)

_MARKER_PROBE = '''
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--verdict-only", action="store_true")
args = parser.parse_args()
marker = Path(args.root) / "marker.txt"
value = marker.read_text(encoding="utf-8").strip() if marker.is_file() else "absent"
print(f"PASS probe-marker value={value}")
print("PASS probe-shape stable")
'''

_IMPURE_PROBE = '''
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--verdict-only", action="store_true")
parser.parse_args()
print("PASS probe-impure first")
print("elapsed 0.0001s")
'''

_PATHY_PROBE = '''
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--verdict-only", action="store_true")
args = parser.parse_args()
print(f"PASS probe-pathy root={args.root}")
'''

_INTERPRETER_PROBE = '''
import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--verdict-only", action="store_true")
args = parser.parse_args()
(Path(args.root) / "interpreter.txt").write_text(sys.executable, encoding="utf-8")
print("PASS probe-interpreter recorded")
'''

_FAILING_PROBE = '''
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--verdict-only", action="store_true")
parser.parse_args()
print("FAIL probe-always-red")
raise SystemExit(1)
'''


def _write_probe(directory: Path, name: str, body: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(body.lstrip(), encoding="utf-8", newline="")
    return path


def _tree_pair(tmp_path: Path, first: str = "same", second: str = "same") -> tuple[Path, Path]:
    """两棵最小的「树」：只有一个 marker.txt，内容可控。"""
    left = tmp_path / "tree-a"
    right = tmp_path / "tree-b"
    for tree, value in ((left, first), (right, second)):
        tree.mkdir(parents=True, exist_ok=True)
        (tree / "marker.txt").write_text(value, encoding="utf-8", newline="")
    return left, right


def _run_entry(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(ENTRY), *arguments],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _shared_args(probe: Path, left: Path, right: Path, *extra: str) -> list[str]:
    return [
        "--script",
        str(probe),
        "--script-mode",
        "shared",
        "--root",
        str(left),
        "--clean-root",
        str(right),
        *extra,
    ]


def test_entry_and_clause_doc_are_in_the_tree() -> None:
    """交付面：入口与承载条款的规范页都在树。"""
    assert ENTRY.is_file(), f"两树入口不在树：{ENTRY}"
    assert CONVENTIONS_DOC.is_file(), f"复检脚本规范页不在树：{CONVENTIONS_DOC}"


def test_both_trees_agree_when_assertions_agree(tmp_path: Path) -> None:
    """① 两树同结论 ⇒ 绿：判词逐行相同 + 两份 sha256 相同 + 退出码 0。"""
    probe = _write_probe(tmp_path, "marker_probe.py", _MARKER_PROBE)
    left, right = _tree_pair(tmp_path)
    result = _run_entry(_shared_args(probe, left, right))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TWO-TREE PASS" in result.stdout
    assert "COMPARE identical=True" in result.stdout
    digests = [line.split("sha256=")[1] for line in result.stdout.splitlines() if "sha256=" in line]
    assert len(digests) == 2, digests
    assert digests[0] == digests[1], f"两份判词 sha256 不同：{digests}"


def test_second_tree_differing_makes_the_entry_red(tmp_path: Path) -> None:
    """② 反证：第二树跑出不同结果 ⇒ 入口非 0 且**点名差异行**。"""
    probe = _write_probe(tmp_path, "marker_probe.py", _MARKER_PROBE)
    left, right = _tree_pair(tmp_path, first="same", second="different")
    result = _run_entry(_shared_args(probe, left, right))
    assert result.returncode != 0, "两树结论不同却没有判红 ⇒ 入口只是「打印两份」"
    assert "TWO-TREE RED" in result.stdout
    assert "COMPARE identical=False" in result.stdout
    assert "DIFF" in result.stdout, f"没有点名差异行：{result.stdout}"


def test_both_trees_use_the_same_interpreter(tmp_path: Path) -> None:
    """③-① 共用解释器：两棵树记录到的解释器相同，且就是调用入口的那一个。"""
    probe = _write_probe(tmp_path, "interpreter_probe.py", _INTERPRETER_PROBE)
    left, right = _tree_pair(tmp_path)
    result = _run_entry(_shared_args(probe, left, right))
    assert result.returncode == 0, result.stdout + result.stderr
    left_used = (left / "interpreter.txt").read_text(encoding="utf-8")
    right_used = (right / "interpreter.txt").read_text(encoding="utf-8")
    assert left_used == right_used, f"两棵树用了不同解释器：{left_used!r} vs {right_used!r}"
    assert Path(left_used).resolve() == Path(sys.executable).resolve(), (
        f"两树没有共用调用方的解释器：{left_used!r} vs {sys.executable!r}"
    )


def test_impure_output_is_refused_not_filtered(tmp_path: Path) -> None:
    """③-② 输出纯度：出现非判词行 ⇒ 拒绝（非 0），**不得**静默过滤后照常判绿。"""
    probe = _write_probe(tmp_path, "impure_probe.py", _IMPURE_PROBE)
    left, right = _tree_pair(tmp_path)
    result = _run_entry(_shared_args(probe, left, right))
    assert result.returncode != 0, "非判词行被静默过滤了 ⇒ 纯度不是判据"
    assert "TWO-TREE PASS" not in result.stdout
    assert "不纯" in result.stdout, f"失败理由没有点名纯度：{result.stdout}"


def test_path_dependent_verdict_is_refused_not_normalized(tmp_path: Path) -> None:
    """③-③ 路径无关：判词嵌入本树绝对路径 ⇒ 拒绝（非 0），**不得**规范化后判绿。"""
    probe = _write_probe(tmp_path, "pathy_probe.py", _PATHY_PROBE)
    left, right = _tree_pair(tmp_path)
    result = _run_entry(_shared_args(probe, left, right))
    assert result.returncode != 0, "路径相关判词被规范化后照常判绿 ⇒ 判词不再是结论"
    assert "TWO-TREE PASS" not in result.stdout
    assert "路径相关" in result.stdout, f"失败理由没有点名路径相关性：{result.stdout}"


def test_a_failing_tree_is_never_reported_as_pass(tmp_path: Path) -> None:
    """两树判词相同但都不绿 ⇒ 仍必须判红（「一样」不等于「成立」）。"""
    probe = _write_probe(tmp_path, "failing_probe.py", _FAILING_PROBE)
    left, right = _tree_pair(tmp_path)
    result = _run_entry(_shared_args(probe, left, right))
    assert result.returncode != 0, "两树都 FAIL 却报绿 ⇒ 入口把「一致」当成了「成立」"
    assert "TWO-TREE PASS" not in result.stdout
    assert "NOT-GREEN" in result.stdout, f"没有登记不绿理由：{result.stdout}"


def test_missing_clean_tree_never_degrades_to_single_tree_pass(tmp_path: Path) -> None:
    """④ 只跑一路 ⇒ 非 0：拿不到干净树时拒绝服务，不得降级成单树 PASS。"""
    probe = _write_probe(tmp_path, "marker_probe.py", _MARKER_PROBE)
    left, _ = _tree_pair(tmp_path)
    missing = tmp_path / "absent-tree"
    result = _run_entry(_shared_args(probe, left, missing))
    assert result.returncode != 0, "干净树不存在却报了绿 ⇒ 这就是 GOAL-021 W-0 的形态"
    assert "TWO-TREE PASS" not in result.stdout
    assert "SETUP" in result.stdout, f"没有登记入口自身的失败：{result.stdout}"


def test_tree_mode_requires_identical_script_bytes(tmp_path: Path) -> None:
    """同一组断言的前提：`tree` 模式下两棵树的脚本字节必须相同。"""
    left, right = _tree_pair(tmp_path)
    relative = "probe.py"
    (left / relative).write_text(_MARKER_PROBE.lstrip(), encoding="utf-8", newline="")
    (right / relative).write_text(_PATHY_PROBE.lstrip(), encoding="utf-8", newline="")
    result = _run_entry(["--script", relative, "--root", str(left), "--clean-root", str(right)])
    assert result.returncode != 0, "两树脚本字节不同却继续比较 ⇒ 比的不是同一组断言"
    assert "字节不同" in result.stdout, f"失败理由没有点名脚本差异：{result.stdout}"


def test_verdict_files_are_written_and_byte_identical_when_green(tmp_path: Path) -> None:
    """留档面：`--verdict-*` 落点写出的两份判词**逐字节相同**（raw sha256，不是 git diff）。"""
    probe = _write_probe(tmp_path, "marker_probe.py", _MARKER_PROBE)
    left, right = _tree_pair(tmp_path)
    current_dump = tmp_path / "verdict-current.txt"
    clean_dump = tmp_path / "verdict-clean.txt"
    result = _run_entry(
        _shared_args(
            probe,
            left,
            right,
            "--verdict-current",
            str(current_dump),
            "--verdict-clean",
            str(clean_dump),
        )
    )
    assert result.returncode == 0, result.stdout + result.stderr
    left_bytes = current_dump.read_bytes()
    right_bytes = clean_dump.read_bytes()
    assert left_bytes == right_bytes, "两份判词落档不是逐字节相同"
    digest = hashlib.sha256(left_bytes).hexdigest()
    assert f"sha256={digest}" in result.stdout, "入口报的 sha256 与落档字节不一致"


def test_the_clause_section_names_live_files() -> None:
    """EC-01(c)「条款不得悬空」：小节标题在位，且点名的文件**都存在**。

    判的是**结构**（标题 + 文件存在性）：把判据文件改名或搬走即判红，
    所以条款不会指向一个已经不存在的东西。
    """
    text = CONVENTIONS_DOC.read_text(encoding="utf-8")
    assert CLAUSE_SECTION in text, f"规范页缺少条款小节 {CLAUSE_SECTION!r}"
    section = text.split(CLAUSE_SECTION, 1)[1]
    section = section.split("\n## ", 1)[0]
    for relative in CLAUSE_NAMED_FILES:
        assert relative in section, f"条款小节里没有点名 {relative}"
        assert (ROOT / relative).is_file(), f"条款点名的 {relative} 不存在 ⇒ 条款悬空"
