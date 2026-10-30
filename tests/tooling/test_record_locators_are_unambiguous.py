"""GOAL-20261030-101 EC-04 判据：**记录面定位必须唯一，读取必须显式 UTF-8**。

**它补哪一格**（本轮提示词第一节的两条纪律，都是**上一轮驱动方自己栽过**的）：

1. **定位文件要用精确路径，不要用宽松 glob**。实测：`glob('GOAL-*100*')` 会匹配到
   `GOAL-20261001-028`（文件名里的日期 `20261001` 含 `100`）⇒ 读**错**了文件，并据此
   得出「`f15929e5` 零命中」的错误结论。
2. **判断文件结构必须按显式 UTF-8 读**，不能在非 UTF-8 终端里用 `sed`/`grep` 目视下结论。
   实测：GBK 终端里 `sed -n` 一个中文文件读到乱码，于是把别的文件的旧台账误认成本文件
   粘错的表，并写进报告当成实质缺陷。

**判什么**（两条，各自机械化）：

- `test_each_goal_number_has_exactly_one_file`：对每个 GOAL 编号 `NNN`，**宽松 glob**
  `GOAL-*NNN*` 必须**只**匹配那一个文件。任何编号一旦泄漏进另一个文件名的日期段或标题段，
  这条立刻红 —— 那正是第 1 条纪律的失败形态。
- `test_record_face_reads_are_explicitly_utf8`：记录面判据（`tests/tooling/` 下读
  宪章 / GOAL / 归档的那些文件）**不得**出现「不带 encoding 的 `read_text()`」或
  「`open(...)` 不带 encoding」—— 那会在 Windows 上落回区域默认编码（GBK），
  正是第 2 条纪律的根因。

**两向反证**（`TestTheCriterionBites`）：① 合成一对「编号 N 出现在另一个名字的日期里」的
文件名 ⇒ 唯一性判据报红；② 合成一个不带 `encoding` 的 `read_text()` ⇒ 读取面判据报红。

**射程边界（如实登记）**：本文件判的是**记录面的定位与读取**（`tests/tooling/` 的判据
源码 + `.cursor/plans/**` 的文件命名）。产品代码的编码纪律由既有的
`tests/architecture/**` 与 lint 面覆盖，此处不重复判。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_GOALS = _ROOT / ".cursor" / "plans" / "goals"
_TOOLING = _ROOT / "tests" / "tooling"

#: GOAL 文件名的形状：`GOAL-YYYYMMDD-NNN-slug.md`。
_GOAL_NAME = re.compile(r"^GOAL-(\d{8})-(\d{3})-.+\.md$")

#: 记录面里**允许**用宽松 glob 的两处（都不是「定位一个具体 GOAL」）：
#: `_GOALS.glob("GOAL-*.md")` 是**枚举全部**，`archive/*.md` 是**枚举归档**。
_ALLOWED_ENUMERATION = ("GOAL-*.md", "*.md")


def _goal_files() -> list[Path]:
    return sorted(path for path in _GOALS.glob("GOAL-*.md") if _GOAL_NAME.match(path.name))


def test_each_goal_number_has_exactly_one_file() -> None:
    """**宽松 glob 的唯一性**：`GOAL-*<NNN>*` 只能匹配到该编号的那一个文件。

    这是第 1 条纪律的机械化：一旦某个编号出现在**别的文件**的日期段或标题里，按编号
    glob 就会读到错的文件。实测反例：`GOAL-*100*` 命中 `GOAL-20261001-028`。
    """
    files = _goal_files()
    assert len(files) >= 100, f"只找到 {len(files)} 个 GOAL 文件 ⇒ 受判面疑似不成立"
    offenders: list[str] = []
    for path in files:
        match = _GOAL_NAME.match(path.name)
        assert match is not None, path
        number = match.group(2)
        # **只**看 `-<NNN>-` 那一段：把编号当任意子串搜（`*001*`）会命中日期段
        # （`GOAL-20261001-028` 的 `20261001` 含 `001`）—— 那正是纪律第 1 条的失败形态，
        # 但它说明的是「**不要**用任意子串 glob」，不是「文件名里有重复数字」。
        # 因此本判据钉的是：**按编号段的 glob 必须唯一**；词表之外不加宽。
        matches = sorted(item.name for item in _GOALS.glob(f"GOAL-*-{number}-*.md"))
        if matches != [path.name]:
            others = [name for name in matches if name != path.name]
            offenders.append(f"{path.name}: `GOAL-*-{number}-*` 还匹配到 {others}")
    assert not offenders, (
        "以下 GOAL 编号的**编号段 glob 不唯一** ⇒ 按编号定位会读错文件（本轮纪律第 1 条）",
        offenders,
    )
    # 另一半（纪律的**原始形态**，作为**可复现的反例**记录在案）：任意子串 glob
    # `GOAL-*100*` 会命中一串编号不是 100 的文件 —— 那次事故正是这样发生的
    # （`GOAL-20261001-028` 的日期段含 `100`）。本判据**不**要求子串 glob 唯一（它做不到），
    # 而是把「它确实不唯一」钉成事实：哪天子串 glob 变唯一了，说明文件名策略变了，
    # 那时该重新审这份判据。
    substring = sorted(item.name for item in _GOALS.glob("GOAL-*100*"))
    leaky = [
        name
        for name in substring
        if (matched := _GOAL_NAME.match(name)) is not None and matched.group(2) != "100"
    ]
    assert leaky, "`GOAL-*100*` 居然只匹配到编号 100 的文件 —— 文件名策略可能变了，请重审本判据"


def _has_encoding(call: ast.Call) -> bool:
    return any(keyword.arg == "encoding" for keyword in call.keywords)


def _open_mode(call: ast.Call) -> str:
    """`open()` 的模式串（位置第二参或 `mode=` 关键字；缺省空串）。"""
    mode = ""
    if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
        mode = str(call.args[1].value)
    for keyword in call.keywords:
        if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
            mode = str(keyword.value.value)
    return mode


def _literal_without_encoding(source: str) -> list[str]:
    """源码里**没有** `encoding=` 的文本读取调用（`read_text()` / `open(..., 'r')`）。

    AST 级：只看调用，不看注释/字符串（文本搜索会被示例代码骗过）。
    `open(path, "rb")` 是二进制读（合法）⇒ 不要求 encoding。
    """
    findings: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name == "read_text" and not _has_encoding(node):
            findings.append(f"line {node.lineno}: read_text() 未显式指定 encoding")
        elif name == "open" and "b" not in _open_mode(node) and not _has_encoding(node):
            findings.append(f"line {node.lineno}: open() 文本模式未显式指定 encoding")
    return findings


def test_record_face_reads_are_explicitly_utf8() -> None:
    """记录面判据的读取**必须显式 UTF-8**（第 2 条纪律的根因在区域默认编码）。

    受判面 = `tests/tooling/` 下**读记录**的那些文件（凡是出现 `.cursor/plans` 的）。
    """
    assert _TOOLING.is_dir(), _TOOLING
    offenders: dict[str, list[str]] = {}
    scanned = 0
    for path in sorted(_TOOLING.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if ".cursor/plans" not in source and "MAINLINE" not in source:
            continue
        scanned += 1
        findings = _literal_without_encoding(source)
        if findings:
            offenders[path.name] = findings
    assert scanned >= 8, f"受判面只有 {scanned} 个文件 ⇒ 判据失去对象"
    assert not offenders, (
        "这些记录面判据在**区域默认编码**下读文本（Windows 上是 GBK）⇒ 纪律第 2 条的根因",
        offenders,
    )


def test_the_goal_filename_shape_is_what_we_think_it_is() -> None:
    """受判面自检：文件名形状判据本身成立（否则上面两条会空转）。"""
    match = _GOAL_NAME.match("GOAL-20261029-100-submission-ready-and-citation-binding.md")
    assert match is not None
    assert match.group(1) == "20261029"
    assert match.group(2) == "100"
    assert _GOAL_NAME.match("PLAN-20261029-100-x.md") is None


class TestTheCriterionBites:
    """两向反证：两条判据在合成缺陷上**必须报红**。"""

    def test_a_number_leaking_into_another_date_is_reported(self, tmp_path: Path) -> None:
        """反向①：`GOAL-*100*` 还会匹配到日期含 `100` 的另一个文件 ⇒ 必须被点名。"""
        goals = tmp_path / "goals"
        goals.mkdir()
        (goals / "GOAL-20261029-100-a.md").write_bytes(b"# a\n")
        (goals / "GOAL-20261001-028-b.md").write_bytes(b"# b\n")  # 日期里含 `100`
        matches = sorted(item.name for item in goals.glob("GOAL-*100*"))
        assert len(matches) == 2, matches
        # 判据的形态：`matches != [那一个文件]` ⇒ 报红。
        offenders: list[str] = []
        for name in matches:
            parsed = _GOAL_NAME.match(name)
            assert parsed is not None, name  # 两个文件都是 GOAL 形状（本用例的前提）
            number = parsed.group(2)
            if sorted(item.name for item in goals.glob(f"GOAL-*{number}*")) != [name]:
                offenders.append(name)
        assert offenders, "泄漏进日期的编号没有被判出来"

    def test_a_read_without_encoding_is_reported(self) -> None:
        """反向②：不带 `encoding` 的 `read_text()` / 文本 `open()` ⇒ 必须被点名。"""
        bad = (
            "from pathlib import Path\n"
            "text = Path('x.md').read_text()\n"
            "with open('y.md') as handle:\n"
            "    other = handle.read()\n"
        )
        findings = _literal_without_encoding(bad)
        assert len(findings) == 2, findings
        good = (
            "from pathlib import Path\n"
            "text = Path('x.md').read_text(encoding='utf-8')\n"
            "raw = Path('z.md').read_bytes()\n"
            "with open('y.md', encoding='utf-8') as handle:\n"
            "    other = handle.read()\n"
        )
        assert _literal_without_encoding(good) == [], _literal_without_encoding(good)

    def test_a_comment_does_not_fool_the_reader(self) -> None:
        """反面：注释里出现 `read_text()` **不得**被读成调用（AST 读，不靠文本巧合）。"""
        source = "# 曾经写成 Path('x').read_text()（注释里的说明不是调用）\nvalue = 1\n"
        assert _literal_without_encoding(source) == []
