"""Evidence / Claim 应用层 use case（M10 Evidence Ledger）。

- verification：PROPOSED → VERIFIED 的唯一升级入口（gate PASS + 合法 provenance）；
- contradiction：冲突证据检测（REFUTES → DISPUTED）。

本包只组合 application-owned Port（EvidenceLedger）与 Domain 类型。
"""
