/** 团队与项目设置客户端（Role/Agent/模板/项目设置）。 */

import { newIdempotencyKey, request } from "./http";
import type {
  AgentCreateDto,
  AgentSpecDto,
  AgentUpdatePayload,
  ProjectSettingsDto,
  RoleDefinitionDto,
  TeamTemplateDto,
  Version,
} from "./types";

const PROJECT = "example-project";

export const teamClient = {
  listRoles(): Promise<RoleDefinitionDto[]> {
    return request("/roles", { method: "GET" });
  },
  listTeamTemplates(): Promise<TeamTemplateDto[]> {
    return request("/team-templates", { method: "GET" });
  },
  listAgents(): Promise<AgentSpecDto[]> {
    return request(`/projects/${PROJECT}/agents`, { method: "GET" });
  },
  createAgent(payload: AgentCreateDto): Promise<AgentSpecDto> {
    return request(
      `/projects/${PROJECT}/agents`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  updateAgent(
    agentId: string,
    payload: AgentUpdatePayload,
    ifMatch: Version,
  ): Promise<AgentSpecDto> {
    return request(
      `/agents/${encodeURIComponent(agentId)}`,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      },
      { idempotencyKey: newIdempotencyKey(), ifMatch },
    );
  },
  /** 克隆 Agent 配置实例（WP-B；new_id 缺省由服务端生成）。 */
  cloneAgent(agentId: string, newId?: string): Promise<AgentSpecDto> {
    return request(
      `/agents/${encodeURIComponent(agentId)}/clone`,
      {
        method: "POST",
        body: JSON.stringify({ new_id: newId }),
      },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  /** 删除用户 Agent 记录（WP-B G10；契约基线不可删 → 404）。 */
  removeAgent(agentId: string): Promise<void> {
    return request(
      `/agents/${encodeURIComponent(agentId)}`,
      { method: "DELETE" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  /** 创建用户自定义 Role（WP-B；同 examples schema 校验）。 */
  createCustomRole(document: Record<string, unknown>): Promise<RoleDefinitionDto> {
    return request(
      "/roles/custom",
      { method: "POST", body: JSON.stringify(document) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  /** 创建用户自定义 TeamTemplate（WP-B）。 */
  createCustomTeamTemplate(document: Record<string, unknown>): Promise<TeamTemplateDto> {
    return request(
      "/team-templates/custom",
      { method: "POST", body: JSON.stringify(document) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  getProjectSettings(): Promise<ProjectSettingsDto> {
    return request(`/projects/${PROJECT}/settings`, { method: "GET" });
  },
  /** 项目设置 PUT 无版本契约（last-write-wins）；仍需幂等键。 */
  saveProjectSettings(payload: ProjectSettingsDto): Promise<ProjectSettingsDto> {
    return request(
      `/projects/${PROJECT}/settings`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
