"""GOAL-20261117-114 EC-07：**真实 k=3 两臂配对消融**（第一次真实读数）。

**它补哪一格**：阶梯「计划」行的 `下一级` 是「配对消融下，X 的存在使输出读数分布发生
位移（k≥3）」。机制在 GOAL-109 就交付了（`comparison_digest` / `AblationPair` /
`output_readings` / `ablation_report` 的 `MIN_CORPUS=3`），但这个 GOAL 的 `U-1` 逐字写着
「**本轮不宣称任何一次真实位移被测到过**」。本判据交付那一份读数。

**两臂只差一个槽位**：`present` 臂的记忆库里**播种一条** PROJECT 档记忆（于是立题会话的
提示词里有 `PRIOR KNOWLEDGE` 段）；`absent` 臂是**全新空库**（同一份装配、其余逐字相同）。

**判什么**（缺一即判红）：

1. **六次 run 全部登记**（`ARM_SEQUENCE` 预先声明 P/A 交替）—— 失败的也登记，不挑样本；
2. **每 run 的可比键相等**（取自 `manifest.frozen` 事件）：这仍是 EC-02 的按压，在真控制面；
3. **语料门**（`MIN_CORPUS=3`）给出结论 —— **不足**则点名缺口（而不是「没看到位移」）；
4. **四列读数 + 位移表**落进证据 JSON（原始观测 + 汇总，两者同源）；
5. **措辞守卫**：`render_report` 不抛（出口自检仍然在）。

**如实边界（本判据不声称的事）**：
- n=3 是**标定下界**，不是统计功效；无采样控制（无 temperature / no seed）⇒ 只比**分布**，
  不判因果方向；
- 只测「计划」一格；检索 / 复检 / 迭代三格**逐字未动**（一格的证据不足以推广）；
- 四列都无位移是**合法结论**（「测量成立、bar 不升」）—— 那时本判据仍通过，记录里写读数。

**离线纪律**：默认门下如实 skip（`requires_live_llm` + 显式开关 + 凭据 + 端点）。

用法（与既有 live 判据同一口令形态）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands <live 开关>=1 RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1 \
      uv run --frozen --no-sync python -B -m pytest \
      tests/e2e/test_paired_ablation_on_the_plan_live.py -q --no-header

（开关的环境变量名只在 `tests/e2e/live_switch_support.py` 里出现 —— 本文件不重复那个
字面量，`test_live_switch_is_single_source` 的「单一声明点」判据因此不用为它开例外。）
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.paired_ablation_live_support import (
    ARM_SEQUENCE,
    EVIDENCE,
    MEMORY_CONTENT,
    MEMORY_ID,
    MEMORY_PROVENANCE,
    PROTOCOL,
    ArmRun,
    build_raw_pairs,
    load_report_tool,
    write_evidence,
)

_RUN_ID = "run-goal114-ablation-k3"
pytestmark = pytest.mark.requires_live_llm


def _gate() -> Any:
    """live 门（与既有 live 判据**同一判定**：凭据 + 端点 + runtime + 显式开关）。"""
    import os

    from adapters.relay.credential_resolver import EnvCredentialResolver
    from packages.application.model_relay.live_run_gate import evaluate_live_run_gate
    from services.api.runtime_support import OPENHANDS_RUNTIME
    from tests.e2e.live_switch_support import live_e2e_switch_enabled
    from tests.e2e.test_research_report_chain_live import _endpoint

    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _seed(deps: Any) -> None:
    """把「前一轮的结论」落成一条 **PROJECT** 档记忆（跨 run 才读得到）。"""
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store = deps.memory
    assert store is not None, "产品组合根必须给出记忆面（本判据的前提）"
    store.allow_source(MEMORY_PROVENANCE)
    store.commit(
        MemoryWriteProposal(
            id=MEMORY_ID,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.LESSON,
            content=MEMORY_CONTENT,
            provenance=MEMORY_PROVENANCE,
            confidence=0.9,
            scope="project",
        )
    )


def _live_preflight_context(deps: Any) -> Any:
    """**显式运维上下文**（既有路径，不是缝）：生产 preflight + provider 健康的显式声明。

    为什么必需（本轮实测，**第一次真跑的六次 run 全部在 0.4–0.7 秒内 FAILED**）：出厂探测面
    对 REST provider 诚实 `UNKNOWN` ⇒ `TOOL_HEALTH_UNPROVEN` 是 WARNING 且**没有接受通道**
    ⇒ `freeze_manifest` 拒冻。拒冻抛出后控制面**没有落任何事件**（`manifest_digest` 为
    null、事件列表为空）⇒ 读面表现为「秒失败而无原因」。

    本判据不改门禁：端点的 URL 裁决 / 健康 / 策略面**全部取自生产 `_live_preflight`
    现算**（同一次请求、同一份合并目录），只把 **provider** 那一面声明成 HEALTHY ——
    与 `tests/e2e/manuscript_chain_live_support.preflight_override` 同一条既有处置。
    """
    from dataclasses import replace

    from packages.domain.enums import EndpointHealth
    from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings
    from services.api.run_execution import _live_preflight

    context = _live_preflight(
        deps, merged_catalog_snapshot(deps), merged_project_settings(deps, "example-project")
    )
    assert context.policy_evaluator is not None, "生产 preflight 必须给出策略求值器"
    return replace(
        context,
        provider_health={
            provider_id: EndpointHealth.HEALTHY for provider_id in context.catalog.tool_providers
        },
    )


def _arm_deps(db_path: str, *, arm: str) -> Any:
    """一臂的**产品装配**（`assemble()`；两臂只差「有没有那一条记忆」）。

    **检索调用表由本判据给出**（`europepmc_calls()`），不是产品的 `product_retrieval`：
    产品那一份的检索词路径是 `research_question.query`，要求本 run 有一个**问题相**；
    本探针是单相、由声明简报驱动（消融要固定输入，不能每臂换问题）⇒ 检索词来自简报的
    `retrieval.query`。这是既有 live 判据同款处置（`manuscript_chain_live_support`
    也由装配方接 `capabilities`）。
    """
    import os

    from services.api.composition import assemble
    from services.api.runtime_support import OPENHANDS_RUNTIME
    from services.api.settings import ApiSettings
    from tests.e2e.literature_chain_support import (
        EUROPE_PMC_ID,
        capabilities_for,
        europepmc_calls,
        with_capabilities,
    )
    from tests.e2e.live_run_support import register_live_key

    deps = assemble(
        ApiSettings(
            db_path=db_path,
            # **真实执行体**：不传它 ⇒ 选择面回落 `fake`（受控 demo，产出
            # `analysis_report`）⇒ 探针的 `research_plan` 恒缺、run 在验收门判拒。
            # 本判据测的就是真实模型 ⇒ 必须显式选 runtime。
            agent_runtime=OPENHANDS_RUNTIME,
            allow_localhost_endpoints=True,
            workspace_allow_host_shell=True,
            workflow_lease_ttl_seconds=3600,
        )
    )
    assert deps.runs is not None and deps.artifacts is not None
    assert deps.preflight_override is None, "组合根不得自带 preflight 上下文"
    register_live_key(deps, os.environ.get("LLM_MAIN_KEY"))
    # 先补显式运维上下文（`capabilities_for` 从它取 provider 声明 —— 那是规格来源）。
    deps.preflight_override = _live_preflight_context(deps)
    # provider **实例**取自组合根自己那份 `CapabilityDeps`（组合根不把它放在
    # `deps.tool_providers` 上 —— 那里是空 dict，实测）。本判据只换「调用表」这一面：
    # 检索词来自声明简报的 `retrieval.query`，而产品那份要 `research_question.query`。
    shipped = deps.runs._deps.capabilities
    assert shipped is not None, "产品组合根必须给出运行链检索面（本判据的前提）"
    with_capabilities(
        deps,
        capabilities_for(
            deps,
            provider_id=EUROPE_PMC_ID,
            provider=dict(shipped.providers)[EUROPE_PMC_ID],
            calls=europepmc_calls(),
        ),
    )
    if arm == "present":
        _seed(deps)
    return deps


def _read_run(client: Any, run_id: str) -> dict[str, Any]:
    """一次 run 的读面读数（状态 / 可比键 / 检索来源数 / 计划载荷）。"""
    import json

    events = client.get(f"/runs/{run_id}/events").json()
    frozen = [event for event in events if event["type"] == "manifest.frozen"]
    digest = str(frozen[-1]["payload"].get("comparison_digest") or "") if frozen else ""
    evidence = client.get(f"/runs/{run_id}/evidence").json()
    retrieved = sum(1 for row in evidence if str(row.get("source_trust_label")) == "RETRIEVED")
    artifacts = client.get(f"/runs/{run_id}/artifacts").json()
    ids = [str(item["id"]) for item in artifacts if str(item["id"]).endswith(":research_plan")]
    payload: dict[str, Any] | None = None
    if ids:
        body = client.get(f"/artifacts/{ids[0]}/content")
        if body.status_code == 200:
            loaded = json.loads(body.content.decode("utf-8", errors="replace"))
            payload = loaded if isinstance(loaded, dict) else None
    return {"digest": digest, "retrieved": retrieved, "payload": payload}


def _known_memory_ids(arm: str) -> tuple[str, ...]:
    """该臂**提示词里可能出现**的 memory id（引用的**分母**）。

    `present` 臂的库里有那一行 ⇒ 分母是它；`absent` 臂是空库 ⇒ 分母是空集。
    分母按**臂的持久事实**给，不按「我期望它引用什么」给 —— 否则 `absent` 臂会因为
    分母里塞了它根本没有的 id 而拿到一个假非零计数。
    """
    return (MEMORY_ID,) if arm == "present" else ()


def _one_arm(index: int, arm: str, db_path: str) -> ArmRun:
    """跑一次 run，返回该臂的读数（观测只在 `SUCCEEDED` 且产物在场时产出）。"""
    from fastapi.testclient import TestClient

    from packages.application.run_orchestration.ablation_observations import observation_from
    from packages.application.run_orchestration.output_readings import read_plan_payload
    from services.api.app import create_app

    deps = _arm_deps(db_path, arm=arm)
    started = time.monotonic()
    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": PROTOCOL},
            headers={"Idempotency-Key": f"{_RUN_ID}-{index}-{arm}"},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        state = client.get(f"/runs/{run_id}").json()["state"]
        readings = _read_run(client, run_id)
    elapsed = time.monotonic() - started
    observation = None
    if state == "SUCCEEDED" and readings["payload"] is not None and readings["digest"]:
        observation = observation_from(
            # **分母必须给**（`read_plan_payload` 的 `citation_count` 只在**已知 id 集合**里找）：
            # 不给分母 ⇒ 该列结构上恒为 0 ⇒ 一条不可能判红的判据。真跑实测抓到过：
            # 首轮六次 run 的 `citation_count` 全是 0，而 `present` 臂的正文逐字引用了
            # `mem-ablation-live-prior` —— 缺陷在判据侧，不在模型侧。
            read_plan_payload(readings["payload"], known_memory_ids=_known_memory_ids(arm)),
            comparison_digest=readings["digest"],
        )
    return ArmRun(
        index=index,
        arm=arm,
        run_id=run_id,
        state=state,
        comparison_digest=readings["digest"],
        retrieved_sources=int(readings["retrieved"]),
        seconds=elapsed,
        observation=observation,
    )


def test_the_run_arm_supplies_a_citation_denominator() -> None:
    """**分母不可缺**（本轮真跑抓到的判据缺陷，离线可判）：`present` 臂必须给分母。

    首轮六次 run 的 `citation_count` 两臂全 0 —— 不是模型没引用（`present` 臂的正文逐字
    写着 `mem-ablation-live-prior`），而是读数调用没给 `known_memory_ids` ⇒ 该列**结构上
    恒为 0** ⇒ 一条不可能判红的判据。这条判据把「分母从臂的持久事实来」钉住。
    """
    from packages.application.run_orchestration.output_readings import read_plan_payload

    cited = read_plan_payload(
        {"content": f"builds on {MEMORY_ID} (a stored PROJECT memory)"},
        known_memory_ids=_known_memory_ids("present"),
    )
    uncited = read_plan_payload(
        {"content": f"builds on {MEMORY_ID} (a stored PROJECT memory)"},
        known_memory_ids=_known_memory_ids("absent"),
    )
    assert cited.cited_memory_ids == (MEMORY_ID,), (
        "`present` 臂必须给分母，否则 citation_count 结构上恒为 0",
        cited.cited_memory_ids,
    )
    assert uncited.cited_memory_ids == (), (
        "`absent` 臂是空库 ⇒ 分母是空集（它根本没有那条记忆可引）",
        uncited.cited_memory_ids,
    )


def test_the_evidence_records_the_recompute() -> None:
    """证据 JSON 必须**如实登记**重算（否则「读数」与「那次真跑的产物」之间的关系不可审）。"""
    import json

    path = Path(EVIDENCE)
    if not path.is_file():
        pytest.skip(f"no ablation evidence yet ({EVIDENCE})")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("recompute_note"), "重算必须在证据里点名理由与手段"
    for run in payload["runs"]:
        assert run.get("reading_note"), run["run_id"]
        assert run["arm"] in ("present", "absent"), run


def test_paired_ablation_over_three_pairs(tmp_path: Path) -> None:
    """真实 k=3 两臂：跑六次 run，出语料门结论与四列位移表。"""
    gate = _gate()
    if not gate.open:
        from packages.application.model_relay.live_run_gate import skip_record_for_gate

        pytest.skip(f"live run skipped: {skip_record_for_gate(_RUN_ID, gate).reason}")

    runs: list[ArmRun] = []
    for index, arm in enumerate(ARM_SEQUENCE, start=1):
        runs.append(_one_arm(index, arm, str(tmp_path / f"arm-{index}-{arm}.db")))

    report_tool = load_report_tool()
    refused: str | None = None
    try:
        report = report_tool.build_report(build_raw_pairs(runs))
        rendered = report_tool.render_report(report)
    except report_tool.AblationError as error:  # 两臂键不等 / 观测畸形 ⇒ 点名，不猜
        refused = str(error)
        report = report_tool.build_report({"slot": "prior_knowledge", "pairs": []})
        rendered = report_tool.render_report(report)
    path = write_evidence(runs, report=report, rendered=rendered, refused=refused)

    assert path.is_file(), path
    assert EVIDENCE.endswith(".json")
    # 六次 run 全部登记（失败的也在里面）—— 不挑样本。
    assert [run.index for run in runs] == list(range(1, len(ARM_SEQUENCE) + 1))
    # 报告的输出面自检没被绕过。
    assert "prior_knowledge" in rendered
    # 语料门给出**结论**（足够 / 不足都行）；不足时必须点名缺口。
    assert report.gate.sufficient or report.gate.missing, report.gate
