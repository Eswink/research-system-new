"""m0 见证必须覆盖**当前这棵树**（GOAL-20261020-090）。

**它补哪一格**：`docs/architecture/LOCAL_GATE_PROTOCOL.md` 的「记录面覆盖」规定了顺序
「写记录 → 记录面判据 → 全量门」，但那条纪律**只靠人记住**。GOAL-089 的收口为此多跑了
三次全量 m0（每次约 16 分钟独占）：每多一次记录提交，上一次的终态行就失效一次 ——
于是「最后一次 m0 的证据」与「现在这棵树」不是同一个对象。

`tools/run_m0_with_witness.py` 把「门跑的是哪棵树」写成树内见证；本判据**重算当前树的
指纹**并与见证比对。两者相等 ⇒「最后一次 m0 覆盖的就是现在这棵树」。

**三态语义（必须分得开）**：

* 见证不存在 ⇒ **判红**（点名该跑哪个入口）。「没跑过」不得被读成「跑过了且覆盖当前树」
  —— 这正是本判据要消灭的含混。
* 见证存在但指纹不等 ⇒ **判红**，并**逐条点名**差在哪个文件（路径 + 状态 + digest）。
* 指纹相等 ⇒ 判过；`green` 字段为 `False` 时**照实**报告「最后一次 m0 是红的」
  （判过指的是**覆盖关系成立**，不是「门一定是绿的」—— 红绿是 `terminal_line` 的事，
  本判据不冒充它，否则「跑过但红了」会退化成「没跑过」）。

**边界**：本判据只证明**本地**这棵树被覆盖过；CI 覆盖的是推送后的树，两者对象不同。
它也不校验 23 项是否都执行完 —— 那是终态行的职责。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
WITNESS = ROOT / ".cursor" / "plans" / "goals" / "evidence" / "M0-WITNESS.json"
#: 与 `tools/run_m0_with_witness.py` 的 `MARKER` 逐字同路径：它存在 ⇒ 本次 m0 正由
#: 见证入口运行（见证要等门跑完才写）。
MARKER = ROOT / ".cursor" / "plans" / "goals" / "evidence" / "M0-WITNESS.in-progress"
TOOL = ROOT / "tools" / "run_m0_with_witness.py"


def _in_progress() -> bool:
    """**第三种状态**：「正由见证入口跑着」（见证尚未写）。

    为什么必须有它：见证在门**跑完之后**才写，而本判据**本身就在门里**跑 ⇒
    「本次运行里见证还不存在」是**结构必然**，不是缺陷。把这种情况判红会让
    「跑一次门」永远无法自证覆盖 —— 那是把判据变成了它自己的反例。
    区分方式不靠猜：见证入口在 `subprocess.run` 之前写下标记、在 `finally` 里删除
    ⇒ 标记在场就是「正在进行」，判据**跳过并点名**（不是静默通过：`skip` 在
    `-q` 输出里可见，且 `-rs` 会给出理由）。
    """
    return MARKER.is_file()


def _tool_module() -> Any:
    """按**路径**加载见证工具（`tools/` 没有 `__init__.py`，静态 import 会让 mypy
    报「Source file found twice」——与 `MEM` 里 `tools-dir-load-by-path` 同一坑）。

    逐字遵守那条纪律：**先写 `sys.modules` 再 `exec_module`**，否则模块内的
    `from __future__` 之外的 dataclass/typing 求值会崩。
    """
    import importlib.util

    name = "run_m0_with_witness"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, TOOL)
    assert spec is not None and spec.loader is not None, f"无法加载 {TOOL}"
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def _witness() -> dict[str, Any]:
    if _in_progress():
        pytest.skip(
            "m0 正由见证入口运行（标记在场）⇒ 见证要等门跑完才写。"
            "本次覆盖由**跑完后写下的见证**证明，不在门内部自证。"
        )
    assert WITNESS.is_file(), (
        f"m0 见证不在树：{WITNESS.relative_to(ROOT)}。**「没跑过」不是「覆盖当前树」** —— "
        "用 `uv run --frozen --no-sync python -B tools/run_m0_with_witness.py` 跑一次全量 m0，"
        "它会在**跑完后**写见证（顺序必须是「记录写完 → 跑门 → 不再改树」）。"
    )
    parsed: dict[str, Any] = json.loads(WITNESS.read_text(encoding="utf-8"))
    return parsed


def test_the_witness_is_for_the_tree_we_are_looking_at() -> None:
    """核心：见证里的指纹 == 当前树的指纹。"""
    tool = _tool_module()
    recorded = _witness()
    current = tool.tree_fingerprint()
    if current == recorded.get("fingerprint_after"):
        return

    # 逐条点名差异，而不是只说「不相等」：判词要能直接指向该改哪一步。
    def rows(fingerprint: Any) -> set[tuple[str, str, str]]:
        dirty = fingerprint.get("dirty", []) if isinstance(fingerprint, dict) else []
        return {
            (str(item.get("path")), str(item.get("status")), str(item.get("sha256")))
            for item in dirty
        }

    before = rows(recorded.get("fingerprint_after"))
    now = rows(current)
    added = sorted(now - before)
    removed = sorted(before - now)
    pytest.fail(
        "m0 见证与当前树**不一致** ⇒ 最后一次全量 m0 覆盖的不是现在这棵树"
        "（典型成因：跑完门之后又提交/改动了受判文件，于是那次终态行失效）。\n"
        f"  见证记录的 HEAD: {recorded.get('ran_at_head')}；当前 HEAD: {current.get('head')}\n"
        f"  当前有而见证没有（{len(added)} 项）：{added[:10]}\n"
        f"  见证有而当前没有（{len(removed)} 项）：{removed[:10]}\n"
        "  修法：把记录推到最后一个动作，然后重跑 "
        "`uv run --frozen --no-sync python -B tools/run_m0_with_witness.py`，之后**不再改树**。"
    )


def test_the_witness_records_a_terminal_line() -> None:
    """见证必须抄下终态行 —— 否则「跑过」与「跑完了」不可区分。"""
    recorded = _witness()
    terminal = str(recorded.get("terminal_line", "")).strip()
    assert terminal, (
        f"见证里没有终态行（`terminal_line` 为空）：{WITNESS.relative_to(ROOT)}。"
        "runner 没有跑到终态 ⇒ 这次运行不能作为覆盖证据。"
    )
    assert terminal.startswith("PASS: profile=m0;") or terminal.startswith("FAILED:"), (
        f"终态行形态不认识：{terminal!r}"
    )


def test_the_witness_reports_red_honestly_instead_of_hiding_it() -> None:
    """**红也照记**：`green` 必须与终态行一致（不允许把红写成「没跑」）。"""
    recorded = _witness()
    terminal = str(recorded.get("terminal_line", "")).strip()
    expected_green = terminal == "PASS: profile=m0; 23 deterministic checks"
    assert recorded.get("green") is expected_green, (
        f"见证的 `green`={recorded.get('green')!r} 与终态行 {terminal!r} 不一致 —— "
        "见证必须如实记录红绿，否则「跑过但红了」会退化成「没跑过」"
    )
    # 红的见证在 CI 上不该让**这条**判据拦路（它判的是覆盖关系，不是门本身）；
    # 但必须让它可见：把终态行原样放进消息里。
    if not expected_green:
        pytest.skip(f"最后一次本地 m0 不是全绿（覆盖关系仍成立）：{terminal}")


def test_the_witness_tool_is_wired_to_the_canonical_runner() -> None:
    """入口必须指向 canonical runner（不是自己拼一套检查）。"""
    source = TOOL.read_text(encoding="utf-8")
    assert "run_all_checks.py" in source, source[:400]
    assert '"--profile", "m0"' in source or "'--profile', 'm0'" in source, source[:400]
    assert "--keep-going" in source, source[:400]
    # 反过来：runner 真的在那个路径上（改名即判红，见证不得指向不存在的入口）。
    assert (ROOT / ".cursor/skills/cursor-framework-check/scripts/run_all_checks.py").is_file()


def test_the_witness_is_committed_not_scratch() -> None:
    """见证必须**进树**（`scratch/` 在 gitignore 里 ⇒ 放那里不算证据）。"""
    relative = WITNESS.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ("git", "check-ignore", "--quiet", relative),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    # `check-ignore` 命中 ⇒ exit 0 ⇒ 该路径被 ignore ⇒ 不算交付。
    assert result.returncode != 0, (
        f"{relative} 被 gitignore 忽略 ⇒ 见证不算树内证据。"
        "它必须落在 `evidence/` 下并被跟踪（与两树复检的判词归档同一落点约定）。"
    )


def test_the_in_progress_state_is_a_real_third_state_not_a_silent_pass() -> None:
    """**第三态不得退化成静默通过**：标记在场 ⇒ `skip`（理由可见），而非 `pass`。

    为什么单列一条：`pytest.skip` 与「断言恒真」在 `-q` 输出里**只差一个字母**（`.` vs `s`）。
    如果没人钉住这个语义，将来把 `_witness()` 里的 `skip` 改成 `return {}` 就会让
    「门正在跑」与「从没跑过」再次不可区分 —— 那正是本判据存在的理由。
    """
    source = Path(__file__).read_text(encoding="utf-8")
    assert "pytest.skip(" in source, "第三态必须用 skip（可见），不能用静默 return"
    assert "MARKER.is_file()" in source, "第三态必须由**标记的在场**判定，不靠猜"
    # 反向：标记路径与工具里的 `MARKER` 逐字一致（改了一边而没改另一边 ⇒ 第三态失效）。
    tool_source = TOOL.read_text(encoding="utf-8")
    assert "M0-WITNESS.in-progress" in tool_source, tool_source[:400]
    assert "M0-WITNESS.in-progress" in source, source[:400]
    # 标记必须在 `finally` 里删除（异常路径也不留残骸 ⇒ 否则下一次会永远 skip）。
    assert "finally:" in tool_source and "MARKER.unlink(missing_ok=True)" in tool_source, (
        tool_source[:800]
    )
