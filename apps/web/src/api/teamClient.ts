/** 团队与项目设置客户端（Role/Agent/模板/项目设置）。 */

import type {
  AgentCreateDto,
  AgentSpecDto,
  AgentUpdatePayload,
  ProjectSettingsDto,
  RoleDefinitionDto,
  TeamTemplateDto,
  Version,
} from "./types";
import { newIdempotencyKey, request } from "./http";

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
    return request(`/projects/${PROJECT}/agents`, {
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
    return request(`/projects/${PROJECT}/settings`, { method: "GET" });
  },
  /** 项目设置 PUT 无版本契约（last-write-wins）；仍需幂等键。 */
  saveProjectSettings(payload: ProjectSettingsDto): Promise<ProjectSettingsDto> {
    return request(`/projects/${PROJECT}/settings`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }, { idempotencyKey: newIdempotencyKey() });
  },
};
