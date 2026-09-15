/**
 * Control Plane API 门面（apps/web 唯一网络入口）。
 *
 * 实现按职责拆分到 endpointsClient/modelsClient/teamClient/protocolClient/
 * runClient/inspectionClient/operationsClient/draftClient；本文件只组合它们，
 * 保持既有 `api.*` 调用面与 ETag 结果形状（`.dto`/`.etag`）向后兼容。
 *
 * 约束：只消费 src/api/types.ts 的 DTO；mutating 带 Idempotency-Key；
 * 带版本资源带 If-Match；Key 永不写入 localStorage/URL/logs。
 */

import { endpointsClient } from "./endpointsClient";
import { artifactClient } from "./artifactClient";
import { experimentClient } from "./experimentClient";
import { memoryClient } from "./memoryClient";
import { notificationsClient } from "./notificationClient";
import { ApiError } from "./http";
import { inspectionClient } from "./inspectionClient";
import type { EndpointWithEtag } from "./legacyShapes";
import { libraryClient } from "./libraryClient";
import { modelsClient } from "./modelsClient";
import { operationsClient } from "./operationsClient";
import { opsViewClient } from "./opsViewClient";
import { opsControlClient } from "./opsControlClient";
import { policyClient } from "./policyClient";
import { projectsClient } from "./projectsClient";
import { protocolClient, type ProtocolSource } from "./protocolClient";
import { runClient } from "./runClient";
import { teamClient } from "./teamClient";
import { toolProvidersClient } from "./toolProvidersClient";
import { workspaceSnapshotClient } from "./workspaceSnapshotClient";
import type {
  AgentCreateDto,
  AgentSpecDto,
  AgentUpdatePayload,
  AlertRulePatchDto,
  AlertRuleWriteDto,
  IncidentAssignDto,
  IncidentCloseDto,
  IncidentDeclareDto,
  LlmEndpointCreateDto,
  LlmEndpointReadDto,
  LlmEndpointUpdateDto,
  ModelCreateDto,
  ModelReadDto,
  ModelUpdateDto,
  ProjectSettingsDto,
  ResourceKind,
  ResourceType,
  Version,
} from "./types";

export { ApiError };
export type { EndpointWithEtag };

function withDto(r: { data: LlmEndpointReadDto; etag: Version }): EndpointWithEtag {
  return { dto: r.data, etag: r.etag };
}

