"""Evidence / Claim 应用层 use case（M10 Evidence Ledger）。

- verification：PROPOSED → VERIFIED 的唯一升级入口（gate PASS + 合法 provenance）；
- contradiction：冲突证据检测（REFUTES → DISPUTED）；
- m12_chain：M12 Reference Workflow 证据链组合（实验产物 → Source →
  Evidence → Claim → Memory）。
"""
