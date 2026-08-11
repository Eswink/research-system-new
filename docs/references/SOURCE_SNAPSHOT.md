# Source Snapshot — 2026-08-10

Official/primary sources reviewed for v0.4.0:

## OpenHands

- https://docs.openhands.dev/sdk
- https://docs.openhands.dev/sdk/api-reference/openhands.sdk.conversation
- https://docs.openhands.dev/sdk/api-reference/openhands.sdk.agent
- https://docs.openhands.dev/sdk/api-reference/openhands.sdk.llm
- https://docs.openhands.dev/sdk/api-reference/openhands.sdk.workspace
- https://docs.openhands.dev/sdk/guides/security
- https://docs.openhands.dev/sdk/guides/plugins
- https://docs.openhands.dev/sdk/guides/convo-fork
- https://docs.openhands.dev/sdk/guides/convo-persistence
- https://docs.openhands.dev/sdk/guides/agent-stuck-detector
- https://docs.openhands.dev/sdk/guides/agent-server/docker-sandbox
- https://docs.openhands.dev/sdk/guides/agent-server/apptainer-sandbox
- https://github.com/OpenHands/software-agent-sdk

## MCP

- https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices
- https://modelcontextprotocol.io/docs/tutorials/security/authorization
- https://modelcontextprotocol.io/specification/draft/client/roots
- https://modelcontextprotocol.io/seps/2567-sessionless-mcp
- https://ts.sdk.modelcontextprotocol.io/server

## Workflow / Policy / Telemetry

- https://docs.temporal.io/
- https://www.openpolicyagent.org/docs
- https://opentelemetry.io/docs/specs/semconv/
- https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/

## Sandbox

- https://github.com/SWE-agent/SWE-ReX
- https://e2b.dev/docs

## Model Relay Transport (M3)

- https://developers.openai.com/api/docs （OpenAI API reference；权威机器可读规范为 https://github.com/openai/openai-openapi 的 openapi.yaml v2.3.0，MIT）
- https://www.python-httpx.org/advanced/transports/ （httpx 0.28.1，BSD-3-Clause；MockTransport/ASGITransport 用于离线确定性测试）
- https://tenacity.readthedocs.io/ （tenacity 9.1.4，Apache-2.0）

Re-check exact license/version before locking dependencies.
