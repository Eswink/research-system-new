"""**产品组合根的执行缝**（GOAL-20261026-097 EC-01/EC-02：实验缝 + 报告缝 + 运行链检索缝）。

**它补哪一格**（本轮建档实测）：`OrchestrationDependencies` 早就有 `experiment_task`、
`report_task`、`capabilities` 三道缝，工厂也早已存在 —— 但**只有测试在接**：
`rg "experiment_task|report_task|run_chain" services/api/composition.py` 零命中 ⇒ 缺省
`None` ⇒ 从**产品入口**（真 API）起的 run 走到 `experiment` / `report` 相就以**点名拒绝**
收敛；而 `capability_execution: run_chain` 的相会走 `execute_run_chain_capabilities(None, …)`
⇒ **空步**（没有证据、没有失败、会话照常继续），下游 `minimum_tool_evidences: 1` 因此必拒。

**三条如实边界**：

1. **装配期零 Docker 连接**：实验后端经 `lazy_docker_experiment_assembly` 惰性到手
   （`DockerExecutionBackend.__init__` 就 `docker.from_env()`）。`assemble()` 在默认门的
   `quality-windows-latest` 上必须成功 —— 那段不保证有 Docker。
2. **脚本/镜像按契约声明优先，装配面兜底**（EC-03）。
3. **运行链检索只接**「产品上真的能打的」那两件：`europe_pmc` / `ncbi_eutils`（REST，
   `network_domains` 已声明）。它们的实例同时进 `ApiDeps.tool_providers` —— 否则预检的
   健康探测诚实地收敛为 `UNKNOWN` ⇒ `TOOL_HEALTH_UNPROVEN` **没有接受通道** ⇒ 拒冻。

**本模块不判定任何东西**：只把组合根手里的既有 Port 收成可调用体。
"""

from __future__ import annotations

from typing import Any

#: 组合根兜底脚本（契约**没有** pin 脚本时用它）。选 `exact_match_index_benchmark.py`：
#: 只依赖 stdlib、确定性、产出 `metrics`（`experiment_execution` 的 `ARTIFACT_EXISTS(metrics)`
#: 判的就是它），且是既有 e2e 一直在用的那一个。
DEFAULT_EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
#: 组合根兜底镜像（契约 pin 镜像时用契约的）。
DEFAULT_EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"


def experiment_task_for(  # noqa: PLR0913 - 装配面：Port 就这几件（齐了才叫接上）
    *,
    artifacts: Any,
    policy: Any,
    ledger: Any,
    experiment_store: Any,
    script: str | None = DEFAULT_EXPERIMENT_SCRIPT,
    image: str = DEFAULT_EXPERIMENT_IMAGE,
    design_source: str | None = None,
) -> Any:
    """实验缝：契约声明了 `experiment` 的任务由**既有**沙箱执行链跑（惰性后端）。

    `design_source` 缺省 `None` ⇒ 臂来自装配面（逐字沿用既有语义）；`"plan"` ⇒ 臂从
    **本 run 的计划产物内容**读出。组合根**不猜**：由调用方（`ApiSettings`）声明。
    """
    from services.api.experiment_factories import lazy_docker_experiment_assembly
    from services.api.experiment_support import sandbox_experiment_runner

    return sandbox_experiment_runner(
        lazy_docker_experiment_assembly(
            artifacts=artifacts,
            policy=policy,
            ledger=ledger,
            experiment_store=experiment_store,
            script=script,
            image=image,
            design_source=design_source,
        )
    )


def report_task_for(*, artifacts: Any, ledger: Any, review_findings: Any) -> Any:
    """报告缝：契约声明了 `report` 的任务由**既有**汇编器按持久事实汇出（不建会话）。

    叙述者（`narrator`）**不接**：接它要模型端点 + 凭据引用的解析，属装配方的显式决策
    （`report_support.narrative_runner` 留作另接）⇒ 缺省走**确定性汇编**，与
    `report_task_runner(narrator=None)` 的既有语义逐字一致。
    """
    from services.api.report_support import report_task_runner

    return report_task_runner(artifacts=artifacts, ledger=ledger, review_findings=review_findings)


