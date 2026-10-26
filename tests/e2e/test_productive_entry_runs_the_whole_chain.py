"""GOAL-20261026-097 EC-02：**从产品入口跑通**七相链（`assemble()` 出来的 deps，不补缝）。

**它补哪一格**（本轮建档实测）：上一轮（GOAL-096）的 live 判据在 `_assembled()` 之后
**手工 `replace(...)`** 补了四道缝（检索能力 / 实验 / 报告 / 被评对象）。那证明的是
「机制成立」，**不**证明「产品入口能用」—— 本轮把缝接进组合根之后，本判据**一律不补缝**：

- 不 `replace(deps.runs._deps, ...)`；
- 不 `deps.tool_providers = {...}`；
- 不调用 `_attach_capabilities` / `_attach_runtime` / `_declare_direction`。

判据在 `assemble()` 之后只做两件**运维上下文**的事（与 GOAL-009/010/096 全部真实 run
相同的一条既有路径，`examples/protocols/real_retrieval_research_v1.yaml:11-19` 有登记）：

1. 注入凭据（`register_live_key`）—— 那是**部署配置**，不是缝；
2. 显式 `preflight_override`（provider 健康 + 目录），因为出厂探测面对 REST provider
   诚实地收敛为 `UNKNOWN` ⇒ `TOOL_HEALTH_UNPROVEN` **没有接受通道** ⇒ 拒冻。
   这是**既有**的语义不一致，本轮不改门禁。

**取证文件**（`.cursor/plans/goals/evidence/GOAL-20261026-097-productive-entry-run.txt`）
写明用的是哪一种入口，并**先写盘再断言**（GOAL-096 `W-1` 的教训：旧写法只在断言前写，
失败路径根本走不到写盘 ⇒ 失败读数不在文件里）。

**默认门**：`evaluate_live_run_gate`（runtime 显式 `openhands` + 凭据可解析 + live 开关）。
缺一 ⇒ **如实 skip**（skip 不是 PASS）。Docker 不可用亦 `requires_docker` skip。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.application.model_relay.live_run_gate import (
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from services.api.app import create_app
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

#: 本轮的取证文件（读数逐条落盘；**失败路径也写**）。
_EVIDENCE = Path(".cursor/plans/goals/evidence/GOAL-20261026-097-productive-entry-run.txt")
#: 本判据跑的是**七相**协议（v2：v1 的六相 + `novelty`）。
_PROTOCOL = "direction_to_report_v2.yaml"
_PROTOCOL_ID = "direction_to_report_v2_0_0"
_DIRECTION = "retrieval augmentation for scientific hypothesis generation"
#: 七相各自的产物（`retrieval_report` 由运行链 + 会话共同产出）。
_PHASE_ARTIFACTS = (
    "research_question",
    "retrieval_report",
    "novelty_claim",
    "research_plan",
    "review_decision",
    "research_report.md",
)


def _write_evidence(entry: str, readings: dict[str, Any]) -> None:
    """读数逐条落盘（**先写再断言**；本轮修的是 GOAL-096 `W-1` 的机制）。"""
    _EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GOAL-20261026-097 EC-02 真跑读数",
        "",
        "入口形态：`TestClient(create_app(assemble(...)))` —— **产品组合根**，"
        "**未**做任何 `replace(deps.runs._deps, ...)` / `deps.tool_providers = ...` "
        "补缝；仅注入部署凭据与显式 `preflight_override`（既有运维路径）。",
        "",
        f"## {entry}",
        "",
    ]
    for key, value in readings.items():
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    _EVIDENCE.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _assembled_product() -> Any:
    """**产品组合根**（`assemble()`）；本函数**不补任何缝**（补了就断言失败）。"""
    from services.api.composition import assemble
    from services.api.runtime_support import OPENHANDS_RUNTIME
    from services.api.settings import ApiSettings

    deps = assemble(
        ApiSettings(
            # 每次一个全新的库（pid 会复用 ⇒ 按 pid 命名会让上一次的 lease 残留进来，
            # 实测表现是 `no matching lease for task` 的 422）。
            db_path=f"data/goal097-live-{os.getpid()}-{started_key()}.db",
            # 真实 runtime：产品根经选择面装配（**不是**测试侧 `replace` 补的）。
            agent_runtime=OPENHANDS_RUNTIME,
            allow_localhost_endpoints=False,
            # 真实会话要能建工作区（§9 的 host shell 默认 deny 不变：这是**显式**开发开关，
            # 与 live e2e 既有做法同一口径）。
            workspace_allow_host_shell=True,
            # 实验设计来自**本 run 的计划产物**（GOAL-080 的机制，装配面声明）。
            experiment_design_source="plan",
            # 任务租约 TTL：同步执行路径只在会话**开始前**心跳一次，而真实会话常超 300 秒
            # ⇒ 租约过期 ⇒ `no matching lease for task`（实测反复出现）。给足预算。
            workflow_lease_ttl_seconds=3600,
        )
    )
    _register_credential(deps)
    runs = deps.runs
    assert runs is not None, "产品根必须产出编排服务"
    inner = runs._deps
    # 产品入口的**结构前提**：三道缝都由组合根给出（补过缝的入口不算产品入口）。
    assert inner.experiment_task is not None, "产品根没接实验缝"
    assert inner.report_task is not None, "产品根没接报告缝"
    assert inner.capabilities is not None, "产品根没接运行链检索面"
    return deps


def _register_credential(deps: Any) -> None:
    """把部署凭据注册进**产品根自己那个**解析器（`RegistryCredentialResolver`）。

    为什么不能复用测试夹具的 `register_live_key`：那个把实例 cast 成
    `FakeCredentialResolver`（`tests/api/run_fixtures` 的形态）；产品根持有的是
    `RegistryCredentialResolver` —— 两者 API 同名但**不是同一个实例**，cast 只是类型谎言。
    值只从环境变量来，本函数不读值、不回显、不落盘。
    """
    value = os.environ.get("LLM_MAIN_KEY")
    if not value:
        return
    register = getattr(deps.credentials, "register", None)
    if callable(register):
        register("LLM_MAIN_KEY", value)


def _preflight_override(deps: Any) -> Any:
    """显式运维上下文：目录 + provider 健康（既有路径，非缝）。

    为什么需要：出厂探测面对 REST provider 诚实 `UNKNOWN` ⇒ `TOOL_HEALTH_UNPROVEN`
    是 WARNING 且**没有接受通道** ⇒ `freeze_manifest` 拒冻
    （`examples/protocols/real_retrieval_research_v1.yaml:11-19` 已登记这条既有缺口）。
    本判据不改门禁，走**显式声明**这条既有路径。
    """
    from packages.application.ports.resource_catalog import PreflightContext
    from packages.domain.enums import EndpointHealth
    from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings

    catalog = merged_catalog_snapshot(deps)
    project = merged_project_settings(deps, "example-project")
    return PreflightContext(
        catalog=catalog,
        project=project,
        # 凭据解析面必须与产品根**同一个实例**（`CREDENTIAL_MISSING` 就是漏了它）。
        credentials=deps.credentials,
        policy_evaluator=deps.policy_evaluator,
        endpoint_health={endpoint_id: EndpointHealth.HEALTHY for endpoint_id in catalog.endpoints},
        provider_health={
            provider_id: EndpointHealth.HEALTHY for provider_id in catalog.tool_providers
        },
    )


def started_key() -> str:
    """一次性的幂等键（同进程内多次起 run 不互相顶掉）。"""
    import uuid

    return uuid.uuid4().hex[:12]


def _collect_novelty(deps: Any, chain: dict[str, Any], readings: dict[str, Any]) -> None:
    """创新点两面在**这次真跑**里的读数：命中的真实标识 + 引用它的判词条数。

    - **声明面**：`novelty_claim_of_run` 从 canonical 读出声明并判「`nearest_prior` 命中本 run
      检索到的标识」（与门判据**同一个**函数，不是另一套解析）。
    - **评审面**：判词正文里**逐字**出现那个标识 ⇒ 「评审说的是哪一条」可复述。
    """
    from packages.application.run_orchestration.novelty_claim import (
        novelty_claim_of_run,
    )

    run_id = str(readings.get("run_id") or "")
    if not run_id:
        return
    claim = novelty_claim_of_run(deps.artifacts, deps.ledger, run_id)
    matched = None if claim is None else claim.matched_prior
    readings["novelty_matched_prior"] = matched
    bare = "" if not matched else matched.split(":")[-1]
    texts = _review_texts(deps, chain)
    readings["review_texts_cite_that_identifier"] = sum(
        1 for text in texts if bare and bare in text
    )


def _review_texts(deps: Any, chain: dict[str, Any]) -> list[str]:
    """**评审者写的正文**（`review_decision` 制品），不是验收门的判词。

    两者是不同的面：`GET /runs/{id}/reviews` 给的是**验收门**逐条判据（`findings` 里是
    `ARTIFACT_EXISTS …` 一类的机器判词）；「评审者说了什么」在它自己的交付物里
    （`{task}:review_decision` 的信封 `content`）。本判据要的是后者 —— 否则「引用了标识」
    这件事永远数成 0（实测）。
    """
    texts: list[str] = []
    for artifact_id in chain["artifact_ids"]:
        if not str(artifact_id).endswith(":review_decision"):
            continue
        raw = deps.artifacts.get(str(artifact_id)).decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except ValueError:
            continue
        content = payload.get("content") if isinstance(payload, dict) else None
        texts.append(content if isinstance(content, str) else raw)
    return texts


def _write_failure_reason(client: Any, run_id: str, readings: dict[str, Any]) -> None:
    """把 run 的**终态原因**也写进取证（失败路径同样留下可归因的读数）。"""
    if not run_id:
        return
    try:
        events = client.get(f"/runs/{run_id}/events").json()
    except Exception:  # noqa: BLE001 - 取证失败不得掩盖判据本身
        return
    rows = events.get("items") if isinstance(events, dict) else events
    reasons = [
        str(row.get("payload", {}).get("message"))
        for row in rows or []
        if isinstance(row, dict)
        and str(row.get("event_type", "")).endswith(("run.failed", "task.failed"))
    ]
    if reasons:
        readings["failure_reasons"] = reasons[-3:]


def _read_chain(client: Any, run_id: str) -> dict[str, Any]:
    """读面读数（制品 / 证据 / 实验 / 判词各一次）。"""
    return {
        "artifacts": client.get(f"/runs/{run_id}/artifacts").json(),
        "evidence": client.get(f"/runs/{run_id}/evidence").json(),
        "experiments": client.get(f"/runs/{run_id}/experiments").json(),
        "reviews": client.get(f"/runs/{run_id}/reviews").json(),
    }


def _rows(payload: Any, key: str) -> int:
    """读面的行数（有的读面直接返回 list，有的包一层 `{key: [...]}`；两种都认）。"""
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        return len(payload.get(key) or [])
    return 0


def _artifact_ids(chain: dict[str, Any]) -> list[str]:
    items = chain["artifacts"]
    rows = items.get("items") if isinstance(items, dict) else items
    return [str(row.get("id")) for row in rows or [] if isinstance(row, dict)]


def _gate() -> Any:
    """live run 门（runtime 显式 openhands + 凭据可解析 + live 开关；缺一如实 skip）。"""
    from adapters.contracts.models_loaders import load_llm_endpoints
    from adapters.relay.credential_resolver import EnvCredentialResolver
    from services.api.runtime_support import OPENHANDS_RUNTIME

    endpoints = load_llm_endpoints("examples/config/llm_endpoints.yaml")
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=endpoints["main"],
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def test_the_product_entry_runs_the_whole_chain() -> None:
    """从产品入口起一次 run，走完七相，并把读数落盘（失败也落盘）。"""
    gate = _gate()
    if not gate.open:
        pytest.skip(str(skip_record_for_gate("goal097-productive-entry", gate)))

    deps = _assembled_product()
    try:
        deps.preflight_override = _preflight_override(deps)
        with TestClient(create_app(deps)) as client:
            readings = _drive_one_run(client, deps)
            assert readings["http_status"] == 200, readings.get("http_body")
            assert readings["state"] == "SUCCEEDED", readings.get("failure_reasons")
            assert readings["missing_phase_artifacts"] == [], readings
            assert readings["experiment_rows"] >= 1, readings
            # EC-04 的**端到端**那一半：创新点声明的 `nearest_prior` 真的命中了本 run
            # 检索到的标识；两位评审者的判词都引用了**同一个**标识（两面互相引用）。
            assert readings["novelty_matched_prior"], readings
            assert readings["review_texts_cite_that_identifier"] >= 2, readings
    finally:
        deps.close()


def _drive_one_run(client: Any, deps: Any) -> dict[str, Any]:
    """声明方向 → 起 run → 读四个读面 → **先写盘**再返回读数（失败路径同样有读数）。"""
    declared = client.put(
        "/projects/example-project/direction",
        json={"direction": _DIRECTION},
        headers={"Idempotency-Key": "goal097-declare-direction"},
    )
    assert declared.status_code == 200, declared.text
    started = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"goal097-{os.getpid()}-{started_key()}"},
    )
    payload = started.json()
    run_id = str(payload.get("id") or "")
    readings: dict[str, Any] = {
        "http_status": started.status_code,
        "http_body": started.text[:600],
        "state": payload.get("state"),
        "run_id": run_id,
        "protocol": _PROTOCOL_ID,
        "direction": _DIRECTION,
    }
    if run_id:
        _collect_readings(client, run_id, readings, deps)
    _write_evidence("读数", readings)
    return readings


def _collect_readings(client: Any, run_id: str, readings: dict[str, Any], deps: Any) -> None:
    """四个读面的读数（制品 / 证据 / 实验行 / 判词行）+ 失败原因。"""
    chain = _read_chain(client, run_id)
    artifact_ids = _artifact_ids(chain)
    chain["artifact_ids"] = artifact_ids
    readings["artifact_ids"] = artifact_ids
    readings["missing_phase_artifacts"] = [
        name
        for name in _PHASE_ARTIFACTS
        if not any(str(i).endswith(f":{name}") for i in artifact_ids)
    ]
    readings["experiment_rows"] = _rows(chain["experiments"], "experiments")
    readings["review_rows"] = _rows(chain["reviews"], "findings")
    _collect_novelty(deps, chain, readings)
    _write_failure_reason(client, run_id, readings)
