"""域内核 bootstrap 冒烟：导入与基础确定性回归。"""

from __future__ import annotations

from packages.domain import canonical_json_bytes, digest_of
from packages.domain.core import ID, Digest, Money, Timestamp, Version
from packages.domain.serialization import canonical_json_roundtrip


def test_domain_package_imports() -> None:
    assert canonical_json_bytes is not None
    assert digest_of is not None


def test_domain_core_exports() -> None:
    members = {
        "Digest": Digest,
        "ID": ID,
        "Money": Money,
        "Timestamp": Timestamp,
        "Version": Version,
    }
    for name, member in members.items():
        assert member is not None, name


def test_bootstrap_digest_regression() -> None:
    payload = {
        "project": "research-system",
        "version": "0.4.0",
        "objects": [{"kind": "run", "count": 1}],
    }
    first = str(digest_of(payload))
    second = str(digest_of(payload))
    assert first == second
    assert Digest.parse(first).hex_value == digest_of(payload).hex_value


def test_bootstrap_roundtrip_regression() -> None:
    payload = {"run": {"id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301", "active": True}}
    assert canonical_json_roundtrip(payload) == payload
