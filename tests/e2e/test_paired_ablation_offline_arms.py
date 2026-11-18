"""GOAL-20261117-114 EC-06：**两臂在真实装配上配得起来、且观测能过消融门**（离线）。

**它补哪一道缝**：本 GOAL 的 EC-02/03/04 各自在**单元面**成立（键归一化、payload 增键、
四列映射），但没有任何一条判据证明它们在**同一份真实装配**上串起来可用。GOAL-109 的
教训正是这个形态：四个件都在树、七条 EC 全绿，而真实路径上 `AblationPair` 会因为
`accepted_at` 一律拒绝 —— 那一面只有「拿两个真 run 去配」才暴露。

**判什么**（每条都指向一个只有在装配面才出现的形态）：

1. **两臂都能跑完**：`present`（播种一条 PROJECT 档记忆）与 `absent`（空库）各自
   `SUCCEEDED` —— 证明播种没把 run 弄坏、也没依赖记忆才成功；
2. **两 run 的可比键相等**：键取自各自 `manifest.frozen` 事件的 `comparison_digest`
   （**读面回读**，不是现算一份内存里的）——这是 EC-02 在真装配上的按压；
3. **观测量出得来**：两 run 的计划制品经 `read_plan_payload → observation_from` 各得
   一份四列 `int` 观测（`present` 的 `citation_count` 在本文件里**不**要求非零 ——
   离线执行体不读提示词，那是 live 判据的事）；
4. **门接受三对**：把这对观测重复成 3 对喂 `tools/ablation_report.build_report` ⇒
   `gate.sufficient` 真、四列渲染、措辞守卫不抛。

**为什么用引擎自己的 `assemble()`**：`prior_knowledge` 与 `memory_gate` 的接线是
**组合根的决策**（`composition.py:332/336`）。用 `openhands_deps()` 那类 run-ready 夹具
会绕开它们 ⇒ 本判据就测不到「产品组合根接好了」这件事（GOAL-082 之前正是这样漏的）。

**如实边界**：离线执行体（mock 端点）不读提示词 ⇒ 本判据证的是**读数管线**，
不是「记忆改变了模型输出」；后者是 live 判据（EC-07）。
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.application.run_orchestration.ablation_observations import observation_from
from packages.application.run_orchestration.output_readings import read_plan_payload
from services.api.app import create_app
from tests.e2e.literature_chain_support import (
    EUROPE_PMC_ID,
    OfflineEuropePmc,
    capabilities_for,
    europepmc_calls,
    europepmc_run_chain_provider,
    with_capabilities,
)
from tests.e2e.test_ec03_real_runtime_offline_chain import mock_relay

__all__ = ["mock_relay"]

#: 单相消融台（EC-05 交付的协议）；一次 run 只建一个会话。
_PROTOCOL = "ablation_plan_probe_v1.yaml"
_PLAN_CONTRACT = "research_report_plan"
#: 播种的那条记忆（内容与 provenance 都是判据自己的事实，不 import 产品常量）。
_MEMORY_ID = "mem-ablation-seed"
_MEMORY_CONTENT = "Prior round: pin duplicate_pairs before comparing arms."
_MEMORY_PROVENANCE = "run:ablation-prior:claim:result"
#: 出厂目录里 main 端点的凭据引用名（`examples/config/llm_endpoints.yaml` 的 `credential_ref`）。
_CREDENTIAL_REF = "LLM_MAIN_KEY"
#: 离线占位值：**不是**任何可用凭据，只为让「凭据引用可解析」这一项在离线装配上成立。
_OFFLINE_PLACEHOLDER = "offline-placeholder-not-a-credential"


def _register_offline_credential(deps: Any) -> None:
    """给**离线**装配注册一个占位凭据（`CREDENTIAL_MISSING` 是 preflight 的 fail-closed 项）。

    为什么必需：默认门的 conftest 会**删掉**出厂目录声明的凭据键（
    `tests/conftest.py::_default_gate_hides_live_credentials`，防止默认门看见 live 凭据）。
    本判据根本不会真的调模型（会话输出是受控注入的），但 preflight 仍要判「凭据可解析」——
    这一项不是「能不能调通」，是「解析器里有没有这个引用」。

    **不物化任何可用凭据**：值是一个常量占位串，且只注册进**本次装配自己的**解析器。
    """
    from adapters.relay.registry_credential_resolver import RegistryCredentialResolver

    register = getattr(deps.credentials, "register", None)
    if callable(register) and isinstance(deps.credentials, RegistryCredentialResolver):
        register(_CREDENTIAL_REF, _OFFLINE_PLACEHOLDER)


def _preflight_context(deps: Any) -> Any:
    """**显式运维上下文**（既有路径，不是缝）：目录 + 声明的端点/provider 健康。

    为什么必需：出厂探测面对 REST provider 诚实 `UNKNOWN` ⇒ `TOOL_HEALTH_UNPROVEN` 是
    WARNING 且**没有接受通道** ⇒ `freeze_manifest` 拒冻（`real_retrieval_research_v1.yaml`
    已登记这条既有缺口）。本判据不改门禁，走与既有 live 判据**同一条**显式声明路径
    （`tests/e2e/manuscript_chain_live_support.preflight_override` 同一手法）。
    """
    from packages.application.ports.resource_catalog import PreflightContext
    from packages.domain.enums import EndpointHealth
    from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings

    catalog = merged_catalog_snapshot(deps)
    return PreflightContext(
        catalog=catalog,
        project=merged_project_settings(deps, "example-project"),
        # 凭据解析面必须与产品根**同一个实例**（`CREDENTIAL_MISSING` 就是漏了它）。
        credentials=deps.credentials,
        policy_evaluator=deps.policy_evaluator,
        endpoint_health={endpoint_id: EndpointHealth.HEALTHY for endpoint_id in catalog.endpoints},
        provider_health={
            provider_id: EndpointHealth.HEALTHY for provider_id in catalog.tool_providers
        },
    )


def _deps(db_path: str) -> Any:
    """**产品组合根** + 运行链检索缝（检索由运行链执行，不注入判词）。

    调用表由**装配方**给出（`europepmc_calls()`）：产品那一份的检索词路径是
    `research_question.query`，而本探针是单相、由声明简报驱动 ⇒ 检索词从简报的
    `retrieval.query` 来（消融要固定输入，不能每臂换一个问题）。相 id 仍按产品瞄准的
    那个取（见协议注释）—— 这一点由 `test_the_probe_really_retrieves` 按压。

    会话输出由**装配方**注入（`controlled_plan_output()`）：产品缺省的 Fake 执行体只发
    `analysis_report` 这一件事实，而本协议要的是 `research_plan`。**这不是在伪造研究
    结论** —— 离线判据判的是「读数管线」，正文内容是受控常量；真实模型那一面在 live
    判据（EC-07）。
    """
    from services.api.composition import assemble
    from services.api.settings import ApiSettings

    deps = assemble(
        ApiSettings(
            db_path=db_path,
            # 目录里的端点今天指向局域网中转站 ⇒ 默认被判 private 而拒（§9 姿态，正确）。
            # 本判据用的是**离线** mock 端点的等价放行（与既有离线 live 装配同一开关）。
            allow_localhost_endpoints=True,
            workspace_allow_host_shell=True,
        )
    )
    assert deps.runs is not None and deps.artifacts is not None, "组合根必须给出编排服务与制品店"
    assert deps.preflight_override is None, "组合根不得自带 preflight 上下文"
    _register_offline_credential(deps)
    deps.preflight_override = _preflight_context(deps)
    provider = europepmc_run_chain_provider(deps, OfflineEuropePmc(requests=[]))
    with_capabilities(
        deps,
        capabilities_for(
            deps,
            provider_id=EUROPE_PMC_ID,
            provider=provider,
            calls=europepmc_calls(),
        ),
    )
    _install_controlled_output(deps)
    return deps


def controlled_plan_output(*, cited_memory_id: str | None = None) -> dict[str, object]:
    """受控的 `research_plan` 会话输出（两臂**只有引用那一处**可不同）。

    `cited_memory_id` 非空 ⇒ 正文里逐字写上那个 id（这正是两臂唯一的差别：
    `present` 臂的提示词里有那条记忆、输出里因此可以引用它；`absent` 臂没有那一段）。
    设计块逐字相同 —— 消融比较的是**读数分布**，不是让两臂写不同的实验。
    """
    lines = [
        "This study asks whether duplicate-detection cost grows with corpus size.",
        "It rests on the retrieved records listed above.",
    ]
    if cited_memory_id:
        lines.append(f"It builds on {cited_memory_id} (a stored PROJECT memory).")
    lines.append(
        '```experiment_design\n{"experiment_design": {"arms": {"treatment": '
        '{"seed": 17, "n_items": 120}, "control": {"seed": 17}}}}\n```'
    )
    return {"research_plan": {"content": "\n".join(lines)}}


def _install_controlled_output(deps: Any) -> None:
    """把受控会话输出装进 runtime（装配方身份；产品代码零改动）。"""

    from packages.application.run_orchestration.service import RunOrchestrationService
    from tests.e2e.scenario import StructuredOutputAgentRuntime

    inner = deps.runs._deps
    deps.runs = RunOrchestrationService(
        replace(
            inner,
            runtime=StructuredOutputAgentRuntime(
                outputs_by_contract={_PLAN_CONTRACT: controlled_plan_output()}
            ),
        )
    )


def _seed(deps: Any) -> None:
    """把「前一轮的结论」落成一条 **PROJECT** 档记忆（跨 run 才读得到）。"""
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store = deps.memory
    assert store is not None, "产品组合根必须给出记忆面（本判据的前提）"
    store.allow_source(_MEMORY_PROVENANCE)
    store.commit(
        MemoryWriteProposal(
            id=_MEMORY_ID,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.LESSON,
            content=_MEMORY_CONTENT,
            provenance=_MEMORY_PROVENANCE,
            confidence=0.9,
            scope="project",
        )
    )


def _arm_deps(tmp_path: Any, *, seeded: bool) -> Any:
    """一臂的装配：`seeded` 只决定「有没有那一行记忆」，其余逐字相同。"""
    deps = _deps(str(tmp_path / ("present.db" if seeded else "absent.db")))
    if seeded:
        _seed(deps)
    return deps


def _frozen_comparison_digest(client: TestClient, run_id: str) -> str:
    """该 run 的可比键（从 `manifest.frozen` 事件的 payload **回读**，不是现算）。"""
    events = client.get(f"/runs/{run_id}/events").json()
    frozen = [event for event in events if event["type"] == "manifest.frozen"]
    assert frozen, f"run {run_id} 没有 manifest.frozen 事件"
    digest = str(frozen[-1]["payload"].get("comparison_digest") or "")
    assert digest.startswith("sha256:"), ("冻结快照必须带可比键", frozen[-1]["payload"].keys())
    return digest


def _plan_payload(client: TestClient, run_id: str) -> dict[str, Any]:
    """本 run 的计划制品载荷（经既有读面；制品缺席 ⇒ 判据自己点名失败）。"""
    artifacts = client.get(f"/runs/{run_id}/artifacts").json()
    ids = [str(item["id"]) for item in artifacts if str(item["id"]).endswith(":research_plan")]
    assert ids, f"run {run_id} 没有计划制品：{[item['id'] for item in artifacts]}"
    body = client.get(f"/artifacts/{ids[0]}/content")
    assert body.status_code == 200, (ids[0], body.status_code)
    loaded: Any = json.loads(body.content.decode("utf-8", errors="replace"))
    assert isinstance(loaded, dict), loaded
    return loaded


def _run_one(deps: Any, key: str) -> dict[str, Any]:
    """跑一次 run，返回四件读数：状态 / 可比键 / 检索证据数 / 四列观测。"""
    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": key},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        state = client.get(f"/runs/{run_id}").json()["state"]
        digest = _frozen_comparison_digest(client, run_id)
        retrieved = [
            row
            for row in client.get(f"/runs/{run_id}/evidence").json()
            if str(row.get("source_trust_label") or "") == "RETRIEVED"
        ]
        payload = _plan_payload(client, run_id) if state == "SUCCEEDED" else None
    base: dict[str, Any] = {
        "run_id": run_id,
        "state": state,
        "comparison_digest": digest,
        "retrieved_sources": len(retrieved),
        "observation": None,
    }
    if payload is None:
        return base
    readings = read_plan_payload(payload)
    base["observation"] = observation_from(readings, comparison_digest=digest)
    return base


@pytest.fixture
def two_arms(tmp_path: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """两臂各跑一次（`present` 先、`absent` 后；顺序不影响观测）。"""
    present = _run_one(_arm_deps(tmp_path, seeded=True), "goal114-present-1")
    absent = _run_one(_arm_deps(tmp_path, seeded=False), "goal114-absent-1")
    return present, absent


def test_the_probe_really_retrieves(two_arms: tuple[dict[str, Any], dict[str, Any]]) -> None:
    """**探针真的检索了**：两臂都要有 `RETRIEVED` 性质的来源。

    没有这条，相 id 取名错了也照样「跑通」——`planned_in_this_phase` 对不匹配的相静默
    跳过，run 随后在合约的 `minimum_retrieved_sources` 上判拒，归因落在验收门而不是
    「检索没跑」。本判据把「检索这一半真的发生了」钉在探针自己身上。
    """
    for arm in two_arms:
        assert arm["retrieved_sources"] >= 1, (
            "探针相必须真的走运行链检索（`RETRIEVED` 来源 ≥ 1）",
            arm["run_id"],
            arm["retrieved_sources"],
        )


def test_both_arms_succeed_on_the_ablation_probe(
    two_arms: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    """两臂都必须 `SUCCEEDED`（播种不把 run 弄坏，也不依赖记忆才成功）。"""
    present, absent = two_arms
    assert present["state"] == "SUCCEEDED", present
    assert absent["state"] == "SUCCEEDED", absent


def test_the_two_arms_share_one_comparison_digest(
    two_arms: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    """**EC-02 在真装配上的按压**：同一份装配的两次 run 必须配得起来。"""
    present, absent = two_arms
    assert present["comparison_digest"] == absent["comparison_digest"], (
        "两臂的可比键不等 ⇒ 配对消融在真实装配上仍然不可用",
        present["comparison_digest"],
        absent["comparison_digest"],
    )


def test_each_arm_yields_four_int_readings(
    two_arms: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    """每个 run 都量得出四列 `int` 观测（`bool` 会被消融门拒）。"""
    from packages.application.run_orchestration.ablation_observations import READING_KEYS

    for arm in two_arms:
        observation = arm["observation"]
        assert observation is not None, arm
        for key in READING_KEYS:
            assert type(observation[key]) is int, (arm["run_id"], key, observation[key])
        assert observation["design_block"] == 1, (
            "计划里必须写着设计块（合约 purpose 明写它的形状）",
            observation,
        )


def test_the_pair_is_accepted_by_the_ablation_gate(
    two_arms: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    """**闭环**：一对真实观测复制成 k=3 后必须过门（`MIN_CORPUS` + 四列 + 措辞守卫）。"""
    import importlib.util
    import sys
    from pathlib import Path

    from packages.application.run_orchestration.ablation_observations import READING_KEYS

    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "goal114_offline_report", root / "tools" / "ablation_report.py"
    )
    assert spec is not None and spec.loader is not None
    report_tool = importlib.util.module_from_spec(spec)
    sys.modules["goal114_offline_report"] = report_tool
    spec.loader.exec_module(report_tool)

    present, absent = two_arms
    raw = {
        "slot": "prior_knowledge",
        "pairs": [
            {
                "label": f"k{index}",
                "present": present["observation"],
                "absent": absent["observation"],
            }
            for index in range(1, report_tool.MIN_CORPUS + 1)
        ],
    }
    report = report_tool.build_report(raw)
    assert report.gate.sufficient is True, report.gate
    assert [column.field for column in report.shifts] == list(READING_KEYS)
    assert "prior_knowledge" in report_tool.render_report(report)
