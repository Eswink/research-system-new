"""会话工具的 SDK 实现：把声明的工具名桥接到 ToolProvider Port（GOAL-028 EC-01）。

**它解决什么**：会话工具名会被 OpenHands SDK 的 registry 按名解析（`resolve_tool`），
而 registry 里的名字来自**工具实现自己**（`ToolDefinition.name` 由类名派生）。provider id
（`m12_artifact`）与 SDK 工具名（`artifact.read`）因此是**两个名字空间**——把前者直接
当后者用，只会得到 `KeyError: ToolDefinition '<id>' is not registered`（生产装配的实测
缺口）。本模块提供「工具名 → 实现」的**真实**实现：每个名字对应一个真去执行 provider
的 SDK 工具，而不是让会话起得来的空壳。

**边界（AGENTS.md §5）**：SDK 类型只在本包内可见；SDK 工具名与 provider id 的对应由
**协议声明**（`session_tool_bindings`）给出，本模块只负责把名字变成可解析的实现。
工具名的命名空间是**能力名**（如 `artifact.read`）——这也是策略求值看到的那个名字
（`PolicyEnforcingAgent._evaluate(action_event.tool_name)`）。

**失败形态（点名，不静默）**：调用桥抛错时，SDK 工具返回带错误文本的 observation
（`is_error=True`），错误消息由桥侧走既有 redaction 口径。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, ClassVar

from openhands.sdk.tool.registry import register_tool
from openhands.sdk.tool.schema import Action, Observation
from openhands.sdk.tool.tool import ToolDefinition, ToolExecutor
from pydantic import Field

#: 调用桥：`(工具参数, 会话上下文) → 结果文本`。抛错即视为工具失败（observation 带
#: `is_error`）。`conversation` 由 SDK 在执行点传入（可能是 None），桥用它取
#: **会话级**标识——同一会话内的两次调用因此共享同一命名空间，不同会话互不串台。
SessionToolInvoker = Callable[[dict[str, object], Any], str]


class SessionToolAction(Action):
    """会话工具的调用参数（自由形状：各 provider 的参数字段不同，桥负责解释）。"""

    arguments: dict[str, Any] = Field(default_factory=dict)


class SessionToolObservation(Observation):
    """会话工具的结果（`content` 是 SDK 既有的内容列表，经 `from_text` 构造）。"""


class _BridgeExecutor(ToolExecutor[SessionToolAction, SessionToolObservation]):
    """把一次工具调用转给调用桥；异常收敛成**带文本的**错误 observation。"""

    def __init__(self, invoker: SessionToolInvoker) -> None:
        self._invoker = invoker

    def __call__(
        self, action: SessionToolAction, conversation: Any = None
    ) -> SessionToolObservation:
        try:
            return SessionToolObservation.from_text(
                self._invoker(dict(action.arguments), conversation)
            )
        except Exception as exc:  # noqa: BLE001 - 失败必须变成可读 observation，不炸会话
            return SessionToolObservation.from_text(f"{type(exc).__name__}: {exc}", is_error=True)


class BoundSessionTool(ToolDefinition[SessionToolAction, SessionToolObservation]):
    """按名绑定调用桥的会话工具基类。

    子类经 `bound_tool_class()` 由 `type()` 动态构造，并锚定两件事：`name`（**声明**的
    工具名，显式给出——它含点号，不由类名反推）与 `invoker`（该类对应的调用桥）。
    `invoker` 是**类属性**而不是模块级字典：类与桥的对应关系因此不可被别的装配改写。
    """

    #: 本类对应的调用桥（由 `bound_tool_class()` 注入；缺省 None ⇒ 点名拒绝）。
    #: 必须是 `ClassVar`：本类是 pydantic 模型，非 `ClassVar` 的类属性会被当作**字段**
    #: （读它时 pydantic 的 `__getattr__` 抛 `AttributeError`）。
    invoker: ClassVar[Any] = None

    @classmethod
    def create(cls, conv_state: Any = None, **params: Any) -> Sequence[Any]:
        if params:
            raise ValueError(f"session tool {cls.name!r} does not accept parameters")
        invoker = cls.invoker
        if invoker is None:
            # 点名拒绝：名字在 registry 里但没有调用桥 ⇒ 装配不完整（不静默空转）。
            raise ValueError(f"session tool {cls.name!r} has no invoker wired in this assembly")
        return [
            cls(
                description=f"Research OS session tool {cls.name} (bridged to its provider).",
                action_type=SessionToolAction,
                observation_type=SessionToolObservation,
                executor=_BridgeExecutor(invoker),
            )
        ]


def bound_tool_class(tool_name: str, invoker: SessionToolInvoker) -> type[BoundSessionTool]:
    """为**一个**工具名造一个独有类（类名派生自工具名，`name` 显式锚定）。

    为什么要按名分：SDK 的 `ToolDefinition.name` 缺省由**类名**派生 —— 一个进程里若有
    两次装配各用一个工具名，共用同一个类会让两次会话看到同一个名字（`Duplicate tool
    names found` / 名字串台）。类名只用于**诊断可读性**，语义名始终是显式锚定的 `name`。

    类名与 `__qualname__` 都显式给（SDK 会枚举 `Action` 的具体子类构建判别联合，
    `<locals>` 限定名会毒化同进程后续事件 round-trip —— 见 `tests/e2e/live_run_support.py`
    记录的同族教训）。
    """
    class_name = "Bound" + "".join(part.title() for part in tool_name.replace(".", "_").split("_"))
    return type(
        class_name,
        (BoundSessionTool,),
        {
            "name": tool_name,
            "invoker": invoker,
            "__module__": __name__,
            "__qualname__": class_name,
        },
    )


def build_session_tools(
    invokers: Mapping[str, SessionToolInvoker],
) -> Callable[[Sequence[str]], None]:
    """按「工具名 → 调用桥」构造实现表，并返回可注入的**注册函数**。

    返回的注册函数接 `AdapterDependencies.register_tools`：会话装配时按当次真正用到的
    名字把对应实现注册进进程级 registry（**幂等**——同名重复注册只是覆盖同一解析器）。

    **只注册表里的名字**：表外的名字不在这里处理，交给 SDK 按既有语义点名
    「未注册」——那正是「声明了绑定但装配方没有实现」的失败形态，与
    「provider id 未绑定」共用同一条可观测路径（都点名字，不静默丢工具）。
    """
    impls = {
        tool_name: bound_tool_class(tool_name, invoker) for tool_name, invoker in invokers.items()
    }

    def _register(tool_ids: Sequence[str]) -> None:
        for tool_id in tool_ids:
            factory = impls.get(tool_id)
            if factory is None:
                continue
            register_tool(tool_id, factory)

    return _register


__all__ = [
    "BoundSessionTool",
    "SessionToolAction",
    "SessionToolObservation",
    "SessionToolInvoker",
    "bound_tool_class",
    "build_session_tools",
]
