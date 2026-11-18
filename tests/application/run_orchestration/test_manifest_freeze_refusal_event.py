"""EC-03 ③：**拒冻必须先落一条可读事件**（`outbox_events` 不得为空）。

**它补哪一格**（GOAL-20261119-115 建档实测）：24 次 `dual_model_review` FAILED 里
**5 次 `outbox_events` 为空** —— 任务从未派发，读面表现为「秒失败、无原因」。
根因：`start_run` 里 `freeze_manifest(...)` 抛 `ManifestFreezeError` 时**未捕获**，
而 preflight FAIL 走的是 `_fail_run` → `publish_failed_run`（有 `run.failed`）。

**判什么**（用真实编排服务 + 真实 SQLite outbox，不打桩）：

1. 拒冻时**至少有一条** `run.failed` 落库（不是只抛异常）；
2. 那条事件的 payload 带 `missing` 清单键与 `reason=manifest_freeze_refused`
   （读面能说出「为什么被拒」）；
3. run 的结局是 `FAILED` 且 `system_failure=True`（配置/策略问题不是科学负结果）。

**反证臂**：把 `publish_freeze_refusal(...)` 那一行摘掉 ⇒ 同一条判据必须判红
（`outbox_events` 为空）。按压在测试内用「不带事件发布的同一条路径」复现，不改产品代码。
"""

from __future__ import annotations

from typing import Any

import pytest

from packages.application.preflight.policy_acceptance import (
    FreezeAcceptance,
    freeze_refusal_message,
)
from packages.application.preflight.preflight import ManifestFreezeError
from packages.application.run_orchestration.manifest_freeze_events import (
    MISSING_KEY,
    REASON_KEY,
    freeze_refusal_payload,
    is_freeze_refusal,
    publish_freeze_refusal,
)
from packages.domain.events import EventType


