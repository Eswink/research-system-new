"""GOAL-024 EC-02 读面支撑：应用级装配 + 合成金丝雀注入 + 路由树枚举 + 逐路由实取。

三件事：

1. **应用级装配**（不是只跑编排层）：`make_run_ready_deps()` → 换入金丝雀 runtime →
   `create_app()` → `TestClient`。读面必须是**应用自己的路由表**上的响应体。
2. **合成金丝雀注入**（一律测试内构造，绝不携带真实内容）：用户起草的协议正文
   （草稿 `yaml_text`，随 run 冻结进 canonical）、会话产出的制品正文、claim 正文。
3. **读面取证**：遍历应用路由树的 GET 叶子（含 FastAPI 新版把 `include_router`
   包成的 `_IncludedRouter`），逐路由实取 `(status, 响应文本)`；扫描是**纯函数**。

**口径（白名单）**：读面**契约声明**返回内容的那些路由（草稿正文 / 制品正文 / claim
正文）是**声明过的载体**；其余路由必须**零命中**。未观测到对象的承载路由**逐条登记**
（理由非空），不算通过。
"""

from __future__ import annotations

import contextlib
import json
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from packages.application.run_orchestration import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from services.api.app import create_app
from tests.e2e.scenario import StructuredOutputAgentRuntime
from tests.observability.content_canary_support import (
    ARTIFACT_BODY,
    CANARIES,
    EVIDENCE_BODY,
    PROMPT_TEXT,
    Canary,
    hits,
)

_RUN = uuid.uuid4().hex[:10]
_PROTOCOL_PATH = Path("examples/protocols/m12_reference_research_v1.yaml")
PROJECT_ID = "example-project"
#: 制品正文与 diff 伙伴（两份都进 canonical；diff 路由据此有内容可回）。
ARTIFACT_ID = f"canary-artifact:{_RUN}"
ARTIFACT_PARTNER_ID = f"canary-artifact-partner:{_RUN}"
CLAIM_ID = f"claim-canary-{_RUN}"


def canary_protocol_text() -> str:
    """用户起草的协议正文：把金丝雀写进一个**随解析进 canonical** 的正文位置。

    合成串写在 phase 的 `name` 里（协议正文的一等字段），而不是注释——
    注释不进解析后的正文，放注释就没法证明它真的进了 canonical。
    """
    text = _PROTOCOL_PATH.read_text(encoding="utf-8")
    return text.replace("name: Domain Discovery", f"name: Domain Discovery {PROMPT_TEXT.value}", 1)


class CanaryRuntime(StructuredOutputAgentRuntime):
    """受控执行体：会话产出的制品正文里带合成金丝雀。"""

    def __init__(self) -> None:
        super().__init__(
            structured_output={
                "analysis_report": {"text": ARTIFACT_BODY.value},
                "review_decision": {"verdict": "PASS", "score": 0.95},
            }
        )


@dataclass(slots=True)
class ReadFace:
    """一次读面取证的完整现场（canonical 注入 + 实取结果）。"""

    client: TestClient
    deps: Any
    app: Any
    draft_id: str
    run_id: str
    ids: dict[str, str] = field(default_factory=dict)
    #: canonical 侧的证据（证明夹具真的把金丝雀写进了业务真相）。
    canonical_text: str = ""


def _swap_runtime(deps: Any) -> None:
    """换入金丝雀 runtime（既有夹具一字不改：改的是注入进来的实例）。"""
    from dataclasses import replace

    inner: OrchestrationDependencies = deps.runs._deps
    deps.runs = RunOrchestrationService(replace(inner, runtime=CanaryRuntime()))


def _artifact(artifact_id: str, payload: bytes, run_id: str) -> Any:
    from packages.domain.artifacts import Artifact
    from packages.domain.core import Digest

    return Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(payload),
        size_bytes=len(payload),
        media_type="application/json",
        source_refs=[f"run:{run_id}"],
        classification="execution_result",
    )


