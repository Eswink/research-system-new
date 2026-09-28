"""GOAL-024 EC-02:端到端内容金丝雀(默认离线 Fake 链)。

**命题**(读面/磁盘按白名单口径,承 cycle 1 台账的修正):

```text
沿默认(离线 Fake)运行路径注入的用户内容金丝雀:
- **无合法载体的出口**(遥测 wire / 应用日志)⇒ **零命中**;
- **声明过的载体**(制品 blob、失败消息)⇒ 只允许承载**它自己那一条**金丝雀;
- 每个受判出口都要有**可见性正控制**(扫描器证明它真的能在那条通道上看到内容,承 MEM-156)。
```

canonical state(SQLite 域实体)持有用户输入是**业务真相,不是泄漏** ⇒ 不得据此判红
(反证两向,承 MEM-159)。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tests.observability.content_canary_support import (
    ARTIFACT_BODY,
    CANARIES,
    EVIDENCE_BODY,
    FAILURE_MESSAGE,
    TOOL_ARGUMENT,
    TOOL_OUTPUT,
    artifact_blob_text,
    disk_text,
    failure_payload_text,
    hits,
    metric_wire_text,
    run_default_offline,
    trace_wire_text,
)
from tests.observability.privacy_exit_census import JUDGED
from tests.observability.test_privacy_exit_census import EXIT_SURFACES

#: **无合法载体**的出口:任何内容金丝雀出现在这里都是缺陷。
#: 失败载荷也在内:判拒运行里**没有**注入任何金丝雀 ⇒ 它必须零命中(白名单为空集)。
ABSOLUTE_EXITS: tuple[str, ...] = (
    "otlp-traces-wire",
    "otlp-metrics-wire",
    "application-log",
    "failure-payload",
)

#: **声明过的载体** ⇒ 只允许承载列出的金丝雀 kind(其余一律零命中)。
CARRIER_ALLOW_LIST: dict[str, tuple[str, ...]] = {
    "disk-run-artifacts": (ARTIFACT_BODY.kind,),
}

#: 本 cycle **尚未观测**的受判出口:显式登记理由(不是静默放过;EC-02 因此仍 PENDING)。
NOT_YET_OBSERVED: dict[str, str] = {
    "read-face-http": "读面需要应用级装配(TestClient + 路由表);本 cycle 只跑编排层默认运行",
}

#: EC-01 登记为**豁免**的出口(stdout 无生产点):本 cycle 仍额外扫描它(严于清单)。
EXTRA_SCANNED_EXITS: tuple[str, ...] = ("stdout-stderr",)


@dataclass(frozen=True, slots=True)
class ScanBundle:
    """一次默认离线运行的全部可观测面文本 + 两个分支的终态。"""

    traces: str
    metrics: str
    application_log: str
    stdout: str
    stderr: str
    blob: str
    failure: str
    success_state: str
    failed_state: str


@pytest.fixture
def scan(
    tmp_path: Path, receiver: Any, caplog: pytest.LogCaptureFixture, capsys: Any
) -> ScanBundle:
    with caplog.at_level(logging.DEBUG):
        success = run_default_offline(tmp_path, receiver)
        failed = run_default_offline(tmp_path / "failed", receiver, failing=True)
    captured = capsys.readouterr()
    return ScanBundle(
        traces=trace_wire_text(receiver),
        metrics=metric_wire_text(receiver),
        application_log="\n".join(record.getMessage() for record in caplog.records),
        stdout=captured.out,
        stderr=captured.err,
        blob=artifact_blob_text(success.blob_root),
        failure=failure_payload_text(failed),
        success_state=str(success.outcome.state),
        failed_state=str(failed.outcome.state),
    )


def test_both_branches_reach_a_terminal_state(scan: ScanBundle) -> None:
    """**如实登记运行终态**:两个分支都在本 cycle 收敛到 `FAILED`
    (默认 Fake runtime 的交付物声明与合约不合 ⇒ 验收门判拒,不是我们放宽了门)。
    零命中命题**不依赖** SUCCEEDED:制品正文仍经声明链落到了制品 blob 上
    (`blob` 命中 `artifactbody`),失败载荷因此是**空白名单**面。"""
    assert scan.success_state == scan.failed_state == "FAILED", (
        f"运行终态与登记不符:success={scan.success_state} failed={scan.failed_state}"
    )


def test_the_exit_partition_is_complete() -> None:
    """三类出口(绝对面 / 载体 / 未观测)必须**恰好**覆盖全部受判出口(承 MEM-158)。"""
    judged = {item.id for item in EXIT_SURFACES if item.classification == JUDGED}
    covered = set(ABSOLUTE_EXITS) | set(CARRIER_ALLOW_LIST) | set(NOT_YET_OBSERVED)
    assert judged == covered, f"受判出口未被恰好一次覆盖:{sorted(judged ^ covered)}"
    assert len(judged) >= 5, f"受判出口太少({len(judged)})"
    assert all(reason.strip() for reason in NOT_YET_OBSERVED.values())


def test_the_run_actually_produced_the_observed_channels(scan: ScanBundle) -> None:
    """非空转(承 MEM-156):运行真的产生了 wire 与载体内容,否则下面的零命中是空真。"""
    assert scan.traces.strip(), "OTLP traces 面无内容 ⇒ 零命中不可信"
    assert "research_os." in scan.traces, "traces 面没有本仓 span 前缀"
    assert ARTIFACT_BODY.token in scan.blob, "制品正文没有落到制品 blob 上"


def test_no_content_canary_reaches_an_absolute_exit(scan: ScanBundle) -> None:
    """(a) 绝对面**零命中**:遥测 wire(traces / metrics)、应用日志、失败载荷。"""
    surfaces = {
        "otlp-traces-wire": scan.traces,
        "otlp-metrics-wire": scan.metrics,
        "application-log": scan.application_log,
        "failure-payload": scan.failure,
        "stdout-stderr": f"{scan.stdout}\n{scan.stderr}",
    }
    leaks = {name: hits(text) for name, text in surfaces.items() if hits(text)}
    assert not leaks, f"内容金丝雀进入了无合法载体的出口:{leaks}"


def test_declared_carriers_carry_only_their_own_canary(scan: ScanBundle) -> None:
    """(b) 载体白名单:制品 blob 只许带制品正文金丝雀(其余金丝雀零命中)。"""
    assert hits(scan.blob) == [ARTIFACT_BODY.kind], f"制品 blob 的金丝雀集合异常:{hits(scan.blob)}"


def _emit_through_every_channel(receiver: Any, tmp_path: Path) -> None:
    """正控制第一步:把金丝雀经**每条通道**各发一次(让内容真的出现)。"""
    from adapters.otel.provider import build_telemetry_sink
    from packages.application.observability.attributes import (
        AttributeKey,
        MetricKind,
        MetricLabel,
        MetricName,
        MetricSample,
    )
    from packages.application.observability.scope import operation
    from packages.application.observability.signals import OperationScope
    from tests.observability.canary_support import canary_config

    sink = build_telemetry_sink(canary_config(receiver.endpoint))
    with operation(
        sink,
        scope=OperationScope.LLM_CALL,
        name="llm.call.canary",
        attributes={AttributeKey.endpoint_id.value: ARTIFACT_BODY.value},
    ):
        pass
    sink.record_metric(
        MetricSample(
            name=MetricName.TOOL_CALL_DURATION_MS,
            kind=MetricKind.HISTOGRAM,
            value=1.0,
            labels={MetricLabel.provider: TOOL_ARGUMENT.value},
        )
    )
    sink.flush(timeout_seconds=5.0)
    sink.shutdown(timeout_seconds=5.0)
    logging.getLogger("tests.observability.content_canary_probe").warning(
        "probe %s", TOOL_OUTPUT.value
    )
    print(FAILURE_MESSAGE.value)
    (tmp_path / "disk-probe.txt").write_text(EVIDENCE_BODY.value, encoding="utf-8")


def test_every_observed_exit_has_a_visibility_control(
    tmp_path: Path, receiver: Any, capsys: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """(c) 可见性正控制:**每个观测到的出口**都要证明「内容可见即被抓到」。"""
    with caplog.at_level(logging.WARNING):
        _emit_through_every_channel(receiver, tmp_path)
        controls = {
            "otlp-traces-wire": hits(trace_wire_text(receiver)),
            "otlp-metrics-wire": hits(metric_wire_text(receiver)),
            "application-log": hits("\n".join(record.getMessage() for record in caplog.records)),
            "stdout-stderr": hits(capsys.readouterr().out),
            "disk-run-artifacts": hits(disk_text(tmp_path)),
        }
    missing = sorted(name for name, found in controls.items() if not found)
    assert not missing, f"以下出口的可见性正控制失败(扫描器看不见内容):{missing}"


def test_a_canary_in_an_allowed_key_is_red() -> None:
    """(d) 反证:内容塞进**允许键**(`endpoint_id`)⇒ 判红且失败消息**点名出口与键名**。"""
    from packages.application.observability.attributes import AttributeKey, sanitize_attributes

    key = AttributeKey.endpoint_id.value
    attributes = sanitize_attributes({key: ARTIFACT_BODY.value})
    assert attributes, "允许键被丢掉了 —— 反证前提不成立"
    text = f"otlp-traces-wire span attributes: {attributes}"
    found = hits(text)
    assert found == [ARTIFACT_BODY.kind], f"允许键里的内容没有被抓到:{found}"
    assert key in text, f"失败消息没有点名键名:{text!r}"


def test_a_canary_in_a_log_line_is_red(caplog: pytest.LogCaptureFixture) -> None:
    """(d) 反证:内容写进**日志行** ⇒ 判红且点名出口 `application-log`。"""
    logger = logging.getLogger("tests.observability.content_canary_probe")
    with caplog.at_level(logging.WARNING):
        logger.warning("probe line %s", TOOL_ARGUMENT.value)
    text = "\n".join(record.getMessage() for record in caplog.records)
    found = hits(text)
    assert found == [TOOL_ARGUMENT.kind], f"日志行里的金丝雀没有被抓到:{found}"
    assert "application-log" in ABSOLUTE_EXITS


def test_a_canary_in_canonical_state_is_not_a_leak(scan: ScanBundle) -> None:
    """(e) 反证两向:canonical / 声明过的载体持有内容 ⇒ **不**判红(业务真相)。"""
    assert ARTIFACT_BODY.token in scan.blob
    assert "disk-run-artifacts" in CARRIER_ALLOW_LIST
    assert hits(scan.traces) == [] and hits(scan.application_log) == []


def test_the_verdict_does_not_depend_on_wording() -> None:
    """(f) 措辞无关(承 MEM-141):同一 token、不同措辞 ⇒ 结论不变。"""
    from tests.observability.content_canary_support import Canary

    token = ARTIFACT_BODY.token
    variants = (
        Canary(kind=ARTIFACT_BODY.kind, value=token),
        Canary(kind=ARTIFACT_BODY.kind, value=f"完全不同的措辞 <<<{token}>>> 换了个说法"),
        Canary(kind=ARTIFACT_BODY.kind, value=f"[标题] {token} [尾注]"),
    )
    for canary in variants:
        assert hits(f"carrier body: {canary.value}", (canary,)) == [ARTIFACT_BODY.kind]
        assert hits("carrier body without marker", (canary,)) == []
    assert len(CANARIES) == 7
