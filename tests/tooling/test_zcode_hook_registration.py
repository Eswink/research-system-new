"""ZCode 侧门禁的注册面判据：`zcode.json` 里的 hook 必须真的会跑。

**为什么需要**：`zcode.json` 不在任何既有门的射程内 —— 根目录清单判据只 glob
`*.yml` / `*.yaml`，prettier / eslint / tsconfig 都用显式文件列表且不含它。
⇒ 一份拼错事件名、`enabled` 漏写、或脚本路径不存在的配置会**静默不生效**，
而所有既有判据照绿。本判据把「这份配置会被 ZCode 执行」压成可机械验证的事实。

配置形态来自本机 ZCode bundle 实测（`hooks.events.<Event>` 与
`hooks.enabled`）；事件名闭集是七个，多一个即静默不触发。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CONFIG: Final[Path] = ROOT / "zcode.json"

#: ZCode 支持的**全部**事件名（`diagnosing-hooks` 与 bundle 的七项闭集）。
SUPPORTED_EVENTS: Final[frozenset[str]] = frozenset({
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PostToolUseFailure",
    "Stop",
})

#: `process` 型 hook 允许的字段（混入 `command` 型字段会让该 hook 被丢弃）。
PROCESS_FIELDS: Final[frozenset[str]] = frozenset({
    "type",
    "command",
    "args",
    "timeoutMs",
    "statusMessage",
    "async",
})

#: 本仓必须注册的两个事件（少一个就等于显式调用面不存在）。
REQUIRED_EVENTS: Final[frozenset[str]] = frozenset({"SessionStart", "PreToolUse"})

#: `${ZCODE_PROJECT_DIR}` 前缀：插件根变量在配置面 hook 里不可用。
PROJECT_DIR_VAR: Final[str] = "${ZCODE_PROJECT_DIR}"


def _config() -> dict[str, object]:
    parsed: object = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict), "zcode.json 顶层必须是 JSON object"
    return parsed


def _hooks() -> dict[str, object]:
    hooks = _config().get("hooks")
    assert isinstance(hooks, dict), "zcode.json 缺少 hooks 块 ⇒ ZCode 不会注册任何 hook"
    return hooks


def _events() -> dict[str, list[dict[str, object]]]:
    events = _hooks().get("events")
    assert isinstance(events, dict), "hooks.events 缺失（ZCode 读的是 hooks.events.<Event>）"
    typed = {str(name): list(entries) for name, entries in events.items()}
    return typed


def _iter_hook_commands() -> list[tuple[str, str, dict[str, object]]]:
    """`(事件名, matcher, hook 条目)` 三元组；matcher 为空串表示匹配全部。"""
    found: list[tuple[str, str, dict[str, object]]] = []
    for event, groups in _events().items():
        for group in groups:
            matcher = group.get("matcher", "")
            assert isinstance(matcher, str), f"{event} 的 matcher 必须是字符串"
            entries = group.get("hooks")
            assert isinstance(entries, list) and entries, f"{event} 的 hooks 必须是非空数组"
            for entry in entries:
                assert isinstance(entry, dict), f"{event} 的 hook 条目必须是对象"
                found.append((event, matcher, entry))
    return found


def test_the_hook_runner_is_switched_on() -> None:
    """配置面 hook 缺省**不执行**：`hooks.enabled` 必须显式为 `true`。

    反证：删掉这个键 ⇒ 本判据必红（这也是 ZCode 侧最常见的「配了但没跑」）。
    """
    enabled = _hooks().get("enabled")
    assert enabled is True, f"hooks.enabled 必须是 true，实际是 {enabled!r} ⇒ 全部 hook 不会执行"


def test_every_event_name_is_one_of_the_seven() -> None:
    """事件名闭集：拼错的名字被静默忽略，只有本判据能抓到。"""
    registered = set(_events())
    unknown = sorted(registered - SUPPORTED_EVENTS)
    assert not unknown, f"这些事件名不在 ZCode 的七项闭集内（会被静默忽略）：{unknown}"


def test_the_required_events_are_registered() -> None:
    """显式调用面由两个事件共同构成：索引注入 + 直接读文件拦截。"""
    missing = sorted(REQUIRED_EVENTS - set(_events()))
    assert not missing, f"缺少必需事件 {missing} ⇒ 显式调用面不成立"


def test_every_matcher_is_a_compilable_regex() -> None:
    """matcher 是**大小写敏感正则**；非法正则永不匹配（而且是静默的）。"""
    for event, matcher, _entry in _iter_hook_commands():
        if not matcher:
            continue
        try:
            re.compile(matcher)
        except re.error as error:
            raise AssertionError(f"{event} 的 matcher {matcher!r} 不是合法正则：{error}") from error


def test_every_process_hook_names_an_existing_script() -> None:
    """路径必须真实存在：`args` 用 `${ZCODE_PROJECT_DIR}` 展开后逐项核验。"""
    for event, _matcher, entry in _iter_hook_commands():
        assert entry.get("type") == "process", f"{event} 的 hook 必须是 process 型（跨平台）"
        extra = sorted(set(entry) - PROCESS_FIELDS)
        assert not extra, f"{event} 的 process hook 含非法字段 {extra} ⇒ 该 hook 会被丢弃"
        assert entry.get("command") in {"python", "python3"}, (
            f"{event} 的 command 必须是 python 解释器，实际 {entry.get('command')!r}"
        )
        args = entry.get("args")
        assert isinstance(args, list) and args, f"{event} 的 args 必须是非空数组"
        for raw in args:
            assert isinstance(raw, str), f"{event} 的 args 元素必须是字符串"
            if not raw.startswith(PROJECT_DIR_VAR):
                continue
            relative = raw[len(PROJECT_DIR_VAR) :].lstrip("/\\")
            assert (ROOT / relative).is_file(), f"{event} 引用的脚本不存在：{relative}"


def test_mimosa_stays_disabled_in_the_tracked_config() -> None:
    """仓库级显式关停不得因新增配置文件而丢失（两处配置会被合并读取）。"""
    plugins = _config().get("plugins")
    assert isinstance(plugins, dict), "zcode.json 缺少 plugins 块"
    enabled = plugins.get("enabledPlugins")
    assert isinstance(enabled, dict), "zcode.json 缺少 plugins.enabledPlugins"
    assert enabled.get("mimosa@zcode-plugins-official") is False, (
        "仓库级必须保持 mimosa 关停；否则会按用户级配置重新启用"
    )
