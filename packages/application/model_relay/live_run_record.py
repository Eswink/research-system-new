"""一次真实 run 的可审计记录（GOAL-008 EC-04）。

三条原则（AGENTS.md §4 + EC-04 判定细则）：

1. **结论只有两态**（`ModelReproducibilityVerdict`）：「可重复配置」或「未验证」——
   本模块**没有**、也不接受任何「完全可复现」的表达；把底层模型说成完全可复现，
   需要先让枚举多一个成员，而那一步有独立判据把守。
2. **取不到的字段必须点名**：指纹里读不到的项进 `missing_fields`，
   **留白不等于干净**（GOAL-007 EC-01 的裁定）。
3. **skip 不是 PASS**：无凭据 ⇒ `NOT_VERIFIED` 并点名缺哪一个 `credential_ref`；
   这条记录不得出现在任何「通过」判定的位置。

输入全部是**已脱敏**的（digest / 模型标识 / 计数 / id）：本模块不接收也不回显凭据值。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.domain.enums import ModelReproducibilityVerdict
from packages.domain.run_state import ResearchRunState

#: 判「配置已被真实运行确认」所必需的指纹项：缺任一项就不能声称配置可重复。
REQUIRED_FINGERPRINT_FIELDS: tuple[str, ...] = (
    "endpoint_config_digest",
    "returned_model_identifier",
    "probe_suite_digest",
)

#: provider 是否给出**取决于 provider** 的项：缺失只登记为诚实缺口，不降级结论。
PROVIDER_FINGERPRINT_FIELDS: tuple[str, ...] = (
    "system_fingerprint",
    "safe_response_metadata",
)

_EPSILON = frozenset({None, "", ()})


@dataclass(frozen=True, slots=True)
class LiveRunRecord:
    """一次 live run（或其如实 skip）的脱敏记录。"""

    run_id: str
    terminal_state: str
    verdict: ModelReproducibilityVerdict
    endpoint_config_digest: str | None = None
    returned_model_identifier: str | None = None
    system_fingerprint: str | None = None
    probe_suite_digest: str | None = None
    safe_response_metadata: tuple[tuple[str, str], ...] = ()
    missing_fields: tuple[str, ...] = ()
    model_tokens: int = 0
    usage_entries: int = 0
    artifact_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must not be empty")
        if not self.terminal_state:
            raise ValueError("terminal_state must not be empty")
        if self.verdict is ModelReproducibilityVerdict.NOT_VERIFIED and not self.reason:
            raise ValueError("NOT_VERIFIED must name a reason (skip is not a pass)")
        if self.model_tokens < 0 or self.usage_entries < 0:
            raise ValueError("usage counters must not be negative")

    @property
    def is_verified(self) -> bool:
        """结论是否为「已被真实运行确认的配置」。`NOT_VERIFIED` **不是** PASS。"""
        return self.verdict is ModelReproducibilityVerdict.REPEATABLE_CONFIGURATION

    @property
    def reached_terminal_state(self) -> bool:
        return self.terminal_state in ResearchRunState.terminal()

    def to_payload(self) -> dict[str, object]:
        """可写入证据 / manifest 的脱敏 dict。"""
        return {
            "run_id": self.run_id,
            "terminal_state": self.terminal_state,
            "verdict": self.verdict.value,
            "endpoint_config_digest": self.endpoint_config_digest,
            "returned_model_identifier": self.returned_model_identifier,
            "system_fingerprint": self.system_fingerprint,
            "probe_suite_digest": self.probe_suite_digest,
            "safe_response_metadata": dict(self.safe_response_metadata),
            "missing_fields": list(self.missing_fields),
            "model_tokens": self.model_tokens,
            "usage_entries": self.usage_entries,
            "artifact_ids": list(self.artifact_ids),
            "evidence_ids": list(self.evidence_ids),
            "reason": self.reason,
        }


def build_live_run_record(  # noqa: PLR0913 - 指纹/usage/id 是封闭字段集，包装对象只会复刻记录本身
    *,
    run_id: str,
    terminal_state: str,
    endpoint_config_digest: str | None,
    returned_model_identifier: str | None,
    probe_suite_digest: str | None,
    system_fingerprint: str | None = None,
    safe_response_metadata: tuple[tuple[str, str], ...] = (),
    model_tokens: int = 0,
    usage_entries: int = 0,
    artifact_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
) -> LiveRunRecord:
    """从一次真实 run 的已脱敏事实构建记录并判结论。

    结论规则（写死，避免实施时漂移）：

    - 终止状态 + **必填指纹项齐全** ⇒ `REPEATABLE_CONFIGURATION`；
    - 必填项缺任一项，或 run 未到终止状态 ⇒ `NOT_VERIFIED`（并点名缺的项）。

    `system_fingerprint` / 白名单响应头**缺失不降级**结论——它们取决于 provider
    是否给出，属「如实的缺口」，登记在 `missing_fields` 里。
    """
    fingerprint = _fingerprint_facts(
        endpoint_config_digest,
        returned_model_identifier,
        probe_suite_digest,
        system_fingerprint,
        safe_response_metadata,
    )
    missing = tuple(name for name, value in fingerprint.items() if value in _EPSILON)
    verdict, reason = _assess(terminal_state, missing)
    return LiveRunRecord(
        run_id=run_id,
        terminal_state=terminal_state,
        verdict=verdict,
        endpoint_config_digest=endpoint_config_digest,
        returned_model_identifier=returned_model_identifier,
        system_fingerprint=system_fingerprint,
        probe_suite_digest=probe_suite_digest,
        safe_response_metadata=safe_response_metadata,
        missing_fields=missing,
        model_tokens=model_tokens,
        usage_entries=usage_entries,
        artifact_ids=artifact_ids,
        evidence_ids=evidence_ids,
        reason=reason,
    )


def _fingerprint_facts(
    endpoint_config_digest: str | None,
    returned_model_identifier: str | None,
    probe_suite_digest: str | None,
    system_fingerprint: str | None,
    safe_response_metadata: tuple[tuple[str, str], ...],
) -> dict[str, object]:
    return {
        "endpoint_config_digest": endpoint_config_digest,
        "returned_model_identifier": returned_model_identifier,
        "probe_suite_digest": probe_suite_digest,
        "system_fingerprint": system_fingerprint,
        "safe_response_metadata": safe_response_metadata,
    }


def _assess(
    terminal_state: str,
    missing: tuple[str, ...],
) -> tuple[ModelReproducibilityVerdict, str | None]:
    """判定结论与（降级时的）理由：理由必须**点名**缺了什么。"""
    required_missing = tuple(name for name in missing if name in REQUIRED_FINGERPRINT_FIELDS)
    terminal = terminal_state in ResearchRunState.terminal()
    if not required_missing and terminal:
        return ModelReproducibilityVerdict.REPEATABLE_CONFIGURATION, None
    reasons = []
    if not terminal:
        reasons.append(f"run state {terminal_state!r} is not terminal")
    if required_missing:
        reasons.append(f"missing fingerprint fields: {', '.join(required_missing)}")
    return ModelReproducibilityVerdict.NOT_VERIFIED, "; ".join(reasons)


def not_verified_live_run_record(
    *,
    run_id: str,
    reason: str,
    credential_ref: str | None = None,
    terminal_state: str | None = None,
) -> LiveRunRecord:
    """如实 skip 的记录：**没有**发生真实 run 时用它。

    `reason` 至少要能回答「为什么没跑」；给不出 `credential_ref` 时点名它——
    「缺凭据」不是一个解释，**缺哪个凭据**才是。
    """
    if not reason:
        raise ValueError("a skip record must name why the run did not happen")
    detail = reason if credential_ref is None else f"{reason} (credential_ref={credential_ref})"
    return LiveRunRecord(
        run_id=run_id,
        terminal_state=terminal_state or ResearchRunState.State.DRAFT,
        verdict=ModelReproducibilityVerdict.NOT_VERIFIED,
        missing_fields=REQUIRED_FINGERPRINT_FIELDS + PROVIDER_FINGERPRINT_FIELDS,
        reason=detail,
    )


__all__ = [
    "PROVIDER_FINGERPRINT_FIELDS",
    "REQUIRED_FINGERPRINT_FIELDS",
    "LiveRunRecord",
    "build_live_run_record",
    "not_verified_live_run_record",
]
