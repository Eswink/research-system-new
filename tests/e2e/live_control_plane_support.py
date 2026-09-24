"""`real_control_plane` 类 live 判据的装配支持：**产品组合根 + 执行体缝**。

与 `live_run_support.py` 的区别只有一个，但它是这个 GOAL 的全部要点：

- `live_run_support.openhands_deps` 走的是 **`preflight_override`**（run-ready 夹具给出
  目录与 `provider_health`），那是 GOAL-009…013 全部真实 run 的同一条路径；
- 本模块走**产品组合根**（`services.api.composition.assemble`），`preflight_override`
  **必须为 `None`** ⇒ policy 求值器、endpoint / provider 健康、URL 裁决、预算预留全部由
  `_live_preflight` 在同一份合并目录上**现场**求值。

**只注入执行体，绝不注入判词**（这是本模块的纪律边界）：

- ✅ 注入 provider **实例**（`NcbiEutilsProvider`，真传输）——`ApiDeps.tool_providers`
  这段缝的用途就是注册实例；空着时 `build_provider_health` 对 REST provider 诚实判
  `UNKNOWN`（既有注释写死了这一行为）。注入实例后健康是**真探测**出来的结果。
- ✅ 注入运行链能力步装配（`CapabilityDeps`：谁来执行本 phase 的 run-chain 能力）。
- ❌ **不**注入 `provider_health` / `endpoint_health` / `policy_evaluator` / 任何
  `PreflightContext` 字段——那些是判词，注入它们就等于换一套控制面（那正是
  `preflight_override` 做的事，本 GOAL 的判据不得那么做）。

产品组合根今天**不**自己接这两段缝（`tool_providers` 生产为空、`OrchestrationDependencies`
的 `capabilities` / `experiment_task` 缺省 `None`）——这是如实登记的缺口，见
`GOAL-20260924-014` 的 `F-10`；本模块用装配方身份补上，**不改产品代码**。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from tests.e2e.live_run_support import _retrieval_calls  # 复用既有声明，不新造第二份

#: 目录里那条 REST provider（`examples/config/tool_providers.yaml`）
PROVIDER_ID = "ncbi_eutils"
#: 目录里声明的真实端点（凭据引用 `LLM_MAIN_KEY`，值只在 gitignored `.env` 里）
ENDPOINT_ID = "agnes-anthropic"


def product_control_plane_deps(db_path: str) -> Any:
    """产品组合根装配 + 两段**执行体**缝；`preflight_override` 必须为 `None`。"""
    from adapters.research_tools import NcbiEutilsProvider
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.catalog_merge import merged_catalog_snapshot
    from services.api.composition import assemble
    from services.api.settings import ApiSettings

    deps = assemble(ApiSettings(db_path=db_path))
    assert deps.preflight_override is None, "本支持模块只用于无 override 的产品装配"
    provider = NcbiEutilsProvider(
        deps.artifacts,
        credentials=deps.credentials,
        spill_threshold_bytes=1,  # 运行链证据要求内容在场（既有口径）
    )
    deps.tool_providers = {PROVIDER_ID: provider}
    spec = merged_catalog_snapshot(deps).tool_providers[PROVIDER_ID]
    inner = deps.runs._deps
    deps.runs = RunOrchestrationService(
        replace(inner, capabilities=capability_step(deps, provider, spec))
    )
    return deps


def capability_step(deps: Any, provider: Any, spec: Any) -> Any:
    """运行链能力步装配（谁执行 + 用哪个求值器 + 账本/制品店；都是装配方事实）。"""
    from packages.application.run_orchestration.phase_capabilities import CapabilityDeps

    assert deps.policy_evaluator is not None, "产品组合根必须接上 policy 求值器"
    return CapabilityDeps(
        calls=_retrieval_calls(),
        providers={PROVIDER_ID: provider},
        provider_specs={PROVIDER_ID: spec},
        policy=deps.policy_evaluator,
        artifacts=deps.artifacts,
        ledger=deps.ledger,
    )
