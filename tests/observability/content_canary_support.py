"""GOAL-024 EC-02 支撑面:合成内容金丝雀 + 默认离线运行 + 逐出口扫描。

三件事:

1. **合成金丝雀**(per-import 随机后缀):任务输入 / prompt / 工具参数 / 工具输出 /
   制品正文 / 证据正文 / 失败消息。**一律测试内构造**,绝不携带真实内容。
2. **默认离线运行**:Fake runtime + SQLite 域存储 + 真实 OTLP sink(只发 **loopback**
   测试接收器)+ 制品 blob 指向**临时根**(不写仓库)。
3. **逐出口扫描**:把每个受判出口的可观测文本取出来,变成 `{出口 id: 文本}`;
   扫描是**纯函数**(文本 × 金丝雀 → 命中),便于反证与措辞对照。

**读面/磁盘口径(白名单)**:`GET /artifacts/{id}/content`、制品 blob、run 事件里的失败消息
**契约本来就是**返回/保存用户内容(业务真相)⇒ 它们是**声明过的载体**;受判命题是
「内容只出现在声明过的载体上,其余出口零命中」(承 MEM-158)。
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from adapters.otel.provider import build_telemetry_sink
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.db import connect
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.run_orchestration import (
    OrchestrationDependencies,
    RunOrchestrationService,
    StartRunCommand,
)
from packages.domain.core import ID
from tests.e2e.scenario import StructuredOutputAgentRuntime, m7_protocol
from tests.e2e.scenario_catalog import m7_catalog, m7_preflight_context, m7_project
from tests.observability.canary_support import canary_config

_RUN = uuid.uuid4().hex[:10]


@dataclass(frozen=True, slots=True)
class Canary:
    """一个合成内容金丝雀;**核心 token** 用于扫描(不被合法改写的前后缀)。"""

    kind: str
    value: str

    @property
    def token(self) -> str:
        return f"Z9{self.kind.upper()}{_RUN}"


def _canary(kind: str, template: str = "{token} content") -> Canary:
    return Canary(kind=kind, value=template.format(token=f"Z9{kind.upper()}{_RUN}"))


TASK_INPUT = _canary("taskinput", "TASK[{token}]")
PROMPT_TEXT = _canary("prompt", "PROMPT[{token}]")
TOOL_ARGUMENT = _canary("toolarg", "TOOLARG[{token}]")
TOOL_OUTPUT = _canary("tooloutput", "TOOLOUT[{token}]")
ARTIFACT_BODY = _canary("artifactbody", "ARTIFACT[{token}]")
EVIDENCE_BODY = _canary("evidencebody", "EVIDENCE[{token}]")
FAILURE_MESSAGE = _canary("failuremessage", "FAILURE[{token}]")

CANARIES: tuple[Canary, ...] = (
    TASK_INPUT,
    PROMPT_TEXT,
    TOOL_ARGUMENT,
    TOOL_OUTPUT,
    ARTIFACT_BODY,
    EVIDENCE_BODY,
    FAILURE_MESSAGE,
)


class FailingRuntime(StructuredOutputAgentRuntime):
    """会话产出**空**结构化输出 ⇒ 验收门判拒(不注入任何金丝雀,失败载荷应零命中)。"""


@dataclass(slots=True)
class OfflineRun:
    """一次默认离线运行的**可观测面**。"""

    outcome: Any
    blob_root: Path
    artifacts: Any
    events: Any
    connection: Any
    sink: Any
    failed_run: bool = False


def _dependencies(tmp_root: Path, sink: Any, runtime: Any) -> tuple[OrchestrationDependencies, Any]:
    connection = connect(":memory:")
    artifacts = SqliteArtifactStore(connection=connection, blob_dir=tmp_root / "artifact-blobs")
    events = SqliteOutboxEventPublisher(connection=connection)
    deps = OrchestrationDependencies(
        runtime=runtime,
        workflow=SqliteWorkflowEngine(connection=connection, lease_ttl_seconds=60),
        artifacts=artifacts,
        events=events,
        budget=FakeBudgetLedger(),
        ledger=FakeEvidenceLedger(),
        telemetry=sink,
    )
    return deps, connection


def run_default_offline(tmp_root: Path, receiver: Any, *, failing: bool = False) -> OfflineRun:
    """跑一次默认(离线 Fake)运行;失败分支用于观察失败载荷。"""
    sink = build_telemetry_sink(canary_config(receiver.endpoint))
    runtime = (
        FailingRuntime(structured_output={})
        if failing
        else StructuredOutputAgentRuntime(
            structured_output={
                "analysis_report": {"text": ARTIFACT_BODY.value},
                "review_decision": {"verdict": "PASS", "score": 0.95},
            }
        )
    )
    deps, connection = _dependencies(tmp_root, sink, runtime)
    service = RunOrchestrationService(deps)
    outcome = service.start_run(
        m7_protocol(),
        m7_catalog(),
        m7_project(),
        m7_preflight_context(m7_catalog(), m7_project()),
        StartRunCommand(
            project_id="m7-project",
            protocol_id="sort_analysis_v1",
            run_id=ID.generate(),
            trace_id=f"trace-canary-{'fail' if failing else 'ok'}",
            idempotency_key=f"run-canary-{'fail' if failing else 'ok'}",
        ),
    )
    sink.flush(timeout_seconds=5.0)
    sink.shutdown(timeout_seconds=5.0)
    return OfflineRun(
        outcome=outcome,
        blob_root=tmp_root / "artifact-blobs",
        artifacts=deps.artifacts,
        events=deps.events,
        connection=connection,
        sink=sink,
        failed_run=failing,
    )


def artifact_store_of(deps: OrchestrationDependencies) -> SqliteArtifactStore:
    store = deps.artifacts
    assert isinstance(store, SqliteArtifactStore)
    return store


def trace_wire_text(receiver: Any) -> str:
    """OTLP `/v1/traces` 的原始 wire bytes + 解码后的 span 文本。"""
    from tests.observability.canary_support import decoded_span_text

    payloads = b"\n".join(receiver.payloads)
    return "\n".join([payloads.decode("utf-8", errors="ignore"), decoded_span_text(receiver)])


def metric_wire_text(receiver: Any) -> str:
    """OTLP `/v1/metrics` 的原始 wire bytes + 解码后的 data point 文本。

    接收器不按信号分桶保存原始字节 ⇒ 这里用**全部** payload(保守:更严,不会漏扫)。
    """
    from tests.observability.canary_support import decoded_metric_text

    payloads = b"\n".join(receiver.payloads)
    return "\n".join([payloads.decode("utf-8", errors="ignore"), decoded_metric_text(receiver)])


def disk_text(root: Path) -> str:
    """临时制品根下**所有**文件的原始内容(二进制读)。"""
    if not root.exists():
        return ""
    chunks: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            chunks.append(path.read_bytes().decode("utf-8", errors="ignore"))
    return "\n".join(chunks)


def artifact_blob_text(root: Path) -> str:
    """**声明过的载体**:制品 blob(契约要求保存制品正文)。"""
    return disk_text(root)


def failure_payload_text(run: OfflineRun) -> str:
    """失败载荷面:运行结果消息 + outbox 事件载荷(含失败消息)。"""
    payloads = [str(getattr(run.outcome, "message", "") or "")]
    for record in getattr(run.events, "published", []):
        payloads.append(str(record))
    return "\n".join(payloads)


def hits(text: str, canaries: Iterable[Canary] = CANARIES) -> list[str]:
    """扫描:返回命中的金丝雀 kind(纯函数,便于反证与措辞对照)。"""
    return sorted(canary.kind for canary in canaries if canary.token in text)


def iter_hit_details(text: str, canaries: Iterable[Canary] = CANARIES) -> Iterator[tuple[str, str]]:
    """命中的 (kind, token) —— 失败消息据此**点名出口与金丝雀**。"""
    for canary in canaries:
        if canary.token in text:
            yield canary.kind, canary.token
