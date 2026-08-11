"""确定性序列化：canonical JSON 编码与 sha256 digest。

编码规则见 `docs/architecture/DETERMINISTIC_SERIALIZATION.md`：
- 对象 key 递归排序（嵌套 dict/映射键按 str 排序）
- datetime 编码为 RFC3339 UTC（微秒为 0 时省略小数，否则保留 6 位）
- Decimal 编码为无指数字符串，负零归一为 "0"
- UUID 编码为规范小写形式
- dataclass 递归展开为 dict
- float/NaN/Infinity 拒绝进入 digest 对象
- 输出无多余空白，UTF-8，不转义非 ASCII
"""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from packages.domain.core import Digest


def _encode(value: Any) -> Any:
    if isinstance(value, datetime):
        return _encode_datetime(value)
    if isinstance(value, Decimal):
        return _encode_decimal(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, str)) or value is None:
        return value
    if isinstance(value, float):
        raise ValueError("float is not allowed in canonical serialization")
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _encode(dataclasses.asdict(value))
    if isinstance(value, dict):
        encoded = {str(key): _encode(item) for key, item in value.items()}
        return dict(sorted(encoded.items(), key=lambda item: item[0]))
    if isinstance(value, (list, tuple)):
        return [_encode(item) for item in value]
    raise TypeError(f"unsupported canonical value type: {type(value)!r}")


def _encode_datetime(value: datetime) -> str:
    if value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    utc = value.astimezone(timezone.utc)
    if utc.microsecond == 0:
        return utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    return utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _encode_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("non-finite Decimal is not allowed in canonical serialization")
    if value.is_zero():
        return "0"
    return format(value.normalize(), "f")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _encode(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_json_roundtrip(value: Any) -> Any:
    return json.loads(canonical_json_bytes(value).decode("utf-8"))


def digest_of(value: Any) -> Digest:
    return Digest.of_bytes(canonical_json_bytes(value))
