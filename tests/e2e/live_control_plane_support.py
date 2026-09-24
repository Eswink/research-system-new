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
- ✅ 注入沙箱实验执行体（`with_contract_declared_experiment`：脚本/镜像仍取**合约自己**
  的声明，只是把「谁来执行」接到既有 `DockerExecutionBackend`；见该函数 docstring）。
- ❌ **不**注入 `provider_health` / `endpoint_health` / `policy_evaluator` / 任何
  `PreflightContext` 字段——那些是判词，注入它们就等于换一套控制面（那正是
  `preflight_override` 做的事，本 GOAL 的判据不得那么做）。

产品组合根今天**不**自己接这三段缝（`tool_providers` 生产为空、`OrchestrationDependencies`
的 `capabilities` / `experiment_task` 缺省 `None`）——这是如实登记的缺口，见
`GOAL-20260924-014` 的 `F-10`；本模块用装配方身份补上，**不改产品代码**（装配方补执行体
是本 GOAL 认下的处置；`output_schema_validator` 另说：它在 cycle 6 由应用层给出**缺省**
实现，产品路径本来就带，不算缝）。
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
    assert deps.artifacts is not None, "产品组合根必须给出制品店（运行链证据要内容寻址）"
    assert deps.runs is not None, "产品组合根必须给出编排服务"
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


def with_contract_declared_experiment(deps: Any, *, script: str, image: str) -> None:
    """接上**第三段**执行体缝：合约声明的沙箱实验（GOAL-014 EC-02）。

    与 `live_run_support.with_sandbox_experiment` 的分工**是本质的**：那条路要走
    `declare_sandbox_experiment`，即**改写本次 run 的目录快照**（`preflight_override`）
    ——EC-02 明文禁止的东西。本函数**只接执行体**：

    * 「本任务由沙箱实验执行」这条声明来自**出厂目录**
      （`examples/contracts/task_contracts.yaml` 的 `experiment_execution`；它的
      `experiment: {}` = 声明已给出、脚本由装配上下文决定，见 `ExperimentExecutionSpec`）；
    * 装配方给出的只有**脚本与镜像**（谁去干）与既有 `DockerExecutionBackend`；
    * 契约自己 pin 了的量（`m12_experiment_execution` 的脚本/镜像/命令）不在此被覆盖——
      本函数只服务「合约不 pin、由装配上下文给」的那一份出厂合约。

    产品组合根今天**不**自己接这段缝（`OrchestrationDependencies.experiment_task` 缺省
    `None`）——这是 `F-10` 如实登记的缺口；本函数以装配方身份补上，**不改产品代码**。
    """
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from services.api.experiment_support import (
        docker_experiment_assembly,
        sandbox_experiment_runner,
    )

    policy_evaluator = policy_bindings().get("policy_evaluator")
    assert policy_evaluator is not None, "policy.yaml must be loadable for the sandbox experiment"
    runner = sandbox_experiment_runner(
        docker_experiment_assembly(
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            policy=policy_evaluator,
            script=script,
            image=image,
            experiment_store=deps.experiment_store,
        )
    )
    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(replace(old._deps, experiment_task=runner))
