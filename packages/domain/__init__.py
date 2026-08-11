"""Research OS 域内核。

M1 范围（CODEX_BOOTSTRAP.md）：实体、值对象、枚举、不变量、状态机、
RunManifest/Revision、确定性 digest。无 upstream 类型；Domain 不依赖
Web/ORM/LLM/runtime/provider 等外层实现。
"""

from packages.domain.core import ID, Digest, Money, Timestamp, Version
from packages.domain.serialization import canonical_json_bytes, digest_of

__all__ = [
    "Digest",
    "ID",
    "Money",
    "Timestamp",
    "Version",
    "canonical_json_bytes",
    "digest_of",
]
