"""GOAL-029 EC-04 判据：**两树判词的归档留相**（收 GOAL-028 发现的缺口）。

**它补的是什么**：GOAL-028 的两树复检只留了 log（且那份 log 是 PowerShell 重定向的 CRLF），
**判词文件本身没有独立归档** ⇒ 「两树逐行相同」这条结论**缺可独立复核的物证**
（`scratch/` 在 `.gitignore` 里，clone 出来的仓库看不到）。

**四件事**：

1. **归档落点在树**：`tools/two_tree_recheck.py --verdict-current/--verdict-clean` 的落点
   定在**仓内可引用**的位置（本 GOAL 的口径见 `_ARCHIVE_DIR`），而不是 `scratch/`。
2. **两份 `sha256` 相同**（判词逐字节一致 ⇔ 两树同结论）。
3. **行尾为 LF**（承 `MEM-20260928-152`）：逐字节扫 `\\r`。
   **实测危害**：`pathlib.write_text(..., encoding="utf-8")`（文本模式）在 Windows 把 `\\n`
   写成 `\\r\\n` ⇒ raw `sha256` 变；而 `.gitattributes` 的 `* text=auto eol=lf` 会把差异
   在提交时**静默归一化**掉 ⇒ **`git diff` 不足以**充当逐字节证据。
4. **反证两向**：文本模式写一份 ⇒ 判红（CRLF 与 LF 的 `sha256` 不同）；
   二进制复原 ⇒ 绿。

**射程边界（如实登记）**：本判据**不**产生归档（那是两树入口在收口 cycle 里的事），
它判的是「归档物的形态与一致性」。归档的**产生**由 `tools/verify_goal029_closeout.py` 的
两树复检驱动（`--script-mode shared`）。
"""

from __future__ import annotations

import hashlib
import pathlib
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
#: 归档落点（仓内、可被记录引用）。**不得**落在 `.gitignore` 覆盖的 `scratch/`。
_ARCHIVE_DIR = ".cursor/plans/goals/evidence"
_ENTRY = "tools/two_tree_recheck.py"

#: 判词行前缀（入口的纯度契约：只有 PASS / FAIL / SUMMARY / TREE / COMPARE / DIFF / NOT-GREEN）。
_VERDICT_PREFIXES = ("PASS ", "FAIL ", "SUMMARY ", "TREE ", "COMPARE ", "DIFF ", "NOT-GREEN ")

#: 本轮归档的两份判词（收口 cycle 由两树入口写入）。
_CURRENT = f"{_ARCHIVE_DIR}/GOAL-20261004-029-verdict-current.txt"
_CLEAN = f"{_ARCHIVE_DIR}/GOAL-20261004-029-verdict-clean.txt"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _has_cr(path: Path) -> bool:
    """逐字节扫 `\\r`（**不**用文本模式读 —— 那正是本判据要防的形态）。"""
    return b"\r" in path.read_bytes()


def _verdict_lines(path: Path) -> list[str]:
    return [line for line in path.read_bytes().decode("utf-8").splitlines() if line.strip()]


def _write_like_the_entry(text: str, dest: Path) -> None:
    """按**入口的写法**落盘（`write_text(..., newline="")` ⇒ 二进制安全的逐行形态）。

    与 `tools/two_tree_recheck.py::dump_verdicts` 同一形态；本判据用它做「绿」的
    那一向（反证的另一向是**文本模式**）。
    """
    dest.write_text(text, encoding="utf-8", newline="")


