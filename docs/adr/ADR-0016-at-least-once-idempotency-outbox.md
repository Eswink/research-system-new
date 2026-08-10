# ADR-0016 — At-least-once Execution + Idempotency + Outbox

Status: Accepted

任务可能重复投递。通过 idempotency、lease、dedupe 和 transactional outbox 保持业务一致性，不宣称 exactly-once。
