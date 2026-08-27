/**
 * Control Plane API client（apps/web 唯一网络入口）。
 *
 * 约束（M13 DoD 12/13）：
 * - 只消费 src/api/types.ts 的 DTO；不接触 Python Domain；
 * - mutating 请求必须带 Idempotency-Key（重复提交/重试安全）；
 * - 带资源版本（ETag）的变更带 If-Match（陈旧版本 → 412 → UI 刷新）；
 * - Key 永不写入 localStorage / URL / logs（浏览器持久存储零 secret）。
 */

import type {
  AgentSpecDto,
  AgentCreateDto,
  AgentUpdatePayload,
  CompileResultDto,
  DiscoverModelsResultDto,
  DryRunProjectionDto,
  EndpointHealthDto,
  EndpointTestResultDto,
  ExperimentViewDto,
  LlmEndpointCreateDto,
  LlmEndpointReadDto,
  LlmEndpointUpdateDto,
  ModelCreateDto,
  ModelReadDto,
  ModelUpdateDto,
  PreflightReportDto,
  ProblemDto,
  ProbeResultDto,
  ProjectSettingsDto,
  RoleDefinitionDto,
  RunDetailDto,
  RunEventDto,
  TaskDto,
  TeamTemplateDto,
  Version,
  ApprovalDto,
  BudgetViewDto,
  ClaimMapDto,
  EvidenceDto,
  ExportBundleDto,
  CompatibilityViewDto,
} from "./types";

export interface ApiErrorBody extends Error {
  status: number;
  problem: ProblemDto;
}

export class ApiError extends Error implements ApiErrorBody {
  readonly status: number;
  readonly problem: ProblemDto;

