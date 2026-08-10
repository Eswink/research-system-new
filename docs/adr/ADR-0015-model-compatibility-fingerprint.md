# ADR-0015 — Model Eligibility and Runtime Fingerprint

Status: Accepted

中转站 Model ID 不能单独证明能力或底层模型身份。

Preflight 使用 capability probe/eligibility；Run 保存尽可能完整的 runtime fingerprint，并明确其可复现边界。
