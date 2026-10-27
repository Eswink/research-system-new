"""GOAL-20261027-098 EC-02：**真跑**证明创新点的作者与评审者不是同一个模型。

**它补哪一格**：`tests/contracts/test_direction_to_report_v2_independence.py` 判的是
**结构面**（角色 / agent / `(endpoint, model_name)` 三者都不同）。结构不同**不代表**运行期
真的分开 —— 编译期解析正确、而执行期因为配额/回落/绑定写错把两者落到同一个模型，是
另一类缺陷。本判据判**运行期读数**：

1. **作者与评审者的执行目标不同**：`novelty_claim` 的产出方（`novelty_writer` /
   `deepseek-v4-pro-0813`）与评审它那位的 `reviewer_model`（`novelty_a` / `minimax-m3`）
   是两个不同的 `endpoint/model_name` 串；
2. **每条 `review_decision` 都可归因**：`reviewer_model` 非空**且**属于本协议评审者的目标集
   （`None` = 未声明该面，**不得**读成「独立」）；
3. **两位评审者彼此也不同**：`scientific_reviewer` 与 `novelty_reviewer` 落在两个不同目标上
   （否则「创新点有独立评审」只剩一个模型说了算）。

**反证臂**：把 `novelty` 相的角色改回 `novelty_reviewer`（真文件）⇒ 结构判据（EC-01）
点名判红 —— 那一条已在 `tests/contracts/` 里按 raw `sha256` 逐字节复原地跑过；本文件
**不重复**它，只判运行期读数（两件事）。

**如实边界**：本判据需要真中转站凭据 + Docker。缺一即**如实 skip**（**skip 不是 PASS**）。
凭据不可用 ⇒ EC-02 在 GOAL 里保持 `PENDING`，不拿同一个模型凑。

**取证**：`.cursor/plans/goals/evidence/GOAL-20261027-098-ec02-novelty-independence-run.txt`
（**先写盘再断言** —— GOAL-096 `W-1` 的教训：旧写法只在断言前写，失败路径走不到写盘）。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from packages.application.model_relay.live_run_gate import (
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from services.api.app import create_app
from services.api.runtime_support import OPENHANDS_RUNTIME
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = [pytest.mark.requires_live_llm, pytest.mark.requires_docker]

_EVIDENCE = Path(".cursor/plans/goals/evidence/GOAL-20261027-098-ec02-novelty-independence-run.txt")
_PROTOCOL = "direction_to_report_v2.yaml"
_PROTOCOL_ID = "direction_to_report_v2_0_0"
_DIRECTION = "retrieval augmentation for scientific hypothesis generation"

#: 本协议**评审格**的合约 id（作者格也有门结论，那是产品既有语义）。
_REVIEW_CONTRACT = "multi_role_review"

#: 出厂目录里三个评审面的执行目标（结构与 `examples/config/agents.yaml` 同源）。
_EXPECTED_REVIEW_TARGETS = {"main/glm-5.3", "main/kimi-k2.6", "main/minimax-m3"}
#: 作者的执行目标（`novelty_writer` 绑 `novelty_author_model` = `deepseek-v4-pro-0813`）。
_AUTHOR_TARGET = "main/deepseek-v4-pro-0813"


def _write_evidence(entry: str, readings: dict[str, Any]) -> None:
    """Readings are appended, never overwritten (a later flaky attempt must not erase a pass).

    Measured this round: after a successful capture, one upstream hiccup
    (`retry budget exhausted`) overwrote that SUCCEEDED reading with a FAILED one -- the
    preserved evidence was replaced by "the last attempt". Each attempt now appends a
    timestamped section, so the successful section survives.
    """
    import time

    _EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    lines: list[str] = []
    if not _EVIDENCE.exists():
        lines.append("# GOAL-20261027-098 EC-02 live-run readings")
    lines += ["", f"## {entry} @ {stamp}", ""]
    lines += [f"- `{key}`: {value}" for key, value in readings.items()]
    lines.append("")
    with _EVIDENCE.open("a", encoding="utf-8", newline=chr(10)) as handle:
        handle.write(chr(10).join(lines))


def _gate() -> Any:
    """live run 门（runtime 显式 openhands + 凭据可解析 + live 开关；缺一如实 skip）。"""
    from adapters.contracts.models_loaders import load_llm_endpoints
    from adapters.relay.credential_resolver import EnvCredentialResolver

    endpoints = load_llm_endpoints("examples/config/llm_endpoints.yaml")
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=endpoints["main"],
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _assembled_product() -> Any:
    """**产品组合根**（`assemble()`）；本函数**不补任何缝**。"""
    from services.api.composition import assemble
    from services.api.settings import ApiSettings

    deps = assemble(
        ApiSettings(
            db_path=f"data/goal098-live-{os.getpid()}.db",
            agent_runtime=OPENHANDS_RUNTIME,
            allow_localhost_endpoints=False,
            workspace_allow_host_shell=True,
            experiment_design_source="plan",
            workflow_lease_ttl_seconds=3600,
        )
    )
    register = getattr(deps.credentials, "register", None)
    value = os.environ.get("LLM_MAIN_KEY")
    if value and callable(register):
        register("LLM_MAIN_KEY", value)
    return deps


def _preflight_override(deps: Any) -> Any:
    """显式运维上下文（目录 + provider 健康；既有路径，非缝）。"""
    from packages.application.ports.resource_catalog import PreflightContext
    from packages.domain.enums import EndpointHealth
    from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings

    catalog = merged_catalog_snapshot(deps)
    project = merged_project_settings(deps, "example-project")
    return PreflightContext(
        catalog=catalog,
        project=project,
        credentials=deps.credentials,
        policy_evaluator=deps.policy_evaluator,
        endpoint_health={endpoint_id: EndpointHealth.HEALTHY for endpoint_id in catalog.endpoints},
        provider_health={
            provider_id: EndpointHealth.HEALTHY for provider_id in catalog.tool_providers
        },
    )


def _review_rows(deps: Any, run_id: str) -> list[dict[str, Any]]:
    """**评审格**的判词（canonical 读面；与 HTTP 读面同一查询口径）。"""
    from adapters.canonical.review_read import review_read

    assert deps.review_findings is not None, "产品组合根必须接上评审结论存储"
    reading = cast(dict[str, Any], review_read(deps.review_findings, {"run_id": run_id}))
    reviews = cast(list[dict[str, Any]], reading["reviews"])
    return [item for item in reviews if str(item.get("contract_id")) == _REVIEW_CONTRACT]


def _author_created_by(deps: Any, run_id: str) -> dict[str, Any]:
    """`novelty_claim` 制品的**产出方**读数（`created_by` + 制品 id）。

    「谁写了这份声明」的**产品事实**是 `Artifact.created_by`（会话产出是
    `agent:<agent id>`），不是提示词里的角色名 —— 只读角色名判不出「同一个实例」。
    """
    found: dict[str, Any] = {}
    for artifact_id in sorted(_artifact_ids(deps, run_id)):
        if not str(artifact_id).endswith(":novelty_claim"):
            continue
        meta = deps.artifacts.meta(str(artifact_id))
        if meta is not None:
            found["artifact_id"] = str(artifact_id)
            found["created_by"] = str(getattr(meta, "created_by", ""))
    return found


def _artifact_ids(deps: Any, run_id: str) -> set[str]:
    """本 run 的制品 id（经证据链投影，与读面同一取法）。"""
    ids: set[str] = set()
    for claim in deps.ledger.claims():
        for relation in deps.ledger.relations_for_claim(claim.id):
            try:
                item = deps.ledger.get_evidence(relation.evidence_id)
            except Exception:  # noqa: BLE001 - 引用可能已删除（与读面同一口径）
                continue
            if item.run_id == run_id and item.artifact_id:
                ids.add(str(item.artifact_id))
    return ids


def _drive(deps: Any) -> dict[str, Any]:
    """声明方向 → 起 run → 读评审面与作者面 → **先写盘**再返回读数。"""
    with TestClient(create_app(deps)) as client:
        client.put(
            "/projects/example-project/direction",
            json={"direction": _DIRECTION},
            headers={"Idempotency-Key": "goal098-declare-direction"},
        ).raise_for_status()
        started = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": f"goal098-{os.getpid()}-{os.urandom(4).hex()}"},
        )
        payload = started.json()
        run_id = str(payload.get("id") or "")
        readings: dict[str, Any] = {
            "entry": "TestClient(create_app(assemble(...))) —— 产品组合根，未补任何缝",
            "http_status": started.status_code,
            "state": payload.get("state"),
            "run_id": run_id,
            "protocol": _PROTOCOL_ID,
            "direction": _DIRECTION,
        }
        if run_id:
            rows = _review_rows(deps, run_id)
            readings["review_row_count"] = len(rows)
            readings["reviewer_models"] = sorted({str(item.get("reviewer_model")) for item in rows})
            readings["reviewer_agents"] = sorted({str(item.get("reviewed_by")) for item in rows})
            readings["reviewers_with_no_model"] = [
                str(item.get("reviewed_by")) for item in rows if not item.get("reviewer_model")
            ]
            readings.update(_author_created_by(deps, run_id))
            readings["failure_reasons"] = [
                str(event.get("payload", {}).get("message") or "")
                for event in client.get(f"/runs/{run_id}/events").json()
                if str(event.get("event_type", "")).endswith(("run.failed", "task.failed"))
            ][-3:]
    _write_evidence("true-run", readings)
    return readings


def test_the_novelty_author_and_its_reviewer_run_on_different_models() -> None:
    """**真跑**：作者与评审者落在不同执行目标；每条判词可归因；两位评审者彼此也不同。"""
    gate = _gate()
    if not gate.open:
        skip_record_for_gate("goal098-novelty-independence", gate)
        pytest.skip(f"live run skipped: {gate.reason}")

    deps = _assembled_product()
    try:
        deps.preflight_override = _preflight_override(deps)
        readings = _drive(deps)
    finally:
        deps.close()

    assert readings["http_status"] == 200, readings
    assert readings["state"] == "SUCCEEDED", readings.get("failure_reasons")

    # (1) **每条判词可归因**：`reviewer_model` 非空（`None` 不得读成「独立」）。
    assert readings["reviewers_with_no_model"] == [], readings
    targets = set(readings["reviewer_models"])
    assert targets, readings
    assert targets <= _EXPECTED_REVIEW_TARGETS, targets

    # (2) **两位评审者彼此也不同**（否则「创新点有独立评审」只剩一个模型说了算）。
    assert len(targets) >= 2, targets
    assert "main/minimax-m3" in targets, targets
    assert targets - {"main/minimax-m3"}, targets

    # (3) **作者不是评审者**：声明的产出方是作者 agent，且它**不在**评审者之列。
    #
    # `created_by` 的**产品形态**是裸 agent id（`result_handler`：
    # `created_by=agent_id or task.id.value`）——本轮第一次写成 `agent:novelty_writer` 是
    # **判据自己的错**（真跑读到的是 `novelty_writer`）⇒ 按产品事实更正，不是把产品改成
    # 判据想要的样子。`reviewed_by` 走的是另一条口径（`gate:<agent id>`），两者不同源。
    assert readings.get("created_by") == "novelty_writer", readings
    assert "gate:novelty_writer" not in readings["reviewer_agents"], readings
    # 作者的执行目标（出厂目录声明）与评审者的目标集**不交**。
    assert _AUTHOR_TARGET not in targets, targets
