"""`skill_invocation_guard` 的行为判据：直接读 `.agents/skills/**/SKILL.md` 必须被拒。

**为什么需要**：技能正文按需加载，`Read` / `Bash cat` 能绕开 Skill 工具 ——
绕过之后既没有技能名可引用，也没有「本次调用过哪个技能」的事实。门禁只写在
配置里不算数：`zcode.json` 的注册面由 `test_zcode_hook_registration.py` 判，
**裁决本身**由本文件判。

**射程边界是判据的一部分**：`.cursor/skills/` 不拦（ZCode 侧那 17 个技能没有
Skill 工具入口，拦了等于让正文彻底不可读），遍历式读取（`grep -r`）也不拦。
这两条写成**显式 allow 臂**，让边界可见而不是隐形。
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
GUARD: Final[Path] = ROOT / "tools" / "zcode-hooks" / "skill_invocation_guard.py"


def _load() -> ModuleType:
    """按路径加载 hook（`tools/` 不是包；**先写 `sys.modules` 再 `exec_module`**）。"""
    name = "zcode_skill_invocation_guard"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, GUARD)
    assert spec is not None and spec.loader is not None, f"无法按路径加载 {GUARD}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _decide(payload: object) -> object:
    module = _load()
    decide = module.decide
    assert callable(decide), "hook 必须暴露 decide(payload)"
    return decide(payload)


def _reason(verdict: object) -> str:
    assert isinstance(verdict, dict), f"应为裁决对象，实际 {verdict!r}"
    output = verdict.get("hookSpecificOutput")
    assert isinstance(output, dict), f"裁决必须包在 hookSpecificOutput 里，实际 {verdict!r}"
    assert output.get("hookEventName") == "PreToolUse", "事件名必须是 PreToolUse"
    assert output.get("permissionDecision") == "deny", "该路径必须判 deny"
    reason = output.get("permissionDecisionReason")
    assert isinstance(reason, str) and reason.strip(), "deny 必须给出理由"
    return reason


def _read_payload(path: str) -> dict[str, object]:
    return {"tool_name": "Read", "tool_input": {"file_path": path}}


def _bash_payload(command: str) -> dict[str, object]:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def test_reading_a_skill_file_is_denied() -> None:
    """正向臂：`Read` 命中受门禁的 SKILL.md ⇒ 拒绝，且理由**指向 Skill 工具**。

    拒绝的目的不是禁掉正文，而是把加载方式导向可取证的那条路：Skill 工具会登记调用，
    直接读文件不会。理由必须给出下一步动作，否则模型只会换个办法绕过。
    """
    reason = _reason(_decide(_read_payload(".agents/skills/citation-binding/SKILL.md")))
    assert "Skill(" in reason, f"理由必须给出下一步动作（调用 Skill 工具），实际：{reason}"
    assert "citation-binding" in reason, f"理由必须点名技能名，实际：{reason}"


def test_absolute_and_backslash_paths_are_denied() -> None:
    """Windows 侧三种形态（绝对路径 / `./` 前缀 / 反斜杠）都要命中。"""
    for target in (
        str(ROOT / ".agents" / "skills" / "citation-binding" / "SKILL.md"),
        "./.agents/skills/citation-binding/SKILL.md",
        ".agents\\skills\\citation-binding\\SKILL.md",
    ):
        _reason(_decide(_read_payload(target)))


def test_bash_reading_a_skill_file_is_denied() -> None:
    """Bash 面：`cat` 点名受门禁的 SKILL.md ⇒ deny（否则 Read 门禁可被一步绕过）。"""
    for command in (
        "cat .agents/skills/recheck/SKILL.md",
        "sed -n '1,50p' .agents/skills/recheck/SKILL.md",
        "type .agents\\skills\\recheck\\SKILL.md",
    ):
        reason = _reason(_decide(_bash_payload(command)))
        assert "recheck" in reason, f"理由必须点名技能名，实际：{reason}"


def test_reading_ordinary_sources_is_allowed() -> None:
    """反证臂：普通源码 / 文档读取不得被拦（门禁不能变成读文件的税）。"""
    for target in ("AGENTS.md", "packages/application/deliverable/references.py", "zcode.json"):
        assert _decide(_read_payload(target)) is None, f"{target} 不该被拦"


def test_running_a_skill_script_is_allowed() -> None:
    """反证臂：跑技能自带的脚本不是「读技能正文」。"""
    verdict = _decide(_bash_payload("python -B .cursor/skills/recheck/scripts/validate.py"))
    assert verdict is None, "跑校验脚本不该被拦"


def test_cursor_skills_are_outside_the_guard() -> None:
    """射程边界（显式）：`.cursor/skills/` 不拦 —— ZCode 侧没有它们的 Skill 入口。"""
    verdict = _decide(_read_payload(".cursor/skills/recheck/SKILL.md"))
    assert verdict is None, ".cursor/skills/ 必须在射程外，否则那些正文彻底不可读"


def test_traversal_reads_are_outside_the_guard() -> None:
    """射程边界（显式）：不点名 SKILL.md 的遍历式读取不拦（已登记为残余）。"""
    for command in ("grep -r 引用 .agents/skills", "ls .agents/skills/*/", "find .agents/skills"):
        assert _decide(_bash_payload(command)) is None, f"{command!r} 属于已登记的射程外形态"


def test_malformed_payloads_fail_open() -> None:
    """输入畸形时放行：观测型判据不得把会话卡死（安全硬门禁另按 fail-closed 设计）。"""
    for payload in (None, {}, {"tool_name": "Read"}, {"tool_name": "Read", "tool_input": None}):
        assert _decide(payload) is None, f"畸形载荷 {payload!r} 必须放行"


def test_the_hook_runs_as_a_real_process() -> None:
    """真进程臂：stdin 用 UTF-8（含 BOM 也要认），stdout 必须是可解析的 JSON。"""
    payload = json.dumps(_read_payload(".agents/skills/criterion-authoring/SKILL.md"))
    completed = subprocess.run(
        [sys.executable, "-B", str(GUARD)],
        input=b"\xef\xbb\xbf" + payload.encode("utf-8"),
        capture_output=True,
        cwd=str(ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    output = json.loads(completed.stdout.decode("utf-8"))
    reason = _reason(output)
    assert "criterion-authoring" in reason