export const api = {
  // ── endpoints ─
  listEndpoints: () => endpointsClient.list(),
  createEndpoint: (payload: LlmEndpointCreateDto): Promise<EndpointWithEtag> =>
    endpointsClient.create(payload).then(withDto),
  getEndpoint: (id: string): Promise<EndpointWithEtag> => endpointsClient.get(id).then(withDto),
  updateEndpoint: (
    id: string,
    payload: LlmEndpointUpdateDto,
    ifMatch: Version,
  ): Promise<EndpointWithEtag> => endpointsClient.update(id, payload, ifMatch).then(withDto),
  testEndpoint: (endpointId: string, modelId: string) => endpointsClient.test(endpointId, modelId),
  discoverModels: (endpointId: string) => endpointsClient.discoverModels(endpointId),
  endpointHealth: (endpointId: string) => endpointsClient.health(endpointId),
  removeEndpoint: (endpointId: string) => endpointsClient.remove(endpointId),

  // ── models ──
  listModels: (endpointId?: string): Promise<ModelReadDto[]> => modelsClient.list(endpointId),
  createModel: (payload: ModelCreateDto): Promise<ModelReadDto> =>
    modelsClient.create(payload).then((r) => r.data),
  getModel: (id: string) => modelsClient.get(id),
  updateModel: (id: string, payload: ModelUpdateDto, ifMatch: Version) =>
    modelsClient.update(id, payload, ifMatch),
  probeModel: (id: string) => modelsClient.probe(id),
  removeModel: (modelId: string) => modelsClient.remove(modelId),
  getCompatibility: (modelId: string) => modelsClient.compatibility(modelId),

  // ── projects（WP-C/PLAN-041：注册表 + 归档语义；无 DELETE）──
  listProjects: () => projectsClient.list(),
  createProject: (name: string) => projectsClient.create({ name }),
  updateProject: (
    projectId: string,
    payload: { name?: string | null; status?: "ACTIVE" | "ARCHIVED" | null },
  ) => projectsClient.update(projectId, payload),

  // ── team ──
  listRoles: () => teamClient.listRoles(),
  listTeamTemplates: () => teamClient.listTeamTemplates(),
  listAgents: (): Promise<AgentSpecDto[]> => teamClient.listAgents(),
  createAgent: (payload: AgentCreateDto) => teamClient.createAgent(payload),
  updateAgent: (agentId: string, payload: AgentUpdatePayload, ifMatch: Version) =>
    teamClient.updateAgent(agentId, payload, ifMatch),
  cloneAgent: (agentId: string, newId?: string) => teamClient.cloneAgent(agentId, newId),
  removeAgent: (agentId: string) => teamClient.removeAgent(agentId),
  createCustomRole: (document: Record<string, unknown>) => teamClient.createCustomRole(document),
  createCustomTeamTemplate: (document: Record<string, unknown>) =>
    teamClient.createCustomTeamTemplate(document),
  getProjectSettings: (): Promise<ProjectSettingsDto> => teamClient.getProjectSettings(),
  saveProjectSettings: (payload: ProjectSettingsDto) => teamClient.saveProjectSettings(payload),

  // ── protocol ──
  validateProtocol: (source: ProtocolSource) => protocolClient.validate(source),
  compileAndPreflight: (source: ProtocolSource) => protocolClient.compileAndPreflight(source),
  preflight: (source: ProtocolSource) => protocolClient.preflight(source),
  dryRun: (source: ProtocolSource) => protocolClient.dryRun(source),

  // ── runs & approvals ──
  startRun: (source: string | { draft_id: string; draft_revision: number }) =>
    runClient.start(source),
  listRuns: (projectId?: string) => runClient.list(projectId),
  getRun: (runId: string) => runClient.get(runId),
  cancelRun: (runId: string) => runClient.cancel(runId),
  pauseRun: (runId: string) => runClient.pause(runId),
  resumeRun: (runId: string) => runClient.resume(runId),
  runTasks: (runId: string) => runClient.tasks(runId),
  runEvents: (runId: string) => runClient.events(runId),
  listApprovals: () => runClient.listApprovals(),
  runApprovals: (runId: string) => runClient.runApprovals(runId),
  decideApproval: (approvalId: string, decision: "approve" | "deny", version: Version) =>
    runClient.decideApproval(approvalId, decision, version),

  // ── inspection ─
  runEvidence: (runId: string) => inspectionClient.evidence(runId),
  runClaimMap: (runId: string) => inspectionClient.claimMap(runId),
  runUsage: (runId: string) => inspectionClient.usage(runId),
  /** 成本预测投影（只覆盖已预留部分；PLAN-046）。 */
  runCostForecast: (runId: string) => inspectionClient.costForecast(runId),
  /** 预算调整（走 BudgetLedger：release 既有预留 + reserve 新额度）。 */
  adjustRunBudget: (
    runId: string,
    adjustments: { resource_type: ResourceType; quantity: number; unit: string }[],
  ) => runClient.adjustBudget(runId, adjustments),
  runExperiments: (runId: string) => inspectionClient.experiments(runId),
  runExport: (runId: string) => inspectionClient.export(runId),
  runDeliverable: (runId: string) => inspectionClient.deliverable(runId),
  runLineage: (runId: string) => inspectionClient.lineage(runId),
  projectLineage: (projectId?: string) => inspectionClient.projectLineage(projectId),

  // ── tool providers（PLAN-043 只读目录）──
  listToolProviders: () => toolProvidersClient.list(),

  // ── library（PLAN-044：prompts/datasets/notebooks 共享目录）──
  listLibrary: (kind: ResourceKind) => libraryClient.list(kind),
  createLibrary: (payload: {
    kind: ResourceKind;
    name: string;
    description?: string;
    content_ref?: string | null;
    tags?: string[];
  }) => libraryClient.create(payload),
  updateLibrary: (resourceId: string, payload: { name?: string; status?: "ACTIVE" | "ARCHIVED" }) =>
    libraryClient.update(resourceId, payload),

  // ── ops 只读投影（PLAN-045：alerts/incidents/schedules/data-health）──
  opsAlerts: () => opsViewClient.alerts(),
  opsIncidents: () => opsViewClient.incidents(),
  opsSchedules: () => opsViewClient.schedules(),
  opsDataHealth: () => opsViewClient.dataHealth(),

  // ── ops 写面（PLAN-059：告警规则 CRUD + 事故处置）──
  opsAlertRules: () => opsControlClient.rules(),
  createAlertRule: (payload: AlertRuleWriteDto) => opsControlClient.createRule(payload),
  patchAlertRule: (ruleId: string, payload: AlertRulePatchDto) =>
    opsControlClient.patchRule(ruleId, payload),
  deleteAlertRule: (ruleId: string) => opsControlClient.deleteRule(ruleId),
  declareIncident: (payload: IncidentDeclareDto) => opsControlClient.declareIncident(payload),
  assignIncident: (incidentId: string, payload: IncidentAssignDto) =>
    opsControlClient.assignIncident(incidentId, payload),
  closeIncident: (incidentId: string, payload: IncidentCloseDto) =>
    opsControlClient.closeIncident(incidentId, payload),

  // ── operations ─
  runTelemetry: (runId: string) => operationsClient.telemetry(runId),
  runCost: (runId: string) => operationsClient.cost(runId),
  evaluationsTrend: (datasetId?: string, expectedDigests: string[] = [], limit?: number) =>
    operationsClient.trend(datasetId, expectedDigests, limit),
  clusterWorkers: () => operationsClient.clusterWorkers(),
  runPlacement: (runId: string) => operationsClient.placement(runId),
  dailyCost: (dateFrom?: string, dateTo?: string) =>
    operationsClient.dailyCost(dateFrom, dateTo),
  projectCostForecast: (projectId?: string, horizonDays?: number) =>
    operationsClient.projectCostForecast(projectId, horizonDays),

  // ── artifacts（WP-C 只读）──
  listRunArtifacts: (runId: string) => artifactClient.listForRun(runId),
  getArtifact: (artifactId: string) => artifactClient.get(artifactId),
  artifactContentUrl: (artifactId: string) => artifactClient.contentUrl(artifactId),
  artifactPreviewText: (artifactId: string) => artifactClient.contentText(artifactId),
  artifactDiff: (leftId: string, rightId: string) => artifactClient.diff(leftId, rightId),

  // ── 工作区快照（PLAN-058 只读）──
  workspaceSnapshotCapability: () => workspaceSnapshotClient.capability(),
  runWorkspaceSnapshots: (runId: string) => workspaceSnapshotClient.forRun(runId),
  workspaceSnapshotFiles: (digest: string) => workspaceSnapshotClient.files(digest),
  workspaceSnapshotDiff: (left: string, right: string) =>
    workspaceSnapshotClient.diff(left, right),

  // ── experiments（WP-E + G14 队列）──
  projectExperiments: () => experimentClient.listForProject(),
  experimentPlans: (state?: string) => experimentClient.listPlans(state),
  createExperimentPlan: (payload: {
    name: string;
    hypothesis?: string | null;
    task_contract_ref?: string | null;
  }) => experimentClient.createPlan(payload),
  archiveExperimentPlan: (planId: string) => experimentClient.archivePlan(planId),
  experimentQueue: () => experimentClient.listQueue(),
  enqueueExperiment: (
    planId: string,
    payload: {
      protocol_path?: string | null;
      draft_id?: string | null;
      draft_revision?: number | null;
      not_before?: string | null;
    },
  ) => experimentClient.enqueue(planId, payload),
  rescheduleExperiment: (entryId: string, notBefore: string | null) =>
    experimentClient.reschedule(entryId, notBefore),
  cancelExperiment: (entryId: string) => experimentClient.cancel(entryId),

  // ── memory（WP-F）──
  projectMemory: () => memoryClient.list(),
  proposeMemory: (payload: {
    tier: string;
    kind: string;
    content: string;
    provenance: string;
    confidence: number;
    curator_approved: boolean;
  }) => memoryClient.propose(payload),
  deleteMemory: (memoryId: string) => memoryClient.remove(memoryId),

  // ── policy（WP-C PLAN-049）──
  policyCapabilities: () => policyClient.capabilities(),

  // ── notifications（WP-G）──
  notifications: () => notificationsClient.list(),
  markNotificationRead: (eventId: string) => notificationsClient.markRead(eventId),
};
