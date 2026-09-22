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

四段的**实测终点**（GOAL-010 EC-01 之后）：会话真的驱动了 mock 端点、事件进了 canonical
链、usage 落了账、交付物经登记链变成 evidence——最后由既有 acceptance gate 对着合约裁决，
**声明对齐 ⇒ 门 PASS、run 到 `SUCCEEDED`**。
（GOAL-009 时期这条链的终点是**判拒**——合约要 `analysis_report`，真实会话给 `session_message`。
判据**没有放宽**：门仍按**字面名**匹配；改变的是**交付物的键名由合约声明决定**，
见 `runtime_adapter._declared_deliverable_name`。）
**两个分支成对**：
`test_real_runtime_offline_chain_segments` = 声明恰一个 ⇒ PASS；
`test_real_runtime_offline_chain_rejects_a_non_unique_declaration` = 声明不唯一 ⇒ adapter
**不猜** ⇒ REJECT（GOAL-009 那条判拒证据的保留位）。
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.domain.budget import ResourceType

# 共享装配见 `live_run_support`：同一文件被两个模块名导入会让 SDK 的 Action
# 子类被定义两次而毒化同进程事件 round-trip（Duplicate class definition）。
from tests.e2e.live_run_support import (
    declare_second_artifact as _declare_second_artifact,
)
from tests.e2e.live_run_support import (
    openhands_deps as _openhands_deps,
)
from tests.e2e.live_run_support import (
    run_failures as _failures,
)
from tests.e2e.live_run_support import (
    start_run as _start,
)

_PROTOCOL = "console_demo_research_v1.yaml"
#: GOAL-011 EC-01：声明了 `capability_execution: run_chain` 的真实协议（检索由运行链执行）。
_RETRIEVAL_PROTOCOL = "real_retrieval_research_v1.yaml"


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


def test_declared_run_chain_capabilities_let_production_assembly_start(mock_relay: str) -> None:
    """GOAL-011 EC-01：**声明为 run-chain 的能力不进会话工具列表** ⇒ 生产装配起得来。

    与上一条**成对**，两条合起来才是「声明化排除 ≠ 静默丢弃」的完整句：
    上一条 = 未声明的未映射名字**点名拒绝**（行为不变，且**用 demo 协议**测——它不声明
    这个字段）；这一条 = 显式声明 `capability_execution: run_chain` 的协议里，被声明排除的
    provider 名字**不进会话工具列表**，于是**生产装配**（`map_tools=False`，即
    `build_agent_runtime` 的真实缺省、register_tools 为空操作）也能把会话建起来。

    判据是**可观测的后果**，不是断言实现细节：mock 端点**收到了补全请求**（会话真的建起来
    并驱动了 LLM），失败原因里**没有** "is not registered"，且 run 到 `SUCCEEDED`。
    **反证**：删掉协议里的 `capability_execution` 行 ⇒ 本用例红——实测失败原因为
    `ToolDefinition 'm12_artifact' is not registered`（会话在建的时候就死），
    `_MockRelayHandler.requests` 为空。
    """
    from services.api.app import create_app

    with TestClient(create_app(_openhands_deps(mock_relay, map_tools=False))) as client:
        run = _start(client, _RETRIEVAL_PROTOCOL)
        failures = _failures(client, run["id"])

    assert _MockRelayHandler.requests, (
        "生产装配下会话没建起来 ⇒ 声明化排除没生效",
        run,
        failures,
    )
    assert not any("is not registered" in message for message in failures), failures
    assert run["state"] == "SUCCEEDED", (run, failures)


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


