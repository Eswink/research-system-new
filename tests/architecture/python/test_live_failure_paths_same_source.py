"""失败路径语义的同源判据（GOAL-009 EC-04 / PLAN-20260920-124）。

`docs/integration/LIVE_MODEL_RUNBOOK.md` §7 把三类失败情形（无效凭据 / 端点拒绝 /
模型不存在）的**期望**写成一张固定标签表。本判据做两件事：

1. **把能离线判的语义钉住**——尤其是**「门开 ≠ 凭据有效」**：门只问 `has()`（存在性），
   所以**非空但无效**的值也会开门。这条最容易被读成缺陷，所以必须由判据写下来，
   并与「空值 ⇒ 关门」成对断言，否则「门只看存在性」这半句只是文档里的说法。
2. **核对表里每一格的「证据在哪」仍然成立**——端点拒绝那一格**指到既有套件**
   （`tests/api/test_runtime_egress_gate.py`），本判据核对那两条关键用例**仍在**、
   **没有被 skip**，而不是把「零出站」重写一遍（同一件事跑两遍是浪费）。

**不发起任何真实调用**：live 那一格由 `tests/e2e/test_live_failure_paths.py` 承担。
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest

from adapters.relay.credential_resolver import EnvCredentialResolver
from packages.application.model_relay.live_run_gate import evaluate_live_run_gate
from services.api.runtime_support import OPENHANDS_RUNTIME
from tests.contracts.fixtures import endpoint

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNBOOK = REPO_ROOT / "docs/integration/LIVE_MODEL_RUNBOOK.md"
EGRESS_GATE_SUITE = REPO_ROOT / "tests/api/test_runtime_egress_gate.py"
LLM_FACTORY = REPO_ROOT / "adapters/openhands/llm_factory.py"
SESSION_FACTORY = REPO_ROOT / "services/api/runtime_support.py"
LIVE_FAILURE_SUITE = REPO_ROOT / "tests/e2e/test_live_failure_paths.py"
LIVE_ABSENCE_SUITE = REPO_ROOT / "tests/e2e/test_live_model_absence.py"
ENDPOINTS_YAML = REPO_ROOT / "examples/config/llm_endpoints.yaml"

_CREDENTIAL_REF = "llm_main_key"
_ABSENCE_CASE_ENV = "RESEARCHOS_LIVE_MODEL_ABSENCE_CASE"
#: §7 表格的**固定标签**（解析只认标签，不猜格式）。
_LABELS = ("无效凭据", "端点拒绝", "模型不存在")


def _runbook_text() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def _section_seven() -> str:
    """§7 的正文（到下一个二级标题为止）。解析失败就点名，不返回空串。"""
    text = _runbook_text()
    start = text.find("\n## 7.")
    assert start != -1, "the runbook no longer has a §7 section"
    rest = text[start + 1 :]
    end = rest.find("\n## ", 3)
    return rest if end == -1 else rest[:end]


def _row(label: str) -> str:
    prefix = f"| {label} |"
    for line in _section_seven().splitlines():
        if line.startswith(prefix):
            return line
    raise AssertionError(f"§7 no longer has a row labelled {label!r}")


def _gate_with(resolver: object) -> object:
    return evaluate_live_run_gate(
        credentials=resolver,  # type: ignore[arg-type]
        endpoint=replace(endpoint(), credential_ref=_CREDENTIAL_REF),
        agent_runtime=OPENHANDS_RUNTIME,
        live_agent_runtime=OPENHANDS_RUNTIME,
    )


class TestTheGateAnswersPresenceNotValidity:
    """**门开 ≠ 凭据有效**：这条语义必须成对断言（无效开放 / 空即关）。"""

    def test_a_non_empty_invalid_value_opens_the_gate(self) -> None:
        """非空但明显无效的值 ⇒ `has()` 为真 ⇒ 门**开**（设计内，不是缺陷）。"""
        resolver = EnvCredentialResolver(environment={_CREDENTIAL_REF: "not-a-real-credential"})
        assert resolver.has(_CREDENTIAL_REF) is True, (
            "the resolver must answer the presence question for a non-empty value; "
            "if this changed, §7's first row and this judge are both wrong"
        )
        gate = _gate_with(resolver)
        assert gate.open is True, getattr(gate, "reason", "")  # type: ignore[attr-defined]

    def test_an_empty_value_closes_the_gate(self) -> None:
        """配对断言：变量**存在但为空** == 不可解析 ⇒ 关门。两条一起才钉住「只看存在性」。"""
        gate = _gate_with(EnvCredentialResolver(environment={_CREDENTIAL_REF: ""}))
        assert gate.open is False, "an empty value must not open the gate"  # type: ignore[attr-defined]

    def test_the_gate_never_asks_for_the_value(self) -> None:
        """门只问存在性：`resolve()` 一被调用即判红。"""

        class _ResolveForbidden:
            def has(self, credential_ref: str) -> bool:
                return True

            def resolve(self, credential_ref: str) -> object:
                raise AssertionError("the gate must not materialise the credential value")

        gate = _gate_with(_ResolveForbidden())
        assert gate.open is True  # type: ignore[attr-defined]


class TestEndpointRefusalIsAlreadyJudgedElsewhere:
    """端点拒绝那一格**指到既有套件**：核对它在，且没被跳过。"""

    def test_the_cited_suite_exists(self) -> None:
        assert EGRESS_GATE_SUITE.is_file(), (
            f"§7 cites {EGRESS_GATE_SUITE.relative_to(REPO_ROOT)} for endpoint refusal, "
            "but that file is gone"
        )

    def test_the_cited_suite_still_asserts_zero_outbound_and_a_non_vacuous_counter(self) -> None:
        """被引用的两条关键用例**仍在**：零出站 + 反证不空转。"""
        text = EGRESS_GATE_SUITE.read_text(encoding="utf-8")
        for name in (
            "test_denied_url_makes_zero_outbound_calls",
            "test_allowed_url_does_probe_so_the_counter_is_not_vacuous",
        ):
            assert f"def {name}(" in text, (
                f"§7 points endpoint refusal at {name!r}, but that case is gone; "
                "either restore it or change §7 and this judge together"
            )

    def test_the_cited_suite_is_not_disabled(self) -> None:
        text = EGRESS_GATE_SUITE.read_text(encoding="utf-8")
        for marker in ("pytestmark", "pytest.importorskip", "pytest.skip("):
            assert marker not in text, (
                f"the cited suite now carries {marker!r}: a skipped suite is not evidence"
            )


class TestTheRunLegDoesNotFallBackToAnotherModel:
    """「模型不存在 ⇒ 不回退」：run 的 LLM 装配路径只消费**一个**模型。"""

    def test_the_llm_builder_takes_exactly_one_model(self) -> None:
        text = LLM_FACTORY.read_text(encoding="utf-8")
        assert "def build_llm(\n    endpoint: LLMEndpoint,\n    model: ModelDefinition," in text, (
            "build_llm no longer takes exactly one ModelDefinition — if a candidate list was "
            "added, the run leg can now fall back and §7's third row is wrong"
        )
        assert "fallback" not in text, "the run leg's LLM builder must not consult a fallback list"

    def test_the_session_factory_builds_from_the_bound_model_only(self) -> None:
        text = SESSION_FACTORY.read_text(encoding="utf-8")
        body = text[text.index("def session_llm_factory(") :]
        scoped = body[: body.find("\ndef ", 1)]
        assert "_gated_session_target(spec" in scoped, (
            "the session LLM must be built from the spec's resolved target"
        )
        assert "fallback" not in scoped, (
            "the session LLM factory consulted a fallback list — the run leg would retry on "
            "another model instead of failing"
        )

    def test_retries_are_bounded_by_endpoint_config(self) -> None:
        """「不重试到超时」是**配置保证**：`num_retries` 来自 endpoint 的 `max_retries`。"""
        factory = LLM_FACTORY.read_text(encoding="utf-8")
        assert "num_retries=endpoint.max_retries" in factory, (
            "num_retries must come from the endpoint config, not from an SDK default"
        )
        yaml_text = ENDPOINTS_YAML.read_text(encoding="utf-8")
        assert re.search(r"max_retries:\s*\d+", yaml_text), (
            "every registered endpoint must declare a bounded max_retries"
        )


class TestTheExpectationsAreWrittenDown:
    """三类情形的期望必须有明文（只判在场与否 + 指向，不判文笔）。"""

    def test_every_case_has_a_row(self) -> None:
        for label in _LABELS:
            assert _row(label), label

    def test_the_invalid_credential_row_points_at_the_live_case(self) -> None:
        assert "test_live_invalid_credential_fails_loudly_without_leaking" in _row("无效凭据")

    def test_the_endpoint_row_points_at_the_cited_suite(self) -> None:
        assert "tests/api/test_runtime_egress_gate.py" in _row("端点拒绝")

    def test_the_model_row_points_at_the_builder(self) -> None:
        assert "adapters/openhands/llm_factory.py" in _row("模型不存在")

    def test_the_three_boundaries_are_stated(self) -> None:
        section = _section_seven()
        for phrase in ("门开", "有界", "不消费"):
            assert phrase in section, f"§7 must state the boundary containing {phrase!r}"


class TestTheModelAbsenceRowPointsAtAMeasuredSample:
    """「模型不存在」那一格**既要**指装配层判据，**也要**指 provider 侧**实测样本**。

    GOAL-010 EC-04 之前，这一格只有装配层结构断言（「只消费一个模型」）——
    那证明的是「不会回退」，**不**证明 provider 面对未知模型会拒绝。样本落地后，
    两句话分别有各自的出处；这一组判据把它们**绑在一起**，防止任一侧被悄悄摘掉。
    """

    def test_the_row_still_points_at_the_builder(self) -> None:
        assert "adapters/openhands/llm_factory.py" in _row("模型不存在")

    def test_the_row_points_at_the_live_sample(self) -> None:
        assert "tests/e2e/test_live_model_absence.py" in _row("模型不存在"), (
            "the row no longer cites the measured provider-side sample — if the sample was "
            "removed, the row must go back to saying the provider side is unmeasured"
        )
        assert LIVE_ABSENCE_SUITE.is_file(), (
            f"§7 cites {LIVE_ABSENCE_SUITE.relative_to(REPO_ROOT)}, but that file is gone"
        )

    def test_the_sample_is_marked_requires_live_llm(self) -> None:
        from tests.e2e import test_live_model_absence

        raw = test_live_model_absence.pytestmark
        marks = {mark.name for mark in (raw if isinstance(raw, list) else [raw])}
        assert "requires_live_llm" in marks, (
            "the absence sample spends a real call and must be skipped by the default gate"
        )

    def test_the_sample_skips_without_its_precondition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """预置条件式：**没声明就 skip**（不是恰好通过）。

        **这一条压过一次**（本 cycle 实测）：第一版写成「样本文件里出现开关名」的**文本**判据，
        把样本里的开关名改成 `…_PRESSED` 仍然**绿**——被断言的字符串是别名的**前缀**，
        子串判定根本不区分。改成**行为**判据后，改名 ⇒ 下面第二条红（声明的开关点不亮它）。
        """
        from tests.e2e import test_live_model_absence

        monkeypatch.delenv(_ABSENCE_CASE_ENV, raising=False)
        with pytest.raises(pytest.skip.Exception):
            test_live_model_absence._require_case()

    def test_the_sample_starts_when_its_switch_is_declared(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """配对：声明开关 ⇒ 不再 skip。两条一起才钉住「开关就是这一个名字」。

        **skip 不算红**——所以这里把样本抛出的 skip **转成失败**：否则开关被改名时，
        这条判据自己也跟着 skip，整组又变成「恰好绿」。
        """
        from tests.e2e import test_live_model_absence

        assert test_live_model_absence._CASE_ENV == _ABSENCE_CASE_ENV, (
            "the sample's precondition switch was renamed — the §7 row and this judge "
            "would keep citing a switch that no longer starts it"
        )
        monkeypatch.setenv(_ABSENCE_CASE_ENV, "1")
        try:
            test_live_model_absence._require_case()
        except pytest.skip.Exception as exc:
            pytest.fail(f"{_ABSENCE_CASE_ENV} must start the sample, but it skipped: {exc}")


class TestTheLiveCounterProofIsPreconditionedNotAlwaysGreen:
    """反证用例必须**预置条件式**：未声明即 SKIP 并点名，不得恰好通过。"""

    def test_the_live_failure_suite_exists_and_is_marked_requires_live_llm(self) -> None:
        from tests.e2e import test_live_failure_paths

        raw = test_live_failure_paths.pytestmark
        marks = {mark.name for mark in (raw if isinstance(raw, list) else [raw])}
        assert "requires_live_llm" in marks, (
            "the failure-path counter-proof must be skipped by the default gate"
        )

    def test_the_live_failure_suite_skips_without_its_precondition(self) -> None:
        """未声明预置条件时必须 skip——否则未来操作者跑整套会撞上一个「期望失败」的用例。"""
        text = LIVE_FAILURE_SUITE.read_text(encoding="utf-8")
        assert "pytest.skip(" in text, (
            "the counter-proof must skip (naming why) when its precondition is absent; "
            "an always-green failure test proves nothing"
        )
        assert "RESEARCHOS_LIVE_FAILURE_CASE" in text, (
            "the precondition must be an explicit, single-command switch"
        )