class TestTheEntryWritesBinarySafely:
    """地基事实：两树入口的落盘形态是二进制安全的（`newline=""`）。"""

    def test_the_entry_writes_with_newline_empty(self) -> None:
        source = (_ROOT / _ENTRY).read_text(encoding="utf-8")
        assert 'newline=""' in source, (
            '两树入口的判词写盘必须显式 newline=""（否则 Windows 上会写成 CRLF）'
        )

    def test_the_entry_has_both_verdict_destinations(self) -> None:
        source = (_ROOT / _ENTRY).read_text(encoding="utf-8")
        assert "--verdict-current" in source and "--verdict-clean" in source, (
            "两份判词必须各自可指定落点（只留一份 = 无法逐行比对）"
        )

    def test_the_archive_dir_is_not_gitignored(self) -> None:
        """落点**在树**（承 R26-7：`scratch/` 是树外 ⇒ 不能作为可复核物证）。"""
        gitignore = (_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "scratch/" in gitignore, "前提：scratch/ 确实被忽略（本判据的对比面）"
        assert "evidence/" not in gitignore and f"{_ARCHIVE_DIR}/" not in gitignore, (
            "归档目录不得被 .gitignore 覆盖（那等于又落回树外）",
        )


class TestTheTextModeHazardIsReal:
    """反证的地基：文本模式**在本平台**是否改字节（Windows 会 ⇒ `sha256` 变）。

    **平台口径**（CI 首跑实测）：`Path.write_text` 的行尾转换是**平台相关**的 ——
    Windows 把 `\n` 写成 `\r\n`，**Linux / macOS 不转换**。因此
    「文本模式必须与二进制模式产生不同 `sha256`」这条断言**只在 Windows 成立**；
    在 Linux 上写死它会让判据**假红**（实测：CI 的 `quality-ubuntu-latest` 报
    `文本模式必须与二进制模式产生不同 sha256`，而本地 Windows 全绿）。

    本类因此分两档（都不放宽，只是**各自说各自平台的事实**）：

    - **跨平台硬断言**：入口那种写法（`newline=""`）**必须**产出纯 LF —— 这是归档纪律的载体；
    - **平台事实**：`\r\n` 转换是否发生**按平台断言**。非 Windows 上如实断言「不转换」，
      并说明**归档一律用二进制写盘**这条纪律**不因平台而异**（复检脚本要跨平台可比）。
    """

    def test_the_entry_style_is_lf_only(self, tmp_path: Path) -> None:
        """跨平台硬断言：入口那种写法产出纯 LF（归档纪律的载体）。"""
        binary = tmp_path / "binary.txt"
        _write_like_the_entry("PASS a\nPASS b\n", binary)
        assert not _has_cr(binary), ("入口写法必须产出纯 LF", binary.read_bytes())

    def test_text_mode_hazard_matches_this_platform(self, tmp_path: Path) -> None:
        """平台事实：Windows 上文本模式写 CRLF（`sha256` 因而不同）；其他平台**不转换**。"""
        import os

        payload = "PASS a\nPASS b\n"
        binary = tmp_path / "binary.txt"
        text = tmp_path / "text.txt"
        _write_like_the_entry(payload, binary)
        text.write_text(payload, encoding="utf-8")  # 文本模式

        if os.name == "nt":
            assert _sha256(binary) != _sha256(text), (
                "Windows 上文本模式必须改字节（否则本判据的两向反证无能）"
            )
            assert _has_cr(text), "差异的来源应当是 CRLF（否则本判据的归因错了）"
        else:
            assert not _has_cr(text), (
                "非 Windows 平台不应出现 CRLF 转换（若出现，本判据的归因假设要更新）",
                text.read_bytes(),
            )

    def test_git_normalization_would_hide_it(self) -> None:
        """**为什么 `git diff` 不足**：`.gitattributes` 把行尾归一化 ⇒ 差异被静默吞掉。"""
        attributes = (_ROOT / ".gitattributes").read_text(encoding="utf-8")
        assert "eol=lf" in attributes, (
            "前提：仓里把提交内容归一化成 LF ⇒ git diff 看不见 CRLF 差异（本判据必须读 raw bytes）",
        )


class TestTheTwoArchivesAgree:
    """主判据：两份归档存在、`sha256` 相同、行尾为 LF。"""

    def test_both_archives_exist(self) -> None:
        missing = [name for name in (_CURRENT, _CLEAN) if not (_ROOT / name).is_file()]
        assert missing == [], (
            "两份判词必须都在树（缺一即无法逐行比对）",
            missing,
        )

    def test_the_two_archives_have_the_same_sha256(self) -> None:
        current, clean = _ROOT / _CURRENT, _ROOT / _CLEAN
        assert _sha256(current) == _sha256(clean), (
            "两份判词必须逐字节相同（「两树同结论」的物证）",
            {"current": _sha256(current), "clean": _sha256(clean)},
        )

    def test_neither_archive_has_carriage_returns(self) -> None:
        for name in (_CURRENT, _CLEAN):
            assert not _has_cr(_ROOT / name), (
                f"{name} 含 CR ⇒ 落盘用了文本模式（PowerShell 重定向 / write_text 缺 newline）",
            )

    def test_the_verdicts_are_pure_and_non_empty(self) -> None:
        """受判面非空（MEM-156）+ 纯度：只含判词行前缀，且行数为正。"""
        for name in (_CURRENT, _CLEAN):
            lines = _verdict_lines(_ROOT / name)
            assert lines, (f"{name} 是空文件 ⇒ 未取证", name)
            impure = [line for line in lines if not line.startswith(_VERDICT_PREFIXES)]
            assert impure == [], (
                f"{name} 含非判词行（两树入口会拒绝它们；归档必须是**判词**而不是原始输出）",
                impure[:3],
            )

    def test_the_archives_record_the_same_verdict_sequence(self) -> None:
        """逐行相同（`sha256` 相同是它的充分条件，这里把结论也读出来 —— 判词可列举）。"""
        current = _verdict_lines(_ROOT / _CURRENT)
        clean = _verdict_lines(_ROOT / _CLEAN)
        assert current == clean, (
            "两树逐行相同（逐行比对是入口的结论；归档必须能独立复核它）",
            [line for line in current if line not in clean][:3],
        )


class TestTheArchivesAreSelfDescribed:
    """归档必须能被独立读懂：判词里点出本 GOAL，且不含绝对路径（承两树入口的纯度）。"""

    def test_the_archives_are_identified_by_their_path(self) -> None:
        """自描述：归档**文件名**点名本 GOAL（判词行本身只有 PASS/FAIL，不带 GOAL 名）。

        判词文件的纯度契约（只有判词行）与「可被独立辨认」是两件事 ——
        后者由**路径**承担：`GOAL-20261004-029-verdict-{current,clean}.txt`
        落在 `docs/../.cursor/plans/goals/evidence/` 下，他人 clone 后一眼可辨归属。
        """
        for name in (_CURRENT, _CLEAN):
            path = pathlib.Path(name)
            assert "GOAL-20261004-029" in path.name, (
                "归档文件名必须点名它的 GOAL（判词行不含 GOAL 名，归属由路径承担）",
                path.name,
            )
            assert path.parent.as_posix() == _ARCHIVE_DIR, (path.parent.as_posix(),)

    def test_no_absolute_paths_in_the_verdicts(self) -> None:
        """判词不得嵌本树绝对路径（两棵树的路径必然不同 ⇒ 那类判词是坐标不是结论）。"""
        drive = re.compile(r"[A-Za-z]:[\\/]")
        for name in (_CURRENT, _CLEAN):
            text = (_ROOT / name).read_text(encoding="utf-8")
            assert not drive.search(text), (
                f"{name} 含绝对路径（两树入口会拒绝；归档必须路径无关）",
                drive.findall(text)[:3],
            )


def test_the_assertion_helpers_are_not_vacuous(tmp_path: Path) -> None:
    """受判面自检：本文件的辅助函数在合成输入上给出预期读数（防恒真）。"""
    sample = tmp_path / "sample.txt"
    _write_like_the_entry("PASS x\nFAIL y\n", sample)
    assert _verdict_lines(sample) == ["PASS x", "FAIL y"], _verdict_lines(sample)
    assert not _has_cr(sample)
    assert len(_sha256(sample)) == 64
    assert pathlib.Path(_ROOT / _ENTRY).is_file()
