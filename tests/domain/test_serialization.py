"""canonical 确定性序列化测试。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from packages.domain.serialization import (
    canonical_json_bytes,
    canonical_json_roundtrip,
    digest_of,
)


def test_canonical_json_is_key_sorted() -> None:
    left = canonical_json_bytes({"b": 1, "a": 2})
    right = canonical_json_bytes({"a": 2, "b": 1})
    assert left == right


def test_canonical_json_is_recursively_sorted() -> None:
    nested_a = canonical_json_bytes({"outer": {"z": 1, "y": {"b": 2, "a": 3}}})
    nested_b = canonical_json_bytes({"outer": {"y": {"a": 3, "b": 2}, "z": 1}})
    assert nested_a == nested_b


def test_datetime_utc_with_zero_microseconds() -> None:
    stamp = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
    assert canonical_json_bytes({"at": stamp}) == b'{"at":"2026-08-11T12:00:00Z"}'


def test_datetime_preserves_six_digit_microseconds() -> None:
    stamp = datetime(2026, 8, 11, 12, 0, 0, 123456, tzinfo=timezone.utc)
    assert canonical_json_bytes({"at": stamp}) == b'{"at":"2026-08-11T12:00:00.123456Z"}'


def test_datetime_normalizes_offset_to_utc() -> None:
    from datetime import timedelta

    non_utc = datetime(2026, 8, 11, 20, 0, 0, tzinfo=timezone(timedelta(hours=8)))
    assert canonical_json_bytes({"at": non_utc}) == b'{"at":"2026-08-11T12:00:00Z"}'


def test_datetime_naive_is_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_json_bytes({"at": datetime(2026, 8, 11, 12, 0, 0)})


def test_decimal_trailing_zeros_are_normalized() -> None:
    assert canonical_json_bytes({"v": Decimal("0.0100")}) == canonical_json_bytes({
        "v": Decimal("0.01")
    })
    assert canonical_json_bytes({"v": Decimal("1.0")}) == b'{"v":"1"}'


def test_decimal_zero_is_canonical() -> None:
    assert canonical_json_bytes({"v": Decimal("-0")}) == b'{"v":"0"}'
    assert canonical_json_bytes({"v": Decimal("0E+3")}) == b'{"v":"0"}'


def test_decimal_exponent_is_expanded() -> None:
    assert canonical_json_bytes({"v": Decimal("1E+3")}) == b'{"v":"1000"}'


def test_decimal_non_finite_is_rejected() -> None:
    for bad in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
        with pytest.raises(ValueError):
            canonical_json_bytes({"v": bad})


def test_uuid_is_canonical_lowercase() -> None:
    raw = UUID("3F2504E0-4F89-41D3-9A0C-0305E82C3301")
    assert canonical_json_bytes({"id": raw}) == b'{"id":"3f2504e0-4f89-41d3-9a0c-0305e82c3301"}'


def test_float_is_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_json_bytes({"v": 1.5})


def test_unsupported_type_is_rejected() -> None:
    with pytest.raises(TypeError):
        canonical_json_bytes({"v": object()})


def test_ensure_ascii_is_off() -> None:
    assert canonical_json_bytes({"name": "研究"}) == '{"name":"研究"}'.encode("utf-8")


def test_roundtrip_preserves_structure() -> None:
    payload = {"run_id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301", "tokens": 12, "ok": True}
    assert canonical_json_roundtrip(payload) == payload


def test_digest_is_deterministic() -> None:
    left = digest_of({"a": [1, 2, {"b": "研究"}]})
    right = digest_of({"a": [1, 2, {"b": "研究"}]})
    assert left == right
    assert str(left).startswith("sha256:")
    assert len(left.hex_value) == 64


@dataclass(frozen=True, slots=True)
class _Nested:
    value: str


@dataclass(frozen=True, slots=True)
class _Record:
    kind: str
    nested: _Nested
    extra: list[int] = field(default_factory=list)


def test_dataclass_is_expanded_recursively() -> None:
    record = _Record(kind="probe", nested=_Nested(value="x"), extra=[1, 2])
    assert canonical_json_bytes(record) == b'{"extra":[1,2],"kind":"probe","nested":{"value":"x"}}'


def test_dataclass_matches_equivalent_dict() -> None:
    record = _Record(kind="probe", nested=_Nested(value="x"))
    as_dict = {"kind": "probe", "nested": {"value": "x"}, "extra": []}
    assert canonical_json_bytes(record) == canonical_json_bytes(as_dict)