def _assert_events_mapped(
    client: TestClient, reads: _ChainReads, *, expected_suffix: str = ":analysis_report"
) -> None:
    """段 2：真实 SDK 事件树 → RuntimeEvent 的**映射结果**落 canonical。

    判据是 artifact 载荷里的 `message_count`（被映射出来的 MESSAGE 事件数）与真实
    adapter 的 `session_id`——canonical 事件表不落 session 级事件，这里就是映射段
    唯一的可判窗口。断掉映射（不计数）这两条即红。

    交付物的**键名**在这里同时被钉住（GOAL-010 EC-01）：示例合约
    `console_demo_deliverable` 声明恰一个 artifact 名 `analysis_report`，因此制品 id
    以它结尾；而载荷里的 `fact_name` 仍是 `session_message`——**名字是合约声明的，
    事实名只是被登记下来**。两个名字都写成字面量（不 import adapter 的 helper 当
    判定依据），否则判据会与被测实现循环论证。
    `expected_suffix` 供**反证分支**用：合约声明不唯一时交付物回落到事实名。
    """
    assert "manifest.frozen" in reads.types
    assert reads.tasks and all(task["status"] for task in reads.tasks)
    session_artifact = next(
        (item for item in reads.artifacts if str(item["id"]).endswith(expected_suffix)),
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
    assert mapped["fact_name"] == "session_message", mapped
    assert mapped["contract_id"] == "console_demo_deliverable", mapped
    # 声明恰一个 ⇒ 用该名；声明不唯一 ⇒ `declared_artifact` 为 None（回落到事实名）
    expected_declared = None if expected_suffix == ":session_message" else "analysis_report"
    assert mapped["declared_artifact"] == expected_declared, (mapped, expected_suffix)


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


def _assert_deliverable_landed(reads: _ChainReads) -> None:
    """段 4 的前半：交付物经既有登记链落 canonical（两个分支共用）。

    "carries no structured output"出现即说明登记链被跳过了——这条在**两个分支**上
    都必须为假，否则「判拒」可能来自登记链被跳过而不是来自验收门。
    """
    assert reads.evidence, "canonical evidence is empty: the deliverable never landed"
    assert reads.artifacts, "canonical artifacts are empty: the deliverable never landed"
    assert not any("carries no structured output" in message for message in reads.failures), (
        reads.failures
    )


def _assert_deliverable_adjudicated(reads: _ChainReads) -> None:
    """段 4（声明对齐分支）：合约声明恰一个 artifact 名 ⇒ 交付物用该名 ⇒ **门 PASS**。

    这是 GOAL-010 EC-01 的主干证据：**真实 runtime**（本文件用 mock 端点离线跑同一条
    LLM 路径）的交付物**满足**声明式合约 ⇒ run 到 `SUCCEEDED`。
    GOAL-009 在本路径上观察到的是判拒（终态 `FAILED`）；**判据没有放宽**——门仍按
    字面名匹配，改变的是**交付物的键名由合约声明决定**（见 reject 分支的反证）。
    """
    _assert_deliverable_landed(reads)
    assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
    assert not reads.failures, reads.failures
    assert any(str(item["id"]).endswith(":analysis_report") for item in reads.artifacts), [
        item["id"] for item in reads.artifacts
    ]


def _assert_deliverable_rejected(reads: _ChainReads) -> None:
    """段 4（声明不对齐分支）：合约声明**两个** artifact 名 ⇒ adapter **不猜** ⇒ 门 REJECT。

    这是 EC-01 的**反证**，也是 GOAL-009 那条「判拒是链在正常工作」证据的**保留位**：
    一旦有人把「不猜」的边界去掉（改成无论声明几个都挑一个），这条立刻红。
    """
    _assert_deliverable_landed(reads)
    assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
    assert any("acceptance gate" in message for message in reads.failures), reads.failures


def test_real_runtime_offline_chain_segments(mock_relay: str) -> None:
    """四段：会话创建 / 事件映射 / 预算归账 / 制品与证据（声明对齐 ⇒ 门 PASS）。"""
    from services.api.app import create_app

    deps = _openhands_deps(mock_relay, map_tools=True)
    with TestClient(create_app(deps)) as client:
        reads = _read_chain(client, _start(client))
        _assert_session_created(deps, reads)
        _assert_events_mapped(client, reads)
    _assert_usage_attributed(deps, reads)
    _assert_deliverable_adjudicated(reads)


def test_real_runtime_offline_chain_rejects_a_non_unique_declaration(mock_relay: str) -> None:
    """反证：合约声明**两个** artifact 名时，adapter 不得猜一个名字去凑门。

    判据是**同一条链**上的相反终态（`FAILED` + 点名 acceptance gate）——
    与上面那条用例**成对**，任一条被改成迁就实现都会让另一条失去意义。
    """
    from services.api.app import create_app

    deps = _openhands_deps(mock_relay, map_tools=True)
    _declare_second_artifact(deps, "console_demo_deliverable", "review_verdict")
    with TestClient(create_app(deps)) as client:
        reads = _read_chain(client, _start(client))
        _assert_events_mapped(client, reads, expected_suffix=":session_message")
    _assert_deliverable_rejected(reads)


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
