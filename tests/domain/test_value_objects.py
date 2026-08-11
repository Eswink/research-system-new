"""域内核核心值对象不变量测试。"""

from __future__ import annotations

import hashlib
import uuid as uuid_module
from datetime import datetime, timedelta, timezone

import pytest

from packages.domain.core import ID, Digest, Money, Timestamp, Version


def _utc_offset(hours: int) -> timezone:
    return timezone(timedelta(hours=hours))


def test_id_accepts_canonical_uuid4() -> None:
    raw = "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
    assert ID(raw).value == raw


def test_id_rejects_malformed_string() -> None:
    with pytest.raises(ValueError):
        ID("not-a-uuid")


def test_id_rejects_non_uuid4_version() -> None:
    v1 = "550e8400-e29b-11d4-a716-446655440000"
    with pytest.raises(ValueError):
        ID(v1)


def test_id_rejects_non_canonical_case() -> None:
    with pytest.raises(ValueError):
        ID("3F2504E0-4F89-41D3-9A0C-0305E82C3301")


def test_id_generate_produces_valid_uuid4() -> None:
    generated = ID.generate()
    assert uuid_module.UUID(generated.value).version == 4


def test_timestamp_requires_utc() -> None:
    assert Timestamp(datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)).value is not None
    with pytest.raises(ValueError):
        Timestamp(datetime(2026, 8, 11, 12, 0))
    with pytest.raises(ValueError):
        Timestamp(datetime(2026, 8, 11, 12, 0, tzinfo=_utc_offset(8)))


def test_timestamp_now_is_utc_aware() -> None:
    stamp = Timestamp.now()
    assert stamp.value.tzinfo is not None
    assert stamp.value.utcoffset() == timezone.utc.utcoffset(stamp.value)


def test_digest_accepts_sha256_hex() -> None:
    hex_value = "ab" * 32
    assert Digest(hex_value).hex_value == hex_value


def test_digest_rejects_invalid_hex() -> None:
    with pytest.raises(ValueError):
        Digest("xyz" * 22)
    with pytest.raises(ValueError):
        Digest("abc")


def test_digest_of_bytes_matches_hashlib() -> None:
    payload = b"research-os"
    assert Digest.of_bytes(payload).hex_value == hashlib.sha256(payload).hexdigest()


def test_digest_parse_and_str_roundtrip() -> None:
    hex_value = "cd" * 32
    parsed = Digest.parse(f"sha256:{hex_value}")
    assert parsed.hex_value == hex_value
    assert str(parsed) == f"sha256:{hex_value}"
    with pytest.raises(ValueError):
        Digest.parse(hex_value)


def test_version_accepts_semver() -> None:
    assert Version("0.4.0").text == "0.4.0"
    assert Version("1.2.3").text == "1.2.3"


def test_version_rejects_invalid_semver() -> None:
    for bad in ("1.2", "v1.2.3", "01.2.3", "1.2.3.4", "1.2.3-beta"):
        with pytest.raises(ValueError):
            Version(bad)


def test_money_validates_currency() -> None:
    assert Money(100, "USD").currency == "USD"
    with pytest.raises(ValueError):
        Money(100, "usd")
    with pytest.raises(ValueError):
        Money(100, "US")
    with pytest.raises(ValueError):
        Money(100, "US1")


def test_money_minor_units_are_integers() -> None:
    assert Money(150, "USD").minor_units == 150
