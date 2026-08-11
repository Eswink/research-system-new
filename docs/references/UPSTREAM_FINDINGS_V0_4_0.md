# Upstream Findings Applied in v0.4.0

Audit date: 2026-08-10.

## OpenHands

Official SDK docs show:

- Conversation manages execution/state and supports local/remote workspace;
- built-in status includes paused/stuck/waiting-for-confirmation;
- persistence/resume exists;
- resume verifies Agent type and Tool names, while other config may change;
- direct `execute_tool()` bypasses Agent loop confirmation/security checks;
- plugins bundle skills/hooks/MCP/agents/commands;
- conversation fork supports independent branches;
- LLM supports model/base_url/api_key and usage metrics;
- Docker/remote/Apptainer workspace options exist.

Architecture consequences:

- freeze Tool Set per AgentSession;
- enforce Manifest compatibility before resume;
- wrap all direct tool execution in Policy;
- pin Plugin revision/digest;
- use Fork for model/tool experiments;
- keep Research OS Secret/Domain state outside OpenHands.

Sources:

- https://docs.openhands.dev/sdk
- https://docs.openhands.dev/sdk/api-reference/openhands.sdk.conversation
- https://docs.openhands.dev/sdk/api-reference/openhands.sdk.agent
- https://docs.openhands.dev/sdk/api-reference/openhands.sdk.llm
- https://docs.openhands.dev/sdk/guides/plugins
- https://docs.openhands.dev/sdk/guides/convo-fork
- https://docs.openhands.dev/sdk/guides/security
- https://docs.openhands.dev/sdk/guides/agent-server/docker-sandbox
- https://docs.openhands.dev/sdk/guides/agent-server/apptainer-sandbox

## MCP

Current MCP documentation emphasizes:

- authorization and security best practices for remote servers;
- Streamable HTTP as the current remote transport in the SDK guidance;
- Roots are informational and not an access-control mechanism;
- server state handles must not be treated as authorization;
- structured tool output and evolving protocol versions require schema/version tracking.

Sources:

- https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices
- https://modelcontextprotocol.io/docs/tutorials/security/authorization
- https://modelcontextprotocol.io/specification/draft/client/roots
- https://modelcontextprotocol.io/seps/2567-sessionless-mcp
- https://ts.sdk.modelcontextprotocol.io/server

## Temporal

Temporal provides durable execution for long-running workflows that resume after process/infrastructure failures.

Architecture consequence: keep it behind WorkflowEngine; external side effects remain idempotent Activities.

Source:

- https://docs.temporal.io/

## OpenTelemetry

GenAI semantic attributes can contain sensitive/PII content.

Architecture consequence: content capture disabled by default; record metadata/digest/usage.

Sources:

- https://opentelemetry.io/docs/specs/semconv/
- https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/

## OPA

OPA separates policy decision-making from enforcement via structured input and policy-as-code.

Architecture consequence: Native evaluator for MVP, optional OPA adapter for production.

Source:

- https://www.openpolicyagent.org/docs

## Execution Backends

- OpenHands recommends Docker sandbox for local execution and supports remote/Apptainer patterns.
- SWE-ReX provides a Python interface for local/remote sandboxed shell execution and parallel environments.
- Managed microVM services such as E2B can be optional hardened adapters.

Sources:

- https://docs.openhands.dev/openhands/usage/sandboxes/docker
- https://github.com/SWE-agent/SWE-ReX
- https://e2b.dev/docs

## Model Relay Transport (M3)

- OpenAI Chat Completions + Models API 官方机器可读规范为 `openai/openai-openapi` 的 `openapi.yaml` v2.3.0（MIT，developers.openai.com）；chat/completions 仍是全行业 OPENAI_COMPATIBLE 的事实基线。
- httpx 0.28.1（BSD-3-Clause）提供 `MockTransport`/`ASGITransport`，可完全离线的确定性测试；SSE 事件流需自行按行解析（httpx 不内置）。
- tenacity 9.1.4（Apache-2.0）承载 FAILURE_MODEL retry matrix 的薄包装（429 退避+jitter；401/403、400/422 不重试）。
- 不引入 openai-python SDK（类型/错误语义绑定 vendor），不引入 pybreaker（circuit breaker 在 domain 自实现以保持零依赖与穷尽测试）。

Sources:

- https://github.com/openai/openai-openapi
- https://developers.openai.com/api/docs
- https://www.python-httpx.org/advanced/transports/
- https://tenacity.readthedocs.io/
