/**
 * The only module in the repository allowed to import `@cursor/sdk`.
 * Everything else depends on the `AgentFactory` / `ModelCatalog` interfaces in
 * `types.ts`, which keeps tests fake-driven and SDK types confined here.
 */
import { Agent, Cursor, ConfigurationError, type Run, type SDKAgent } from "@cursor/sdk";

import type {
  AgentFactory,
  AgentHandle,
  ModelCatalog,
  ModelCatalogEntry,
  RunHandle,
  RunOutcome,
  RuntimeOptions,
} from "./types.ts";

/**
 * Read-only toolset: `task` is absent, which also prevents nested subagent
 * delegation per the project no-nesting policy; `mcp` is absent, which
 * disables the whole MCP tool family; shell/edit/delete are never offered.
 */
const READ_ONLY_TOOLS = ["read", "grep", "glob", "ls"] as const;

export class SdkAgentFactory implements AgentFactory {
  async create(
    _task: Parameters<AgentFactory["create"]>[0],
    options: RuntimeOptions,
  ): Promise<AgentHandle> {
    const agent = await Agent.create({
      apiKey: options.apiKey,
      model: { id: options.modelId },
      tools: [...READ_ONLY_TOOLS],
      local: {
        cwd: options.cwd,
        // Inline config only: never implicitly load project/user/team settings.
        settingSources: [],
        sandboxOptions: { enabled: true },
      },
    });
    return new SdkAgentHandle(agent);
  }
}

export class SdkModelCatalog implements ModelCatalog {
  private readonly apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async list(): Promise<readonly ModelCatalogEntry[]> {
    const models = await Cursor.models.list({ apiKey: this.apiKey });
    return models.map((model) => ({ id: model.id, displayName: model.displayName }));
  }
}

export function isConfigurationError(error: unknown): boolean {
  return error instanceof ConfigurationError;
}

class SdkAgentHandle implements AgentHandle {
  private readonly inner: SDKAgent;

  constructor(inner: SDKAgent) {
    this.inner = inner;
  }

  get agentId(): string {
    return this.inner.agentId;
  }

  async send(prompt: string): Promise<RunHandle> {
    return new SdkRunHandle(await this.inner.send(prompt));
  }

  async dispose(): Promise<void> {
    await this.inner[Symbol.asyncDispose]();
  }
}

class SdkRunHandle implements RunHandle {
  private readonly inner: Run;

  constructor(inner: Run) {
    this.inner = inner;
  }

  get id(): string {
    return this.inner.id;
  }

  get requestId(): string | undefined {
    return this.inner.requestId;
  }

  async wait(): Promise<RunOutcome> {
    const result = await this.inner.wait();
    return {
      status: result.status,
      result: result.result,
      errorCode: result.error?.code,
      requestId: result.requestId,
      resolvedModelId: result.model?.id,
      durationMs: result.durationMs,
    };
  }

  async cancel(): Promise<void> {
    await this.inner.cancel();
  }
}
