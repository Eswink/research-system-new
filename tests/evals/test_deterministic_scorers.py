"""M11 deterministic scorers 测试：obvious PASS/FAIL、boundary、malformed、版本。"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping

import pytest

from packages.application.evaluation.scorer_types import (
    V1,
    InvariantPredicate,
    ScorerContext,
    ScorerInput,
)
from packages.application.evaluation.scorers import (
    resolve_scorer,
    versioned_scorer_ids,
)
from packages.domain.core import Version
from packages.domain.eval_result import ScorerFinding
from packages.domain.eval_spec import EvalCase, EvalScope, RubricSpec


def _case(case_id: str, expected: object, scorer_id: str) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref=f"input://{case_id}",
        expected=expected,
        scorer_refs=(),
    )


def _run(
    scorer_id: str,
    case: EvalCase,
    actual: object,
    *,
    predicates: Mapping[str, InvariantPredicate] | None = None,
    evidence: Mapping[str, str] | None = None,
) -> ScorerFinding:
    fn = resolve_scorer(scorer_id, V1.text)
    return fn(
        ScorerContext(
            case=case,
            input=ScorerInput(actual=actual, evidence_sources=evidence or {}),
            predicates=predicates or {},
        )
    )


def _status(
    scorer_id: str,
    case: EvalCase,
    actual: object,
    *,
    predicates: Mapping[str, InvariantPredicate] | None = None,
    evidence: Mapping[str, str] | None = None,
) -> str:
    finding = _run(
        scorer_id,
        case,
        actual,
        predicates=predicates,
        evidence=evidence,
    )
    return finding.status.value


# --- exact_match ---


def test_exact_match_pass() -> None:
    assert (
        _status("exact_match", _case("c", {"answer": 42}, "exact_match"), {"answer": 42}) == "PASS"
    )


def test_exact_match_fail() -> None:
    assert (
        _status("exact_match", _case("c", {"answer": 42}, "exact_match"), {"answer": 43}) == "FAIL"
    )


def test_exact_match_missing_oracle_is_infra_error() -> None:
    case = EvalCase(
        id="c",
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref="input://c",
        expected=None,
        rubric=(RubricSpec("r1", "soundness", "semantic oracle only"),),
    )
    assert _status("exact_match", case, {"answer": 42}) == "INFRA_ERROR"


# --- digest_match ---


def test_digest_match_pass_and_fail() -> None:
    spec = {
        "algorithm": "sha256",
        "hex": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
    }
    assert _status("digest_match", _case("c", spec, "digest_match"), "hello") == "PASS"
    assert _status("digest_match", _case("c", spec, "digest_match"), "world") == "FAIL"


def test_digest_match_malformed_spec_and_actual() -> None:
    assert _status("digest_match", _case("c", {"algorithm": "md5"}, "digest_match"), "x") == "FAIL"
    short_hex_spec = {"algorithm": "sha256", "hex": "short"}
    assert _status("digest_match", _case("c", short_hex_spec, "digest_match"), "x") == "FAIL"
    assert (
        _status(
            "digest_match",
            _case("c", {"algorithm": "sha256", "hex": "a" * 64}, "digest_match"),
            42,
        )
        == "FAIL"
    )


# --- required_fields ---


def test_required_fields_pass_fail_and_malformed() -> None:
    spec = ["a", "b.c"]
    assert (
        _status("required_fields", _case("c", spec, "required_fields"), {"a": 1, "b": {"c": 2}})
        == "PASS"
    )
    assert _status("required_fields", _case("c", spec, "required_fields"), {"a": 1}) == "FAIL"
    assert _status("required_fields", _case("c", spec, "required_fields"), [1, 2]) == "FAIL"
    assert _status("required_fields", _case("c", {"a": 1}, "required_fields"), {"a": 1}) == "FAIL"


# --- numeric_tolerance ---


def test_numeric_tolerance_boundary() -> None:
    spec = {"value": 1.0, "tolerance": 0.1}
    case = _case("c", spec, "numeric_tolerance")
    assert _status("numeric_tolerance", case, Decimal("1.05")) == "PASS"
    assert _status("numeric_tolerance", case, Decimal("1.1")) == "PASS"
    assert _status("numeric_tolerance", case, Decimal("1.11")) == "FAIL"
    assert _status("numeric_tolerance", case, "abc") == "FAIL"
    assert _status("numeric_tolerance", case, {"v": 1}) == "FAIL"


def test_numeric_tolerance_malformed_spec() -> None:
    assert _status("numeric_tolerance", _case("c", {"value": 1}, "numeric_tolerance"), 1) == "FAIL"


# --- invariant ---


def test_invariant_pass_fail_and_missing_predicate() -> None:
    spec = {"predicate_id": "no_negatives", "params": {}}
    case = _case("c", spec, "invariant")
    predicates = {"no_negatives": lambda value, params: all(v >= 0 for v in value)}
    assert _status("invariant", case, [1, 2, 3], predicates=predicates) == "PASS"
    assert _status("invariant", case, [1, -1], predicates=predicates) == "FAIL"
    assert _status("invariant", case, [1], predicates={}) == "INFRA_ERROR"


# --- evidence_source_distinct ---


def test_evidence_source_distinct_counts_identities() -> None:
    spec = {"minimum": 2}
    case = _case("c", spec, "evidence_source_distinct")
    duplicated = {"s1": "identity-a", "s2": "identity-a"}
    distinct = {"s1": "identity-a", "s2": "identity-b"}
    assert _status("evidence_source_distinct", case, None, evidence=duplicated) == "FAIL"
    assert _status("evidence_source_distinct", case, None, evidence=distinct) == "PASS"


# --- schema_validity ---


def test_schema_validity_obvious_pass_and_fail() -> None:
    spec = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"type": "integer"}},
    }
    case = _case("c", spec, "schema_validity")
    assert _status("schema_validity", case, {"answer": 42}) == "PASS"
    assert _status("schema_validity", case, {"answer": "42"}) == "FAIL"
    assert _status("schema_validity", case, {"other": 1}) == "FAIL"


def test_schema_validity_nested_and_unknown_type() -> None:
    spec = {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": {"type": "string"}},
        },
    }
    case = _case("c", spec, "schema_validity")
    assert _status("schema_validity", case, {"items": ["a", "b"]}) == "PASS"
    assert _status("schema_validity", case, {"items": ["a", 2]}) == "FAIL"
    bad = _case("c", {"type": "tuple"}, "schema_validity")
    assert _status("schema_validity", bad, (1, 2)) == "FAIL"


# --- 注册表与版本 ---


def test_resolve_unknown_scorer_version_fails_closed() -> None:
    with pytest.raises(KeyError, match="unknown scorer"):
        resolve_scorer("exact_match", "2.0.0")
    with pytest.raises(KeyError, match="unknown scorer"):
        resolve_scorer("llm_judge", "1.0.0")


def test_versioned_scorer_ids_are_stable() -> None:
    ids = versioned_scorer_ids()
    assert "exact_match@1.0.0" in ids
    assert "schema_validity@1.0.0" in ids
    assert "gpu_compute_device@1.0.0" in ids  # M17 no-fallback discriminator
    assert len(ids) == len(set(ids))
    assert len(ids) == 8


def test_scorer_does_not_mutate_expected() -> None:
    expected = {"answer": 42}
    case = _case("c", expected, "exact_match")
    _run("exact_match", case, {"answer": 42})
    assert case.expected == {"answer": 42}
