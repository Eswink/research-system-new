"""ProtocolBody 值对象：冻结正文与它的 digest 必须自洽（GOAL-004 cycle 1）。

冻结正文是"这份 run 用哪份字节装配"的 durable 事实；它的全部价值建立在
"正文与 digest 相符"这一条不变量上——不符就必须在构造时炸掉，而不是等到
重建时才把一份被改过的正文当成权威输入。
"""

from __future__ import annotations

import pytest

from packages.domain.core import Digest
from packages.domain.protocol_source import ProtocolBody, ProtocolSource

_TEXT = "id: sort_analysis_v1\nversion: 1.0.0\nphases: []\n"


def test_the_digest_is_the_sha256_of_the_body_text() -> None:
    body = ProtocolBody.of(_TEXT)

    assert body.text == _TEXT
    assert body.digest == Digest.of_bytes(_TEXT.encode("utf-8"))


def test_a_body_whose_digest_does_not_match_its_text_is_rejected() -> None:
    """篡改的正文构造不出来（把 digest 换成另一份正文的 digest 也不行）。"""
    with pytest.raises(ValueError, match="digest does not match"):
        ProtocolBody(text=_TEXT, digest=Digest.of_bytes(b"another protocol body"))


def test_an_empty_body_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ProtocolBody(text="", digest=Digest.of_bytes(b""))


def test_the_source_value_object_still_enforces_the_xor() -> None:
    """回归：来源判据不变（路径 xor 草稿修订），正文冻结不改变来源语义。"""
    with pytest.raises(ValueError, match="exactly one protocol source"):
        ProtocolSource(protocol_path="a.yaml", draft_id="d1", draft_revision=1)
    with pytest.raises(ValueError, match="exactly one protocol source"):
        ProtocolSource()
    with pytest.raises(ValueError, match="positive draft_revision"):
        ProtocolSource(draft_id="d1", draft_revision=0)
