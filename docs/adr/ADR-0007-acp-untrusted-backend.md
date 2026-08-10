# ADR-0007 — External Agent Harnesses Are Deferred and Untrusted

Status: Deferred / Optional
Updated: 2026-08-10

Codex、Claude Code、ACP 等不属于 MVP 主路径。

未来若接入，视作不可信执行后端，必须受 Workspace、Network、Credential、Budget 和 Audit 约束，并实现 AgentRuntime contract。
