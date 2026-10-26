"""运行链**检索**能力的产品装配（GOAL-20261026-097 EC-02 的前置：让检索真的发生）。

**它补哪一格**（本轮建档实测）：`capability_execution: run_chain` 的相由
`execute_run_chain_capabilities(deps.capabilities, …)` 执行，而两个产品组合根都**没有**
传 `capabilities=`（`rg "run_chain" services/` 零命中）⇒ 该步收到 `None` ⇒ 返回空
`CapabilityStepOutcome`：**没有证据、没有失败、会话照常继续**。后果是 `retrieval_report`
的覆盖三维（含 `minimum_tool_evidences: 1`）必然判拒，而**判词落在下游的验收门上**，
不是落在「检索没接」这个真实原因上。

**为什么是这两个 provider**：`europe_pmc` / `ncbi_eutils` 是**产品上真的能打的** REST
实现（`adapters/research_tools/`），两者都在 `tool_providers.yaml` 里声明了
`network_domains`（出口白名单的权威声明），且 `literature.search` / `literature.read`
在 `policy.yaml` 里已有 `approved_tool_providers` 放行。本模块**不新增** provider、
**不新增**依赖、**不新增**放行规则。

**三条纪律**：

1. **零出网**：构造 provider 不发请求（`httpx.Client` 只在 `execute` 时用）；
   `health_check` 才会触网，而那是预检的既有行为（`probe_provider_spec`）。
2. **`spill_threshold_bytes=1`**：运行链证据要求**内容在场**（准入会重算 digest），
   默认 32KiB 阈值会让小响应不落盘 ⇒ 证据准入 fail closed。
3. **`None` 不是错误**：目录里没有这两个 provider 的声明 / 没有任何调用声明 ⇒ 返回
   `None`（该能力步不启用，与既有缺省逐字相同）。失败留给合约的覆盖判据判。
"""

from __future__ import annotations

from typing import Any

#: 出厂检索 provider 的 id（与 `examples/config/tool_providers.yaml` 逐字一致）。
EUROPE_PMC_ID = "europe_pmc"
NCBI_ID = "ncbi_eutils"

#: provider 侧的 tool id（**不是**能力名：能力名 `literature.search` 是策略名空间）。
EUROPE_PMC_SEARCH_TOOL = "literature_search"
EUROPE_PMC_READ_TOOL = "literature_read"
NCBI_SEARCH_TOOL = "literature_search"
NCBI_READ_TOOL = "literature_read"

#: 出厂检索的运行链归属于**哪一个相**（出厂协议里跑检索的那一相都叫这个名字：
#: `direction_to_question_v1` / `direction_to_report_v1` / `direction_to_report_v2` /
#: `research_report_chain_v1` 的检索格都是 `retrieval`）。**如实边界**：一个把检索格
#: 取名成别的 id 的协议，本出厂面**不会**在它那里执行检索（`planned_in_this_phase`
#: 按 phase 归属过滤）—— 那条路属「按协议解析调用归属」，本轮不做。
RETRIEVAL_PHASE = "retrieval"

#: 检索词的点分路径：上游 `research_question` 产物的 `query` 字段
#: （`input_material` 把跨相产物的内层对象挂在**产物名**下）。
QUERY_PATH = ("research_question.query",)


def retrieval_providers(*, artifacts: Any, credentials: Any) -> dict[str, Any]:
    """出厂检索 provider 实例（**构造期零出网**；健康探测才触网）。

    只造 `europe_pmc`：`ncbi_eutils` 的 E-utilities 端点在国内网络下常不可达，而
    两个都造会让预检对同一个不可达 host 反复探测。**取舍写明**：`ncbi_eutils` 的声明
    仍在目录里、仍可被别的装配方接（`tests/` 就是这么用的），本出厂面只接一条真能打的。
    """
    from adapters.research_tools.europe_pmc import EuropePmcConfig, EuropePmcProvider

    return {
        EUROPE_PMC_ID: EuropePmcProvider(
            artifacts,
            config=EuropePmcConfig(min_request_interval_seconds=0.0),
            # 运行链证据的准入会重算 digest ⇒ 任何大小的结果都必须落盘。
            spill_threshold_bytes=1,
        )
    }


def retrieval_calls() -> tuple[Any, ...]:
    """出厂检索的两步链：检索（query 来自上游问题）→ 读取（ids 来自上一步结果）。

    与 `tests/e2e/literature_chain_support.europepmc_calls()` **同形**（那是判据侧对同一
    机制的第二份取证；两份都由各自的判据钉住 —— 本函数是**产品**声明，那一份是**判据**
    声明，不许一边改了另一边静默跟随）。
    """
    from packages.application.run_orchestration.phase_capabilities import RunChainCall

    return (
        RunChainCall(
            provider_id=EUROPE_PMC_ID,
            tool_id=EUROPE_PMC_SEARCH_TOOL,
            capability="literature.search",
            arguments_from_input=QUERY_PATH,
            fixed_arguments={"retmax": 3},
            # **必须**标 phase：不标 ⇒ 每条调用在该 run 的**每一个** run_chain 相都会执行
            # （`planned_in_this_phase` 对 `phase_id is None` 一律返回 True）⇒ 问题相在
            # 上游产物还不存在时就去取 `research_question.query`，run 在检索前就失败。
            phase_id=RETRIEVAL_PHASE,
        ),
        RunChainCall(
            provider_id=EUROPE_PMC_ID,
            tool_id=EUROPE_PMC_READ_TOOL,
            capability="literature.read",
            ids_from_previous="ids",
            phase_id=RETRIEVAL_PHASE,
        ),
    )


__all__ = [
    "EUROPE_PMC_ID",
    "NCBI_ID",
    "QUERY_PATH",
    "retrieval_calls",
    "retrieval_providers",
]
