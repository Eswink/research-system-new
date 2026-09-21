"""run 的运行时指纹事实：收集观测 + 终止时落 canonical（GOAL-010 EC-04）。

定案（PLAN-20260921-130 WP1 记录）：「返回 model 名」与「兼容性结论」**只在一次真实
调用之后**才存在，而 manifest 冻结在**调用之前** —— 所以「读面能看见四要素」只能靠
调用后再落一条 canonical 事实。这里把它落在**既有事件链**上：`MODEL_PROBED`
（`packages/domain/events.py` 早已声明、此前无人发出）。

四要素的来源逐条写死（**不新造判据**）：

- **返回 model 名** ← 本次 run 的**会话观测**（`RunSessionObservation`：provider 侧
  usage 度量报告的 model 名），恰一个不同值才写单值槽位；
- **端点头** ← 这些会话**实际用到的**端点的配置 digest（多端点 ⇒ 单值槽位表达不了 ⇒ 缺项）；
- **probe 版本** ← 本 build 钉住的 probe 套件 digest。它是**版本**事实，不是「本 run 跑过
  probe」的执行证据 —— 本模块**不发起任何调用**；
- **兼容性结论** ← `build_live_run_record` 的既有两态规则（`REPEATABLE_CONFIGURATION` /
  `NOT_VERIFIED`）。读面只呈现它，不另判。

三条诚实边界：

1. **没有观测 ⇒ 不发事件**：读面保持冻结占位。「没观测到」不是「无漂移」（AGENTS.md §4）。
2. **单值槽位不替多值做主**：观测到多个不同 model 名时单值留 `None`（缺项 ⇒ 结论必为
   `NOT_VERIFIED`），**不挑一个**；多值本身随 `observed_model_identifiers` 原样带上，
   藏起来等于把「观测到不一致」读成「没观测到」。
3. **不写没测过的数**：记录里的 usage/制品计数器（`model_tokens` / `usage_entries` /
   `artifact_ids` / `evidence_ids`）本层拿不到真值，它们的默认 0/空**不**随事件发布 ——
   发一份带 0 的记录等于把一个没测过的数写成实测值（usage 的真值面是 cost/usage 读面）。
   这是对「payload = `record.to_payload()`」的**有界偏离**，只减不增、且逐键列在这里。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from packages.application.model_relay.fingerprint import probe_suite_digest
from packages.application.model_relay.live_run_record import build_live_run_record
from packages.application.model_relay.observation import RunSessionObservation
from packages.application.model_relay.suite import default_probe_suite
from packages.application.run_orchestration.eventing import EventSink, EventTarget, publish_event
from packages.domain.events import EventType

#: 不随指纹事件发布的记录键（见模块 docstring 第 3 条边界）。
_UNPUBLISHED_RECORD_KEYS = frozenset({
    "model_tokens",
    "usage_entries",
    "artifact_ids",
    "evidence_ids",
})


def _single(values: Iterable[str | None]) -> str | None:
    """恰一个不同值 ⇒ 该值；零个或多个 ⇒ `None`（单值槽位表达不了，**不挑一个**）。"""
    distinct = {value for value in values if value}
    return distinct.pop() if len(distinct) == 1 else None


def runtime_fingerprint_payload(
    *,
    run_id: str,
    terminal_state: str,
    observations: tuple[RunSessionObservation, ...],
) -> dict[str, object] | None:
    """观测 → `MODEL_PROBED` payload；**没有观测 ⇒ `None`**（不发事件）。"""
    if not observations:
        return None
    observed = tuple(
        sorted({name for item in observations for name in item.observed_model_identifiers})
    )
    record = build_live_run_record(
        run_id=run_id,
        terminal_state=terminal_state,
        endpoint_config_digest=_single(item.endpoint_config_digest for item in observations),
        returned_model_identifier=_single(observed),
        probe_suite_digest=str(probe_suite_digest(default_probe_suite())),
    )
    payload = {
        key: value
        for key, value in record.to_payload().items()
        if key not in _UNPUBLISHED_RECORD_KEYS
    }
    payload["observed_model_identifiers"] = list(observed)
    return payload


@dataclass(slots=True)
class RuntimeFingerprintCollector:
    """一次执行期间的会话观测收集器；`_execute_with_context` 建一个、用完即弃。

    收集范围**就是这次执行**：collector 随调用建立，不挂在 service 实例上 ——
    同一条 run 的续跑、以及同一进程里的别的 run，都不会串到这次的观测里。
    """

    observations: list[RunSessionObservation] = field(default_factory=list)

    def observe(self, observation: RunSessionObservation) -> None:
        """phase_runner 交回一次会话观测（没有观测时它**不会**调用这里）。"""
        self.observations.append(observation)

    def publish(self, sink: EventSink, run_id: str, trace_id: str, terminal_state: str) -> bool:
        """把这次执行攒下的观测落成 `MODEL_PROBED`；**没有观测 ⇒ 什么都没发**（返回 False）。"""
        payload = runtime_fingerprint_payload(
            run_id=run_id,
            terminal_state=terminal_state,
            observations=tuple(self.observations),
        )
        if payload is None:
            return False
        publish_event(
            sink,
            EventType.MODEL_PROBED,
            payload,
            EventTarget(run_id=run_id, trace_id=trace_id),
        )
        return True


__all__ = ["RuntimeFingerprintCollector", "runtime_fingerprint_payload"]