  constructor(status: number, problem: ProblemDto) {
    super(problem.detail);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

const API_BASE = "/api";

async function request<T>(
  path: string,
  init: RequestInit,
  options?: { idempotencyKey?: string; ifMatch?: Version },
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (options?.idempotencyKey) {
    headers.set("Idempotency-Key", options.idempotencyKey);
  }
  if (options?.ifMatch) {
    headers.set("If-Match", options.ifMatch);
  }
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    let problem: ProblemDto | undefined;
    try {
      problem = (await response.json()) as ProblemDto;
    } catch {
      problem = undefined;
    }
    if (problem?.title) {
      throw new ApiError(response.status, problem);
    }
    throw new ApiError(response.status, {
      type: "about:blank",
      title: "Request Failed",
      status: response.status,
      detail: `HTTP ${String(response.status)}`,
      instance: path,
    });
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/** 每次 mutating 调用生成幂等 key（重复提交重放同一响应） */
function newIdempotencyKey(): string {
  return `${Date.now().toString(36)}-${crypto.randomUUID()}`;
}

export interface EndpointWithEtag {
  dto: LlmEndpointReadDto;
  etag: Version;
}

async function requestWithEtag(
  path: string,
  init: RequestInit,
  options?: { idempotencyKey?: string; ifMatch?: Version },
): Promise<EndpointWithEtag> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: new Headers({
      ...Object.fromEntries(new Headers(init.headers).entries()),
      Accept: "application/json",
      ...(init.body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(options?.idempotencyKey ? { "Idempotency-Key": options.idempotencyKey } : {}),
      ...(options?.ifMatch ? { "If-Match": options.ifMatch } : {}),
    }),
  });
  if (!response.ok) {
    let problem: ProblemDto | undefined;
    try {
      problem = (await response.json()) as ProblemDto;
    } catch {
      problem = undefined;
    }
    throw new ApiError(
      response.status,
      problem ?? {
        type: "about:blank",
        title: "Request Failed",
        status: response.status,
        detail: `HTTP ${String(response.status)}`,
        instance: path,
      },
    );
  }
  const body = (await response.json()) as LlmEndpointReadDto;
  const etag = response.headers.get("etag") ?? "";
  return { dto: body, etag };
}

export const api = {
  listEndpoints(): Promise<LlmEndpointReadDto[]> {
    return request("/llm-endpoints", { method: "GET" });
  },

  createEndpoint(payload: LlmEndpointCreateDto): Promise<EndpointWithEtag> {
    return requestWithEtag("/llm-endpoints", {
      method: "POST",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },

  getEndpoint(id: string): Promise<EndpointWithEtag> {
    return requestWithEtag(`/llm-endpoints/${encodeURIComponent(id)}`, { method: "GET" });
  },

  updateEndpoint(
    id: string,
    payload: LlmEndpointUpdateDto,
    ifMatch: Version,
  ): Promise<EndpointWithEtag> {
    return requestWithEtag(`/llm-endpoints/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey(), ifMatch });
  },

  testEndpoint(endpointId: string, modelId: string): Promise<EndpointTestResultDto> {
    return request(`/llm-endpoints/${encodeURIComponent(endpointId)}/test`, {
      method: "POST",
      body: JSON.stringify({ model_id: modelId }),
    }, { idempotencyKey: newIdempotencyKey() });
  },

  discoverModels(endpointId: string): Promise<DiscoverModelsResultDto> {
    return request(`/llm-endpoints/${encodeURIComponent(endpointId)}/discover-models`, {
      method: "POST",
    }, { idempotencyKey: newIdempotencyKey() });
  },

  endpointHealth(endpointId: string): Promise<EndpointHealthDto> {
    return request(`/llm-endpoints/${encodeURIComponent(endpointId)}/health`, {
      method: "GET",
    });
  },

  listModels(endpointId?: string): Promise<ModelReadDto[]> {
    const query = endpointId ? `?endpoint_id=${encodeURIComponent(endpointId)}` : "";
    return request(`/models${query}`, { method: "GET" });
  },

  createModel(payload: ModelCreateDto): Promise<ModelReadDto> {
    return request("/models", {
      method: "POST",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },

  getModel(id: string): Promise<ModelReadDto> {
    return request(`/models/${encodeURIComponent(id)}`, { method: "GET" });
  },

  updateModel(id: string, payload: ModelUpdateDto, ifMatch: Version): Promise<ModelReadDto> {
    return request(`/models/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey(), ifMatch });
  },

  probeModel(id: string): Promise<ProbeResultDto> {
    return request(`/models/${encodeURIComponent(id)}/probe`, {
      method: "POST",
    });
  },

  getCompatibility(modelId: string): Promise<CompatibilityViewDto> {
    return request(`/models/${encodeURIComponent(modelId)}/compatibility`, { method: "GET" });
  },

  listRoles(): Promise<RoleDefinitionDto[]> {
    return request("/roles", { method: "GET" });
  },

  listTeamTemplates(): Promise<TeamTemplateDto[]> {
    return request("/team-templates", { method: "GET" });
  },

  listAgents(): Promise<AgentSpecDto[]> {
    return request("/projects/example-project/agents", { method: "GET" });
  },

  createAgent(payload: AgentCreateDto): Promise<AgentSpecDto> {
    return request("/projects/example-project/agents", {
      method: "POST",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },

  updateAgent(
    agentId: string,
    payload: AgentUpdatePayload,
    ifMatch: Version,
  ): Promise<AgentSpecDto> {
    return request(`/agents/${encodeURIComponent(agentId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey(), ifMatch });
  },

  getProjectSettings(): Promise<ProjectSettingsDto> {
    return request("/projects/example-project/settings", { method: "GET" });
  },

  validateProtocol(path: string): Promise<CompileResultDto> {
    return request("/protocols/validate", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },

  compileAndPreflight(path: string): Promise<PreflightReportDto> {
    return request("/projects/example-project/compile", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },

  dryRun(path: string): Promise<DryRunProjectionDto> {
    return request("/projects/example-project/dry-run", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },

  startRun(protocolPath: string): Promise<RunDetailDto> {
    return request("/projects/example-project/runs", {
      method: "POST",
      body: JSON.stringify({ protocol_path: protocolPath }),
    }, { idempotencyKey: newIdempotencyKey() });
  },

  listRuns(projectId = "example-project"): Promise<RunDetailDto[]> {
    return request(`/projects/${encodeURIComponent(projectId)}/runs`, { method: "GET" });
  },

  getRun(runId: string): Promise<RunDetailDto> {
    return request(`/runs/${encodeURIComponent(runId)}`, { method: "GET" });
  },

  cancelRun(runId: string): Promise<RunDetailDto> {
    return request(`/runs/${encodeURIComponent(runId)}/cancel`, {
      method: "POST",
    }, { idempotencyKey: newIdempotencyKey() });
  },

  runTasks(runId: string): Promise<TaskDto[]> {
    return request(`/runs/${encodeURIComponent(runId)}/tasks`, { method: "GET" });
  },

  runEvents(runId: string): Promise<RunEventDto[]> {
    return request(`/runs/${encodeURIComponent(runId)}/events`, { method: "GET" });
  },

  listApprovals(): Promise<ApprovalDto[]> {
    return request("/approvals", { method: "GET" });
  },

  decideApproval(
    approvalId: string,
    decision: "approve" | "deny",
    version: Version,
  ): Promise<ApprovalDto> {
    return request(`/approvals/${encodeURIComponent(approvalId)}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    }, { idempotencyKey: newIdempotencyKey(), ifMatch: version });
  },

  runEvidence(runId: string): Promise<EvidenceDto[]> {
    return request(`/runs/${encodeURIComponent(runId)}/evidence`, { method: "GET" });
  },

  runClaimMap(runId: string): Promise<ClaimMapDto> {
    return request(`/runs/${encodeURIComponent(runId)}/claims`, { method: "GET" });
  },

  runUsage(runId: string): Promise<BudgetViewDto> {
    return request(`/runs/${encodeURIComponent(runId)}/usage`, { method: "GET" });
  },

  runExperiments(runId: string): Promise<ExperimentViewDto> {
    return request(`/runs/${encodeURIComponent(runId)}/experiments`, { method: "GET" });
  },

  runExport(runId: string): Promise<ExportBundleDto> {
    return request(`/runs/${encodeURIComponent(runId)}/export`, { method: "GET" });
  },
};