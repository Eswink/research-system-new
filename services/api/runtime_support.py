"""Agent runtime 选择面（组合层；GOAL-20260919-007 / EC-01 / PLAN-20260919-107）。

背景：两个组合根（`services/api/composition.py` 与 `services/api/pg_composition.py`）
此前各自硬编码 `FakeAgentRuntime(structured_output=demo_session_output())`，而
`packages/domain/manifest.py` 的 docstring 却声称「runtime 装配由 OpenHandsRuntimeAdapter
决定」——声明与事实不符。本模块把这条落差收敛成**一个选择点**：两个组合根都经
`build_agent_runtime()` 取 runtime。

边界（写死，勿漂移）：

- **默认 runtime 保持 Fake**（CI 与离线开发不依赖网络）；选择真实 runtime 必须
  **显式配置**，未知取值 **fail-closed 报错**、不静默回退（静默回退会让「我配了真实
  runtime」与「我跑的是 demo」不可区分，正是 AGENTS.md §4 要消灭的漂移）。
- **取值词表归组合层**：`packages/application/ports/*.py` 有字符串门禁
  （`test_provider_types_do_not_leak_from_ports` 禁止 `openhands` / `openai` 等 token），
  因此词表**不得**放进 ports 或 domain；Domain 只存中性标识字符串。
- **本模块的构造是纯装配**：`OpenHandsRuntimeAdapter.__init__` 只存依赖，不发任何
  出站调用（出网门链与放行语义属 EC-02；离线全链属 EC-03）。
- **默认 deny 不放松**：workspace 构造器保持 `build_local_workspace` 的
  `allow_host_shell=False` 默认（AGENTS.md §9），即真实 runtime 可被装配、
  但会话创建仍受 host shell deny 约束。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adapters.fakes.agent_runtime import FakeAgentRuntime
from packages.application.ports.agent_runtime import AgentRuntime
from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.policy_evaluator import PolicyEvaluator
from services.api.demo import demo_session_output
from services.api.settings import ApiSettings

#: 受控 demo 执行体（默认）。
FAKE_RUNTIME = "fake"
#: 真实 Agent runtime（OpenHands SDK adapter）。
OPENHANDS_RUNTIME = "openhands"
#: 合法取值（顺序即错误信息里的枚举顺序）。
RUNTIME_KINDS = (FAKE_RUNTIME, OPENHANDS_RUNTIME)


class RuntimeConfigurationError(ValueError):
    """runtime 配置非法；装配期 fail-closed，不回退默认值。"""


@dataclass(frozen=True, slots=True)
class RuntimeSelection:
    """选择结果（可判事实；进 manifest `execution_backend` 与读面）。"""

    kind: str
    #: True = 操作者显式配置了取值；False = 用了默认 Fake。
    #: 读面用它区分「默认」与「显式选了 Fake」——两者都是 Fake，但披露口径不同。
    configured: bool

    @property
    def substrate(self) -> str:
        """写进 `RunManifest.execution_backend` 的中性标识（opaque string）。"""
        return self.kind

    def fingerprint_record(self) -> dict[str, object]:
        """AGENTS.md §4 运行时指纹槽位的**诚实状态记录**。

        §4 要的七件事实（ModelDefinition / endpoint 配置摘要 / 返回的 model 名 /
        系统指纹 / 白名单响应头 / probe 套件版本 / 兼容性结论）来自一次真实探测。
        默认的受控 demo 执行体**不发起任何模型调用**，因此这七件事实一件也不存在
        ——诚实做法是**显式标注未验证**，不是留空冒充已验证（留空会让读面分不清
        「没探」与「探了但没问题」）。

        选择真实 runtime 时这里同样先记 `NOT_VERIFIED`：真实事实由出网门链与
        离线全链（EC-02 / EC-03）在拿到 probe 结果后替换，替换前不得宣称已验证。
        """
        return {
            "substrate": self.kind,
            "status": "NOT_VERIFIED",
            "reason": (
                "no model probe was run for this run: the controlled demo runtime makes no "
                "model call, so none of the AGENTS.md section 4 facts exist"
                if self.kind == FAKE_RUNTIME
                else "runtime selected but no model probe fact was collected for this run"
            ),
        }


def resolve_runtime_selection(settings: ApiSettings) -> RuntimeSelection:
    """从配置解析选择结果；未知取值 fail-closed。"""
    raw = settings.agent_runtime
    kind = (raw or "").strip().lower()
    if not kind:
        return RuntimeSelection(kind=FAKE_RUNTIME, configured=False)
    if kind not in RUNTIME_KINDS:
        raise RuntimeConfigurationError(
            f"unknown agent runtime {raw!r}: expected one of {', '.join(RUNTIME_KINDS)}"
        )
    return RuntimeSelection(kind=kind, configured=True)


def _fake_runtime() -> AgentRuntime:
    """受控 demo 执行体（与接线前逐字节一致：同一 `demo_session_output()`）。"""
    return FakeAgentRuntime(structured_output=demo_session_output())


def _openhands_runtime(
    *,
    credentials: CredentialResolver | None,
    policy_evaluator: PolicyEvaluator | None,
    budget_ledger: Any | None,
) -> AgentRuntime:
    """真实 adapter 装配（只构造，不出网）。

    缺凭据解析面或缺 policy 求值面时**点名拒绝**——真实 runtime 需要这两件事实才能
    受策略门禁约束（AGENTS.md §5：不得绕过 Policy Wrapper），缺一不可。
    """
    from adapters.openhands.llm_factory import build_llm
    from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
    from adapters.openhands.session_types import AdapterDependencies
    from adapters.openhands.workspace_adapter import build_local_workspace

    missing = [
        name
        for name, present in (
            ("credential_resolver", credentials is not None),
            ("policy_evaluator", policy_evaluator is not None),
        )
        if not present
    ]
    if missing:
        raise RuntimeConfigurationError(
            "agent runtime 'openhands' requires " + " and ".join(missing)
        )
    deps = AdapterDependencies(
        credential_resolver=credentials,
        policy_evaluator=policy_evaluator,
        build_llm=build_llm,
        # 默认 deny 保持：allow_host_shell 不打开（AGENTS.md §9）。
        build_workspace=build_local_workspace,
        budget_ledger=budget_ledger,
    )
    return OpenHandsRuntimeAdapter(deps)


def build_agent_runtime(
    settings: ApiSettings,
    *,
    selection: RuntimeSelection | None = None,
    credentials: CredentialResolver | None = None,
    policy_evaluator: PolicyEvaluator | None = None,
    budget_ledger: Any | None = None,
) -> AgentRuntime:
    """按选择结果装配 AgentRuntime（两个组合根的唯一装配入口）。

    `selection` 允许调用方传入已经解析过的结果——组合根解析一次、装配与披露共用
    同一个对象（避免"装配用的是 A、读面写的是 B"这类不可见的漂移）。
    """
    resolved = selection if selection is not None else resolve_runtime_selection(settings)
    if resolved.kind == FAKE_RUNTIME:
        return _fake_runtime()
    return _openhands_runtime(
        credentials=credentials,
        policy_evaluator=policy_evaluator,
        budget_ledger=budget_ledger,
    )


__all__ = [
    "FAKE_RUNTIME",
    "OPENHANDS_RUNTIME",
    "RUNTIME_KINDS",
    "RuntimeConfigurationError",
    "RuntimeSelection",
    "build_agent_runtime",
    "resolve_runtime_selection",
]