def sqlite_executor_seams(faces: Any, ports: Any, providers: dict[str, Any]) -> dict[str, Any]:
    """SQLite 组合根的接缝（位置参数形态；`composition.py` 卡在 450 行，接缝收在这里）。

    返回的三个关键字直接展开进 `OrchestrationDependencies(...)`：两道执行缝 +
    运行链检索面（`capabilities`）。
    """
    return {
        "capabilities": product_retrieval(
            artifacts=ports.artifacts,
            ledger=ports.ledger,
            policy=faces.policy_evaluator,
            providers=providers,
        ),
        "experiment_task": experiment_task_for(
            artifacts=ports.artifacts,
            policy=faces.policy_evaluator,
            ledger=ports.ledger,
            experiment_store=ports.experiment_store,
            design_source=faces.settings.experiment_design_source,
        ),
        "report_task": report_task_for(
            artifacts=ports.artifacts,
            ledger=ports.ledger,
            review_findings=ports.review_findings,
        ),
    }


def pg_executor_seams(components: Any, inputs: Any, providers: dict[str, Any]) -> dict[str, Any]:
    """PG 组合根的三道缝（与 SQLite 根**同一份装配决策**，只差 Port 实例）。"""
    effective = inputs.effective
    return {
        "capabilities": product_retrieval(
            artifacts=components["artifacts"],
            ledger=components["ledger"],
            policy=inputs.policy_bindings.get("policy_evaluator"),
            providers=providers,
        ),
        "experiment_task": experiment_task_for(
            artifacts=components["artifacts"],
            policy=inputs.policy_bindings.get("policy_evaluator"),
            ledger=components["ledger"],
            experiment_store=components["experiment_store"],
            design_source=effective.experiment_design_source,
        ),
        "report_task": report_task_for(
            artifacts=components["artifacts"],
            ledger=components["ledger"],
            review_findings=components["review_findings"],
        ),
    }


def retrieval_capabilities(  # noqa: PLR0913 - 装配面：Port 与声明就这几件
    *,
    artifacts: Any,
    ledger: Any,
    policy: Any,
    providers: dict[str, Any],
    provider_specs: dict[str, Any],
    calls: Any,
) -> Any:
    """运行链**检索**能力装配（`CapabilityDeps`）；没有实例或没有调用声明 ⇒ `None`（不启用）。

    `None` 的语义与既有缺省**逐字相同**（那个能力步不执行）。为什么返回 `None` 而不是抛：
    「本目录没有可执行的检索 provider」是**配置事实**，不是错误 —— 该相的 run-chain 面
    因此仍为空步，由合约自己的覆盖判据判（`minimum_tool_evidences` 会拒），
    失败落在**产物面**上而不是装配期。
    """
    if not providers or not calls:
        return None
    from packages.application.run_orchestration.phase_capabilities import CapabilityDeps

    return CapabilityDeps(
        calls=tuple(calls),
        providers=providers,
        provider_specs=provider_specs,
        policy=policy,
        artifacts=artifacts,
        ledger=ledger,
    )


def product_retrieval(  # noqa: PLR0913 - 装配面：Port 与声明就这几件
    *, artifacts: Any, ledger: Any, policy: Any, providers: dict[str, Any]
) -> Any:
    """组合根的运行链检索面（`CapabilityDeps` 或 `None`）：一行接上，实例由调用方持有。

    实例与声明分开取的第二个理由：`ApiDeps.tool_providers` 要的是**同一批实例**
    （预检的健康探测读那一份），所以实例的**持有者**在组合根，本函数只把「声明 +
    声明面 + 调用表」收成执行面。
    """
    from services.api import retrieval_wiring
    from services.api.catalog import load_catalog_snapshot

    declared = load_catalog_snapshot().tool_providers
    return retrieval_capabilities(
        artifacts=artifacts,
        ledger=ledger,
        policy=policy,
        providers=providers,
        provider_specs={key: declared[key] for key in providers if key in declared},
        calls=retrieval_wiring.retrieval_calls(),
    )


def close_providers(providers: dict[str, Any]) -> None:
    """关闭 provider 实例（持有 httpx client 的那个）；无 `close` 的实例跳过。"""
    for provider in providers.values():
        close = getattr(provider, "close", None)
        if callable(close):
            close()


__all__ = [
    "DEFAULT_EXPERIMENT_IMAGE",
    "DEFAULT_EXPERIMENT_SCRIPT",
    "close_providers",
    "experiment_task_for",
    "pg_executor_seams",
    "product_retrieval",
    "report_task_for",
    "retrieval_capabilities",
    "sqlite_executor_seams",
]