def _seed_canonical(deps: Any, run_id: str) -> None:
    """把带金丝雀的制品 + evidence + claim 写进 canonical（业务真相侧）。"""
    from packages.domain.evidence import (
        Claim,
        ClaimStatus,
        Evidence,
        EvidenceRelation,
        EvidenceRelationType,
    )

    store = deps.artifacts
    body = json.dumps({"text": ARTIFACT_BODY.value}, ensure_ascii=False).encode("utf-8")
    partner = json.dumps({"text": f"partner-{_RUN}"}, ensure_ascii=False).encode("utf-8")
    for artifact_id, payload in ((ARTIFACT_ID, body), (ARTIFACT_PARTNER_ID, partner)):
        store.put(_artifact(artifact_id, payload, run_id), payload)
    ledger = deps.ledger
    ledger.register_evidence(
        Evidence(
            id=f"evidence-canary-{_RUN}",
            source_ref=ARTIFACT_ID,
            content_digest=str(_artifact(ARTIFACT_ID, body, run_id).digest),
            run_id=run_id,
            artifact_id=ARTIFACT_ID,
        )
    )
    ledger.register_claim(
        Claim(id=CLAIM_ID, statement=EVIDENCE_BODY.value, status=ClaimStatus.PROPOSED)
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=CLAIM_ID,
            evidence_id=f"evidence-canary-{_RUN}",
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


def _create_draft(client: TestClient) -> str:
    response = client.post(
        f"/projects/{PROJECT_ID}/protocol-drafts",
        json={"name": f"canary-draft-{_RUN}", "yaml_text": canary_protocol_text()},
        headers={"Idempotency-Key": f"draft-{_RUN}"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["draft_id"])


def _start_run(client: TestClient, draft_id: str) -> str:
    response = client.post(
        f"/projects/{PROJECT_ID}/runs",
        json={"draft_id": draft_id, "draft_revision": 1},
        headers={"Idempotency-Key": f"run-{_RUN}"},
    )
    assert response.status_code == 200, response.text
    return str(response.json()["id"])


def _create_endpoint_and_model(client: TestClient) -> dict[str, str]:
    """建端点 + 模型：让端点/模型那几条读路由**有真对象**（不是空响应上的空真）。"""
    from tests.api.conftest import make_endpoint_payload

    created = client.post(
        "/llm-endpoints",
        json=make_endpoint_payload(name=f"canary-endpoint-{_RUN}"),
        headers={"Idempotency-Key": f"endpoint-{_RUN}"},
    )
    assert created.status_code == 201, created.text
    endpoint_id = str(created.json()["id"])
    model_name = f"canary-model-{_RUN}"
    model = client.post(
        "/models",
        json={
            "endpoint_id": endpoint_id,
            "model_name": model_name,
            "display_name": "Canary Model",
        },
        headers={"Idempotency-Key": f"model-{_RUN}"},
    )
    assert model.status_code == 201, model.text
    return {"endpoint_id": endpoint_id, "model_id": str(model.json()["id"])}


def _collect_ids(client: TestClient, draft_id: str, run_id: str) -> dict[str, str]:
    """参数替换表：能用真对象的地方一律用真对象（不拿合成 id 冒充观测）。"""
    ids = {
        "project_id": PROJECT_ID,
        "draft_id": draft_id,
        "revision": "1",
        "run_id": run_id,
        "artifact_id": ARTIFACT_ID,
        "left_id": ARTIFACT_ID,
        "right_id": ARTIFACT_PARTNER_ID,
    }
    ids.update(_create_endpoint_and_model(client))
    for key, path, field_name in (("template_id", "/protocol-templates", "template_id"),):
        rows = client.get(path)
        if rows.status_code == 200 and rows.json():
            ids[key] = str(rows.json()[0][field_name])
    return ids


@contextlib.contextmanager
def open_read_face() -> Iterator[ReadFace]:
    """装配应用、注入金丝雀、跑一次真 run，交出可实取的读面现场。"""
    from tests.api.run_fixtures import make_run_ready_deps

    deps = make_run_ready_deps()
    _swap_runtime(deps)
    app = create_app(deps)
    with TestClient(app) as client:
        draft_id = _create_draft(client)
        run_id = _start_run(client, draft_id)
        _seed_canonical(deps, run_id)
        face = ReadFace(
            client=client,
            deps=deps,
            app=app,
            draft_id=draft_id,
            run_id=run_id,
            ids=_collect_ids(client, draft_id, run_id),
        )
        face.canonical_text = canonical_truth_text(face)
        yield face


def _leaves(route: Any) -> list[Any]:
    """路由树叶子；FastAPI 新版把 `include_router` 包成 `_IncludedRouter`。"""
    inner = getattr(route, "original_router", None)
    if inner is not None:
        out: list[Any] = []
        for child in getattr(inner, "routes", []) or []:
            out.extend(_leaves(child))
        return out
    nested = getattr(route, "routes", None)
    if nested:
        out = []
        for child in nested:
            out.extend(_leaves(child))
        return out
    return [route]


def read_routes(app: Any) -> tuple[str, ...]:
    """应用路由树上的 GET 叶子路径（读面 = 应用自己声明的 GET 面）。"""
    paths: set[str] = set()
    for route in _leaves(app.router):
        path = getattr(route, "path", None)
        methods = set(getattr(route, "methods", None) or [])
        if path and "GET" in methods:
            paths.add(str(path))
    return tuple(sorted(paths))


def fill_path(path: str, ids: dict[str, str]) -> str | None:
    """把路径参数换成真对象 id；缺参数 ⇒ None（调用方登记为未实取）。"""
    filled = path
    for key, value in ids.items():
        filled = filled.replace("{" + key + "}", value)
    return None if "{" in filled else filled


def response_text(response: Any) -> str:
    """响应体文本（字节一律按 utf-8 容错解码后再扫，避免二进制漏扫）。"""
    body = bytes(response.content)
    return body.decode("utf-8", errors="ignore")


def scan(text: str, canaries: tuple[Canary, ...] = CANARIES) -> list[str]:
    """命中金丝雀 kind（纯函数：便于反证与措辞对照）。"""
    return hits(text, canaries)


def canonical_truth_text(face: ReadFace) -> str:
    """canonical 侧原文：草稿正文 + 制品正文 + claim 正文。

    直接读**存储对象**（不是读 HTTP 响应）——这一份是「业务真相里确实有金丝雀」的
    证据，用来让读面零命中**不是空真**。
    """
    chunks: list[str] = [face.draft_id]
    record = face.deps.protocol_draft_service.get(face.draft_id)
    chunks.append(str(getattr(record, "yaml_text", "")))
    chunks.append(face.deps.artifacts.get(ARTIFACT_ID).decode("utf-8", errors="ignore"))
    chunks.append(str(face.deps.ledger.get_claim(CLAIM_ID).statement))
    return "\n".join(chunks)
