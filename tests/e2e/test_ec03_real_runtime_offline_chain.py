"""EC-03 端到端：真实 runtime 的离线全链（GOAL-20260919-007 / PLAN-20260919-109）。

链路四段（各自独立可判）：

1. **会话创建**：真实 adapter 在控制面被真正调用（mock 端点收到补全请求）。
2. **事件映射**：会话进入 canonical 事件链（`manifest.frozen` → … → 终态）。
3. **预算归账**：usage 进 BudgetLedger。
4. **制品与证据落 canonical**：artifact / evidence 可读。

全程**离线**：mock 端点是本机 `threading` HTTP 服务器（不出公网）；localhost 由
`allow_localhost_endpoints=True` **显式**放行（默认 deny 不变，见 EC-02）；
workspace 由 `workspace_allow_host_shell=True` **显式**打开（默认 deny 不变）。

**如实登记的一处射程边界**（本文件不声称已解决）：

- 冻结 Tool Set 是 Research OS 的 **tool provider id**（`openhands_workspace` /
  `m12_artifact` / `ncbi_eutils`），不是 SDK 工具名；provider → SDK 工具的映射属
  EC-05（工具面边界）。本 e2e 用**测试侧**的惰性注册补上这一环，好让四段可测；
  真实控制面缺这一环的行为由 `test_unmapped_tool_set_is_named_not_silently_dropped`
  如实测量并记录。

四段的**实测终点**（不是设计意图，是本机实跑结果）：会话真的驱动了 mock 端点、
事件进了 canonical 链、usage 落了账、交付物经登记链变成 evidence——最后由既有
acceptance gate 对着合约判**拒绝**（合约声明要 `analysis_report`，真实会话交付的是
`session_message`）。判拒绝是这条链在正常工作，不是缺陷：本 EC 的靶子是"真实
runtime 能走完全链并使每一段可判"，不是"演示合约一定通过"。
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from packages.domain.budget import ResourceType

_PROTOCOL = "console_demo_research_v1.yaml"


class _MockRelayHandler(BaseHTTPRequestHandler):
    """最小 OpenAI-compatible 端点：`GET /models` + `POST /v1/chat/completions`。"""

    requests: list[dict[str, Any]] = []

    def do_GET(self) -> None:  # noqa: N802
        payload = json.dumps({"data": [{"id": "relay-model", "object": "model"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        _MockRelayHandler.requests.append(body)
        response = {
            "id": "chatcmpl-mock-1",
            "object": "chat.completion",
            "created": 1755000000,
            "model": body.get("model", "relay-model"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Done."},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
        }
        payload = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


@pytest.fixture
def mock_relay() -> Iterator[str]:
    """本机 mock 端点（threading HTTP 服务器；不出公网）。"""
    _MockRelayHandler.requests = []
    server = HTTPServer(("127.0.0.1", 0), _MockRelayHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _inert_tool_class() -> Any:
    """惰性 SDK 工具（无副作用）：只为让 provider id 在 SDK 注册表里可解析。"""
    from openhands.sdk.tool.schema import Action, Observation
    from openhands.sdk.tool.tool import ToolDefinition, ToolExecutor

    class _InertAction(Action):
        note: str = ""

    class _InertExecutor(ToolExecutor[Any, Observation]):
        def __call__(self, action: Any, conversation: Any = None) -> Observation:
            return Observation.from_text("inert")

    class InertTool(ToolDefinition[Any, Observation]):
        @classmethod
        def create(cls, conv_state: Any = None, **params: Any) -> list[Any]:
            tool = cls(
                description="Inert test tool",
                action_type=_InertAction,
                observation_type=None,
                executor=_InertExecutor(),
            )
            return [tool]

    return InertTool


def _register_all(frozen: tuple[str, ...]) -> None:
    """把冻结 Tool Set 按名注册为惰性工具（测试侧替代 EC-05 的 provider→SDK 映射）。"""
    from openhands.sdk.tool.registry import register_tool

    tool_class = _inert_tool_class()
    for name in frozen:
        register_tool(name, tool_class)


def _point_catalog_at(deps: Any, base_url: str) -> None:
    """把目录里所有 endpoint 的 base_url 指向 `base_url`（其余字段不动）。"""
    from dataclasses import replace

    context = deps.preflight_override
    assert context is not None
    endpoints = {
        key: replace(endpoint, base_url=base_url)
        for key, endpoint in context.catalog.endpoints.items()
    }
    deps.preflight_override = replace(
        context, catalog=replace(context.catalog, endpoints=endpoints)
    )


def _register_live_key(deps: Any, live_key: str | None) -> None:
    """把环境变量里的凭据**值**注册进解析器；本模块不写任何可用凭据字面量。"""
    if live_key is None:
        return
    from adapters.fakes.credential_resolver import FakeCredentialResolver

    # `ApiDeps.credentials` 声明为 Port；run_fixtures 注入的是 Fake 实现。
    cast(FakeCredentialResolver, deps.credentials).register("LLM_MAIN_KEY", live_key)


def _host_shell_workspace(lease: Any, session_id: str) -> Any:
    """测试侧 workspace 构造：**显式**打开 host shell（生产的默认 deny 不放松）。"""
    from adapters.openhands.workspace_adapter import build_local_workspace

    return build_local_workspace(lease, session_id, allow_host_shell=True)


def _real_runtime(deps: Any, settings: Any, policy: Any, *, map_tools: bool) -> Any:
    """测试装配的真实 adapter；`map_tools=False` 改走**生产装配**以测量缺映射行为。"""
    from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
    from adapters.openhands.session_types import AdapterDependencies
    from services.api.assembly import policy_bindings
    from services.api.runtime_support import build_agent_runtime, session_llm_factory

    policy_evaluator = policy_bindings().get("policy_evaluator")
    assert policy_evaluator is not None, "policy.yaml must be loadable for the real runtime"
    if not map_tools:
        # 生产装配的 register_tools 缺省为空操作——保留原样以**如实测量**缺映射时的行为。
        runtime = build_agent_runtime(
            settings,
            credentials=deps.credentials,
            policy_evaluator=policy_evaluator,
            budget_ledger=deps.budget,
        )
        assert isinstance(runtime, OpenHandsRuntimeAdapter)
        return runtime
    return OpenHandsRuntimeAdapter(
        AdapterDependencies(
            credential_resolver=deps.credentials,
            policy_evaluator=policy_evaluator,
            build_llm=session_llm_factory(deps.credentials, policy),
            build_workspace=_host_shell_workspace,
            register_tools=_register_all,  # 测试侧补上 EC-05 的映射
            budget_ledger=deps.budget,
        )
    )


def _openhands_deps(
    base_url: str,
    *,
    map_tools: bool,
    allow_localhost: bool = True,
    live_key: str | None = None,
) -> Any:
    """run-ready 装配 + 真实 adapter + 指向 `base_url` 的目录。

    `live_key` 非空时把它注册进凭据解析器——**值只从环境变量来**（调用方读
    `RESEARCHOS_LIVE_E2E_KEY`）。
    """
    from dataclasses import replace

    from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.runtime_support import OPENHANDS_RUNTIME, resolve_runtime_selection
    from services.api.settings import ApiSettings
    from tests.api.run_fixtures import make_run_ready_deps

    deps = make_run_ready_deps()
    _point_catalog_at(deps, base_url)
    _register_live_key(deps, live_key)
    settings = ApiSettings(
        agent_runtime=OPENHANDS_RUNTIME,
        allow_localhost_endpoints=allow_localhost,
        workspace_allow_host_shell=True,
    )
    policy = EndpointUrlPolicy(allow_localhost=allow_localhost)
    runtime = _real_runtime(deps, settings, policy, map_tools=map_tools)
    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(replace(old._deps, runtime=runtime))
    deps.runtime_selection = resolve_runtime_selection(settings)
    deps.endpoint_url_policy = policy
    return deps


def _start(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"ec03-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def _failures(client: TestClient, run_id: str) -> list[str]:
    events = client.get(f"/runs/{run_id}/events").json()
    return [
        event["payload"].get("message", "")
        for event in events
        if event["type"] in ("run.failed", "task.failed")
    ]


def test_unmapped_tool_set_is_named_not_silently_dropped(mock_relay: str) -> None:
    """实测边界（EC-05 的活）：provider id 未映射成 SDK 工具时，失败**点名**它。

    这条不是"期望行为"的断言，而是对**今天真实行为**的固定：控制面不会偷偷把未知
    工具丢掉或换成别的工具，而是让会话创建失败并把名字报出来。
    """
    from services.api.app import create_app

    with TestClient(create_app(_openhands_deps(mock_relay, map_tools=False))) as client:
        run = _start(client)
        failures = _failures(client, run["id"])

    assert run["state"] == "FAILED"
    assert any("is not registered" in message for message in failures), failures
    assert _MockRelayHandler.requests == [], "no LLM call may happen before tools resolve"


@dataclass(frozen=True, slots=True)
class _ChainReads:
    """一次 run 的 canonical 读面快照（四段判据共用，避免各段各自重新取数）。"""

    run: dict[str, Any]
    failures: list[str]
    types: set[str]
    tasks: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]


def _read_chain(client: TestClient, run: dict[str, Any]) -> _ChainReads:
    """经**既有读面**取 canonical 事实（不经内部对象，判据才与 API 一致）。"""
    return _ChainReads(
        run=run,
        failures=_failures(client, run["id"]),
        types={event["type"] for event in client.get(f"/runs/{run['id']}/events").json()},
        tasks=client.get(f"/runs/{run['id']}/tasks").json(),
        evidence=client.get(f"/runs/{run['id']}/evidence").json(),
        artifacts=client.get(f"/runs/{run['id']}/artifacts").json(),
    )


def _assert_session_created(deps: Any, reads: _ChainReads) -> None:
    """段 1：真实 adapter 真的驱动了 LLM，且线上 model 就是目录里绑定的那个。"""
    assert _MockRelayHandler.requests, f"mock never reached; run={reads.run}; {reads.failures}"
    resolved_names = {
        model.model_name for model in (deps.preflight_override.catalog.models or {}).values()
    }
    sent_model = str(_MockRelayHandler.requests[-1].get("model", ""))
    assert any(name in sent_model for name in resolved_names), (sent_model, resolved_names)


def _assert_events_mapped(client: TestClient, reads: _ChainReads) -> None:
    """段 2：真实 SDK 事件树 → RuntimeEvent 的**映射结果**落 canonical。

    判据是 artifact 载荷里的 `message_count`（被映射出来的 MESSAGE 事件数）与真实
    adapter 的 `session_id`——canonical 事件表不落 session 级事件，这里就是映射段
    唯一的可判窗口。断掉映射（不计数）这两条即红。
    """
    assert "manifest.frozen" in reads.types
    assert reads.tasks and all(task["status"] for task in reads.tasks)
    session_artifact = next(
        (item for item in reads.artifacts if str(item["id"]).endswith(":session_message")),
        None,
    )
    assert session_artifact is not None, (
        [item["id"] for item in reads.artifacts],
        reads.failures,
        reads.run["state"],
    )
    mapped = client.get(f"/artifacts/{session_artifact['id']}/content").json()
    assert mapped["message_count"] >= 1, mapped
    assert mapped["session_id"], mapped


def _assert_usage_attributed(deps: Any, reads: _ChainReads) -> None:
    """段 3：账本里有正向 `MODEL_TOKENS`，且**归因**到本 run 的 task 与绑定的 model。

    mock 端点回报 12/3/15 tokens；判据不是"账本非空"，而是归因正确——这要求
    adapter 既写入条目、也把 `task_id`/`model_id` 填对（见 `usage_mapping`）。
    """
    assert deps.budget is not None
    token_entries = [
        entry
        for entry in deps.budget.snapshot().entries
        if entry.resource_type is ResourceType.MODEL_TOKENS and entry.quantity > 0
    ]
    assert token_entries, "no positive MODEL_TOKENS entry in the ledger"
    task_ids = {task["task_id"] for task in reads.tasks}
    assert {entry.task_id for entry in token_entries} <= task_ids
    catalog_models = deps.preflight_override.catalog.models or {}
    expected_models = {model.id for model in catalog_models.values()}
    assert {entry.model_id for entry in token_entries} <= expected_models, token_entries


def _assert_deliverable_adjudicated(reads: _ChainReads) -> None:
    """段 4：交付物经既有登记链落 canonical，再由 acceptance gate 对着合约裁决。

    判拒是链在正常工作（合约要 `analysis_report`，真实会话给 `session_message`）；
    反过来，"carries no structured output"出现即说明登记链被跳过了。
    """
    assert reads.evidence, "canonical evidence is empty: the deliverable never landed"
    assert reads.artifacts, "canonical artifacts are empty: the deliverable never landed"
    assert reads.run["state"] == "FAILED", reads.run
    assert any("acceptance gate" in message for message in reads.failures), reads.failures
    assert not any("carries no structured output" in message for message in reads.failures), (
        reads.failures
    )


def test_real_runtime_offline_chain_segments(mock_relay: str) -> None:
    """四段：会话创建 / 事件映射 / 预算归账 / 制品与证据。"""
    from services.api.app import create_app

    deps = _openhands_deps(mock_relay, map_tools=True)
    with TestClient(create_app(deps)) as client:
        reads = _read_chain(client, _start(client))
        _assert_session_created(deps, reads)
        _assert_events_mapped(client, reads)
    _assert_usage_attributed(deps, reads)
    _assert_deliverable_adjudicated(reads)


@pytest.mark.requires_live_llm
def test_live_endpoint_is_exercised_only_when_credentials_are_configured() -> None:
    """真端点全链的门控用例：无凭据环境**如实 skip**（skip 不是 PASS）。

    要跑它，操作者需同时给出（只经环境变量，永不硬编码、不落盘）：

    - `RESEARCHOS_LIVE_E2E_ENDPOINT`：OpenAI-compatible Base URL（含版本段，
      如 `https://<host>/v1`）；目录里声明的模型须由该端点提供。
    - `RESEARCHOS_LIVE_E2E_KEY`：该端点的 API Key。

    判据是「真端点被真实调用、usage 真落账」——不是「run 一定成功」：合约层的
    通过与否取决于真实模型产出什么，那属于模型能力，不属于本 EC 的靶子。
    """
    base_url = os.environ.get("RESEARCHOS_LIVE_E2E_ENDPOINT")
    api_key = os.environ.get("RESEARCHOS_LIVE_E2E_KEY")
    if not base_url or not api_key:
        pytest.skip("live LLM e2e needs RESEARCHOS_LIVE_E2E_ENDPOINT + RESEARCHOS_LIVE_E2E_KEY")

    from services.api.app import create_app

    deps = _openhands_deps(
        base_url.rstrip("/"),
        map_tools=True,
        allow_localhost=False,  # 真端点必须是公网地址：默认 deny 姿态不放松
        live_key=api_key,
    )
    with TestClient(create_app(deps)) as client:
        run = _start(client)
        failures = _failures(client, run["id"])
        entries = deps.budget.snapshot().entries

    assert entries, f"live run produced no usage: state={run['state']} failures={failures}"