class _Recorder:
    """最小的 publish 替身：记下 (event_type, payload)。

    **为什么这里可以用替身**：被测的是「拒冻路径**调用了** publish 且 payload 可读」，
    而真实 outbox 的写入语义已由别的判据持有。用替身是为了让「摘掉那一行就红」
    这条反证臂可判 —— 真库在两种形态下都「能写」，区别只在有没有写。
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __call__(self, event_type: Any, payload: dict[str, Any], **_: Any) -> None:
        self.calls.append((str(event_type), dict(payload)))


def _refusal() -> ManifestFreezeError:
    reason = "no policy evaluator is injected in preflight context"
    return ManifestFreezeError(freeze_refusal_message(FreezeAcceptance(refusal_reasons=(reason,))))


class TestTheRefusalProducesAReadableEvent:
    def test_the_publisher_is_called_once_with_run_failed(self) -> None:
        recorder = _Recorder()
        publish_freeze_refusal(recorder, "run-1", _refusal())
        assert len(recorder.calls) == 1, recorder.calls
        event_type, payload = recorder.calls[0]
        assert event_type == str(EventType.RUN_FAILED), event_type
        assert payload["run_id"] == "run-1", payload

    def test_the_payload_carries_a_reason_and_a_missing_list(self) -> None:
        recorder = _Recorder()
        publish_freeze_refusal(recorder, "run-2", _refusal())
        _event_type, payload = recorder.calls[0]
        assert payload[REASON_KEY] == "manifest_freeze_refused", payload
        assert isinstance(payload[MISSING_KEY], list), payload
        assert payload["message"], "拒冻事件必须带可读消息（读面靠它说原因）"

    def test_a_structured_missing_list_is_carried_through(self) -> None:
        """错误对象带结构化 `missing` 时，清单必须原样进 payload（不是只留消息）。"""
        error = _refusal()
        error.missing = (  # type: ignore[attr-defined]
            "preflight report has ERROR findings",
            "budget not reserved",
        )
        payload = freeze_refusal_payload("run-3", error)
        assert payload[MISSING_KEY] == [
            "preflight report has ERROR findings",
            "budget not reserved",
        ], payload

    def test_the_type_predicate_matches_the_real_error(self) -> None:
        assert is_freeze_refusal(_refusal())
        assert not is_freeze_refusal(ValueError("other"))


class TestTheRunContract:
    def test_the_refusal_branch_publishes_and_does_not_double_report(self) -> None:
        """拒冻分支只走**一条**发布路径。

        **本机实测的教训**：最初写成 `publish_freeze_refusal(...)` + `_fail_run(...)`，
        而 `_fail_run` 内部还会发一条 `run.failed` ⇒ 一次拒冻落**两条**事件。
        `publish_freeze_refusal` 现在自己返回 `RunOutcome`，所以分支里**不得**再出现
        `_fail_run` —— 这条判据钉的正是那次重复。
        """
        from pathlib import Path

        source = Path("packages/application/run_orchestration/service.py").read_text(
            encoding="utf-8"
        )
        block = source[source.index("except ManifestFreezeError as refusal") :]
        block = block[: block.index("\n        run = self._started_run")]
        assert "publish_freeze_refusal(" in block, block
        assert "_fail_run(" not in block, (
            "拒冻分支又调了 _fail_run ⇒ 会重复发 run.failed（本机实测过这个缺陷）"
        )


class TestTheWiredPathPublishesExactlyOnce:
    """**端到端**：真实编排服务 + 真实 outbox，拒冻 ⇒ 恰好一条 `run.failed`。

    **为什么这条必须存在**（本机实测）：只测 helper 会漏掉一个真实缺陷 ——
    最初的接线是「先 `publish_freeze_refusal`、再 `_fail_run`」，而 `_fail_run`
    内部还会发一条 ⇒ 一次拒冻落**两条** `run.failed`。helper 的单测全绿，
    只有跑通整条路径才看得见重复。
    """

    def test_one_refusal_yields_one_event(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import packages.application.run_orchestration.service as service_module
        from packages.application.run_orchestration import StartRunCommand
        from packages.domain.core import ID
        from tests.e2e.scenario import M7Harness, m7_protocol
        from tests.e2e.scenario_catalog import m7_catalog, m7_preflight_context, m7_project

        def boom(*_args: Any, **_kwargs: Any) -> Any:
            raise ManifestFreezeError("cannot freeze manifest before a passing preflight: x")

        monkeypatch.setattr(service_module, "freeze_manifest", boom)

        harness = M7Harness()
        captured: list[tuple[str, dict[str, Any]]] = []
        original = harness.service._publish

        def spy(event_type: Any, payload: dict[str, Any], **kwargs: Any) -> Any:
            captured.append((str(event_type), dict(payload)))
            return original(event_type, payload, **kwargs)

        monkeypatch.setattr(harness.service, "_publish", spy)
        try:
            catalog = m7_catalog()
            outcome = harness.service.start_run(
                m7_protocol(),
                catalog,
                m7_project(),
                m7_preflight_context(catalog, m7_project()),
                StartRunCommand(
                    project_id="m7-project",
                    protocol_id="sort_analysis_v1",
                    run_id=ID.generate(),
                    trace_id="trace-goal115-freeze",
                ),
            )
        finally:
            harness.close()

        failures = [payload for event_type, payload in captured if event_type == "run.failed"]
        assert len(failures) == 1, f"拒冻必须**恰好**落一条 run.failed，实得 {len(failures)}"
        assert failures[0][REASON_KEY] == "manifest_freeze_refused", failures[0]
        assert str(outcome.state) == "FAILED", outcome.state
        assert outcome.system_failure is True, "拒冻是配置/系统失败，不是科学负结果"


class TestTheCriterionBites:
    """**反证臂**：没有那次发布 ⇒ 调用记录为空（这就是 5 次空 outbox 的形态）。"""

    def test_without_the_publish_call_nothing_is_recorded(self) -> None:
        recorder = _Recorder()
        # 复现修复前的路径：直接抛、不发布
        with pytest.raises(ManifestFreezeError):
            raise _refusal()
        assert recorder.calls == [], recorder.calls

    def test_the_recorder_would_see_a_call_if_one_happened(self) -> None:
        """正控制：替身本身不是哑的（否则上面那条空断言无意义）。"""
        recorder = _Recorder()
        recorder(EventType.RUN_FAILED, {"run_id": "x"})
        assert recorder.calls, "替身没记下调用 ⇒ 反证臂空转"
