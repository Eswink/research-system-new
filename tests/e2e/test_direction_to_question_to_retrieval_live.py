"""GOAL-20261019-089 **EC-04** live 判据：方向只给一句话，系统自己提出研究问题并检索。

**判什么**（一次真实 run，点名 `direction_to_question_v1.yaml`，**产品组合根** +
`preflight_override is None` + 真实执行体）：

1. 终态恰为 `SUCCEEDED`（`FAILED` 也是终态，但不在这里算通过）；
2. `question` 格**自己提出**了问题：`{task}:research_question` 落库，且其正文里有
   `research_question` 块与 `query`；
3. `retrieval` 格的检索**真的**用了那个 query：证据链里的检索调用参数（`tool-args:`
   制品的字节）里的 `term` 与问题里的 `query` **逐字相同**；
4. 检索命中的**真实标识**（PMID/DOI）出现在证据读面上；
5. 读数落盘（run id / 问题正文 / 检索词 / 真实标识 / 报告 digest 或制品 digest），
   供 GOAL 的「真跑读数」逐条引用。

**默认门**：`evaluate_live_run_gate`（runtime 显式 `openhands` + 凭据可解析 + 开关打开），
三者缺一 ⇒ **如实 skip**（skip 不是 PASS）。

跑它（凭据只由操作者注入；本文件不读值、不回显、不落盘）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \\
      uv run --frozen --no-sync python -B -m pytest \\
      tests/e2e/test_direction_to_question_to_retrieval_live.py -q -rs

**如实边界**：本判据证明「检索词来自模型自己写下的问题」这一条机械事实；它**不**判
问题提得好不好（`W-2`），也**不**声称报告叙述质量（报告域的另一格）。
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.contracts.models_loaders import load_llm_endpoints
from adapters.relay.credential_resolver import EnvCredentialResolver
from packages.application.model_relay.live_run_gate import (
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from services.api.runtime_support import OPENHANDS_RUNTIME
from tests.e2e.live_control_plane_support import (
    ENDPOINT_ID,
    PROVIDER_ID,
    product_control_plane_deps,
)
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_PROTOCOL = "direction_to_question_v1.yaml"
_PROTOCOL_ID = "direction_to_question_v1_0_0"
#: 一句话方向（**只有这一句**：系统要自己把它变成问题与检索词）。
_DIRECTION = "retrieval augmentation for scientific hypothesis generation"
_SAMPLE = Path("scratch") / "goal089-ec04-live-run.json"
_PMID = re.compile(r"\d{6,9}")
#: 参数制品的 `classification`（`phase_capabilities._tool_call` 的落库值）。
TOOL_ARGS_CLASSIFICATION = "tool-args"
#: 检索 / 读取调用在参数制品 id 与 source_ref 里的操作键（`RunChainCall.tool_id`）。
_SEARCH_TOOL_ID = "literature_search"
_READ_TOOL_ID = "literature_read"


def _identifier_suffix(source_ref: str) -> list[str]:
    """读取步 `source_ref` 末段的那批标识（`…:{id}+{id}+{id}`；末段不是当批 ⇒ 空）。"""
    tail = source_ref.rsplit(":", 1)[-1]
    return [part for part in tail.split("+") if _PMID.fullmatch(part)]


def _endpoint() -> Any:
    return load_llm_endpoints(_ENDPOINTS)[ENDPOINT_ID]


def _gate() -> Any:
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _wired_deps() -> Any:
    """产品组合根 + 两段**执行体**缝（检索 provider 实例）；判词不注入。"""
    from dataclasses import replace

    from adapters.research_tools import NcbiEutilsProvider
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.catalog_merge import merged_catalog_snapshot

    deps = product_control_plane_deps(
        f"data/goal089-live-{os.getpid()}.db",
        agent_runtime=OPENHANDS_RUNTIME,
        # AGENTS §9：host shell 默认 deny；真实 run 要建会话必须显式打开（同一条纪律）。
        allow_host_shell=True,
    )
    provider = NcbiEutilsProvider(deps.artifacts, spill_threshold_bytes=1)
    # `europe_pmc` 因**能力并集**进入冻结集（它同样声明 literature.search/read）⇒ 预检会
    # 对它做健康探测。装配方按同一纪律**提供实例**（不是注入判词）：没有实例时它的健康
    # 诚实地是 UNKNOWN ⇒ `TOOL_HEALTH_UNPROVEN` WARN ⇒ 拒冻。
    from adapters.research_tools import EuropePmcProvider

    deps.tool_providers = {
        PROVIDER_ID: provider,
        "europe_pmc": EuropePmcProvider(deps.artifacts, spill_threshold_bytes=1),
    }
    spec = merged_catalog_snapshot(deps).tool_providers[PROVIDER_ID]
    inner = deps.runs._deps
    deps.runs = RunOrchestrationService(
        replace(inner, capabilities=_capability_step(deps, provider, spec))
    )
    # 方向：产品读面（`ProjectStore`）上声明一句话 —— 与 `PUT /projects/{id}/direction`
    # 同一条落库路径（判据直接用 store，避免多一次 HTTP 往返改判读数的可读性）。
    from packages.domain.core import Timestamp
    from packages.domain.projects import ProjectDefinition, ProjectStatus
    from services.api.catalog import load_project_name

    assert deps.project_store is not None
    deps.project_store.save_project(
        ProjectDefinition(
            id="example-project",
            name=load_project_name(),
            status=ProjectStatus.ACTIVE,
            created_at=Timestamp.now(),
            updated_at=Timestamp.now(),
            direction=_DIRECTION,
        )
    )
    return deps


def _capability_step(deps: Any, provider: Any, spec: Any) -> Any:
    """运行链两步：检索词来自**上游问题产物**（`research_question.query`）。

    与既有 live 支持件（`live_run_support._retrieval_calls`）的**唯一差别**就是这一条
    参数路径 —— 因为本协议的检索词来自模型写下的问题，而不是操作者预填的简报。
    """
    from packages.application.run_orchestration.phase_capabilities import (
        CapabilityDeps,
        RunChainCall,
    )

    return CapabilityDeps(
        calls=(
            RunChainCall(
                provider_id=PROVIDER_ID,
                tool_id="literature_search",
                capability="literature.search",
                arguments_from_input=("research_question.query",),
                fixed_arguments={"retmax": 3},
                # 两条调用**只属于检索相**：`question` 相也声明了 `run_chain`（为了让它的
                # 会话工具面为空），若不按 phase 收窄，它会在**问题还没产出时**就执行检索。
                phase_id="retrieval",
            ),
            RunChainCall(
                provider_id=PROVIDER_ID,
                tool_id="literature_read",
                capability="literature.read",
                ids_from_previous="ids",
                phase_id="retrieval",
            ),
        ),
        providers={PROVIDER_ID: provider},
        provider_specs={PROVIDER_ID: spec},
        policy=deps.policy_evaluator,
        artifacts=deps.artifacts,
        ledger=deps.ledger,
    )


def _question_text(store: Any, artifact_id: str) -> str:
    """问题的正文（交付物信封的 `content`；直形态则整份 JSON）。"""
    raw = store.get(artifact_id).decode("utf-8")
    payload = json.loads(raw)
    content = payload.get("content")
    return content if isinstance(content, str) else raw


def _query_of(text: str) -> str:
    """从问题正文里读出 `research_question.query`（**判据读它，不猜**）。"""
    for candidate in (text.strip(), _fenced(text)):
        if candidate is None:
            continue
        try:
            parsed = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(parsed, dict) and "research_question" in parsed:
            block = parsed["research_question"]
            if isinstance(block, dict) and isinstance(block.get("query"), str):
                return str(block["query"])
    raise AssertionError(f"the question artifact carries no research_question.query: {text[:400]}")


def _strings(payload: Any) -> list[str]:
    """载荷里的**全部字符串值**（递归；判据按印迹取证，不绑定属性名）。"""
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        return [item for value in payload.values() for item in _strings(value)]
    if isinstance(payload, list):
        return [item for value in payload for item in _strings(value)]
    return []


def _fenced(text: str) -> str | None:
    if "```" not in text:
        return None
    parts = text.split("```")
    if len(parts) < 3:
        return None
    body = parts[1]
    newline = body.find("\n")
    return body[newline + 1 :] if newline != -1 else body


def _search_argument_artifacts(deps: Any) -> list[str]:
    """检索调用参数制品（**制品面枚举**，不看 run 是否成功、不看任务行是否存在）。"""
    return sorted(
        item.id
        for item in deps.artifacts.list_refs()
        if item.classification == TOOL_ARGS_CLASSIFICATION
        and item.id.endswith(f":{_SEARCH_TOOL_ID}")
    )


def _search_terms(deps: Any, artifact_ids: list[str]) -> list[str]:
    """参数制品里的**全部字符串值**（判据按印迹取证，不绑定属性名）。"""
    payloads = [
        json.loads(deps.artifacts.get(artifact_id).decode("utf-8")) for artifact_id in artifact_ids
    ]
    return [value for payload in payloads for value in _strings(payload)]


def _retrieved_identifiers(
    evidence: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """读取步的真实标识 + 那些证据行（标识只从 `source_ref` 末段取，见正文注释）。"""
    steps = [item for item in evidence if _READ_TOOL_ID in item["source_ref"]]
    identifiers = sorted({
        identifier for item in steps for identifier in _identifier_suffix(item["source_ref"])
    })
    return identifiers, steps


def _write_readings(
    run_id: str,
    run: dict[str, Any],
    artifacts: list[dict[str, Any]],
    readings: dict[str, Any],
) -> None:
    """读数落盘（run id / 问题 / 检索词 / 真实标识 / digest 逐条）。"""
    report = {
        "run_id": run_id,
        "protocol_id": run["protocol_id"],
        "state": run["state"],
        "direction": _DIRECTION,
        **readings,
        "artifact_digests": {item["id"]: item["digest"] for item in artifacts},
    }
    _SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    _SAMPLE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_once(deps: Any) -> tuple[str, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """起一次 run 并读回三份读面（run / evidence / artifacts）。"""
    from services.api.app import create_app

    with TestClient(create_app(deps)) as c:
        created = c.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": "goal089-ec04-live"},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        run = c.get(f"/runs/{run_id}").json()
        evidence = c.get(f"/runs/{run_id}/evidence").json()
        artifacts = c.get(f"/runs/{run_id}/artifacts").json()
    return run_id, run, evidence, artifacts


def _question_and_query(deps: Any, artifacts: list[dict[str, Any]]) -> tuple[str, str]:
    """立题格的产物正文 + 它声明的那条 query（判据读它，不猜）。"""
    question_ids = [
        item["id"] for item in artifacts if str(item["id"]).endswith(":research_question")
    ]
    assert len(question_ids) == 1, artifacts
    question = _question_text(deps.artifacts, question_ids[0])
    return question, _query_of(question)


def test_a_single_sentence_direction_becomes_a_question_and_a_real_search() -> None:
    gate = _gate()
    if not gate.open:
        pytest.skip(f"live run skipped: {skip_record_for_gate('goal089-ec04', gate).reason}")

    deps = _wired_deps()
    run_id, run, evidence, artifacts = _run_once(deps)
    question, query = _question_and_query(deps, artifacts)

    # (3) 检索**真的**用了问题里的 query：从检索**调用参数**里逐字取证。
    #
    # 取法是**印迹**而不是**同名键**：参数制品的属性名由 `RunChainCall` 的声明决定
    # （`arguments_for` 把点分路径的最后一段当参数名）⇒ 在**全部字符串值**里找那串字。
    #
    # **取法是制品面枚举**（`list_refs` 的 `classification` + id 后缀），不是
    # `/runs/{id}/artifacts`（按 claim relation 投影，参数制品不挂 relation），也不是
    # `task_identities`（运行链步在 `engine.submit` **之前**执行 ⇒ 检索零命中时那条 run
    # 是 FAILED 且**没有任务行**，实测到过这个空手而归的形态）。
    search_ids = _search_argument_artifacts(deps)
    assert search_ids, [item.id for item in deps.artifacts.list_refs()]
    search_terms = _search_terms(deps, search_ids)
    assert query in search_terms, (query, search_terms)

    # 真实标识只从**读取步**的 `source_ref` 末段取（形态见 `_retrieved_identifiers`）：
    # task id 自己就是十六进制串（`9f698093-…`），通用数字正则会把它误当 PMID。
    identifiers, retrieved_steps = _retrieved_identifiers(evidence)
    _write_readings(
        run_id,
        run,
        artifacts,
        {
            "question": question,
            "query": query,
            "search_terms": search_terms,
            "search_argument_artifacts": search_ids,
            "retrieved_identifiers": identifiers,
            "evidence_digests": sorted(item["content_digest"] for item in retrieved_steps),
        },
    )

    assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
    assert identifiers, "检索必须命中真实标识（否则覆盖门的性质维不会通过）"
