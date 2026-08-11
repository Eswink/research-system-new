"""Research OS 域内核核心值对象。

契约（CODEX_BOOTSTRAP.md M1）：无 upstream 类型、stable enum、UUID、UTC、
Decimal/最小货币单位、JSON round-trip、deterministic digest、invariant tests。
本模块不 import 任何外层或第三方类型。
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

SHA256_HEX_RE = re.compile(r"[0-9a-f]{64}")
DIGEST_PREFIX_RE = re.compile(r"sha256:([0-9a-f]{64})")
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


@dataclass(frozen=True, slots=True)
class ID:
    """UUID4 标识符，强制规范小写形式。"""

    value: str

    def __post_init__(self) -> None:
        try:
            parsed = uuid.UUID(self.value)
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"invalid UUID: {self.value!r}") from exc
        if parsed.version != 4:
            raise ValueError(f"ID must be a UUID4: {self.value!r}")
        if self.value != str(parsed):
            raise ValueError(f"ID must be canonical lowercase UUID: {self.value!r}")

    @classmethod
    def generate(cls) -> ID:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class Timestamp:
    """UTC 时间戳；拒绝 naive 与非 UTC 时区输入。"""

    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None or self.value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        if self.value.utcoffset() != timezone.utc.utcoffset(self.value):
            raise ValueError("timestamp must be in UTC")

    @classmethod
    def now(cls) -> Timestamp:
        return cls(datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class Digest:
    """sha256 digest；hex 值校验，字符串形式为 `sha256:<hex>`。"""

    hex_value: str

    def __post_init__(self) -> None:
        if SHA256_HEX_RE.fullmatch(self.hex_value) is None:
            raise ValueError(f"invalid sha256 digest: {self.hex_value!r}")

    @classmethod
    def of_bytes(cls, payload: bytes) -> Digest:
        return cls(hashlib.sha256(payload).hexdigest())

    @classmethod
    def parse(cls, text: str) -> Digest:
        match = DIGEST_PREFIX_RE.fullmatch(text)
        if match is None:
            raise ValueError(f"invalid digest literal: {text!r}")
        return cls(match.group(1))

    def __str__(self) -> str:
        return f"sha256:{self.hex_value}"


@dataclass(frozen=True, slots=True)
class Version:
    """语义化版本号（MAJOR.MINOR.PATCH，无预发布/构建元数据）。"""

    text: str

    def __post_init__(self) -> None:
        if SEMVER_RE.fullmatch(self.text) is None:
            raise ValueError(f"invalid semantic version: {self.text!r}")


@dataclass(frozen=True, slots=True)
class Money:
    """以最小货币单位表示的金额；拒绝非大写三字母货币代码。"""

    minor_units: int
    currency: str = "USD"

    def __post_init__(self) -> None:
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError(f"currency must be a 3-letter code: {self.currency!r}")
        if self.currency != self.currency.upper():
            raise ValueError(f"currency must be uppercase: {self.currency!r}")
