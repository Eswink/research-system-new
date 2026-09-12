/** 协议编译/预检/试运行客户端（受控模板路径或草稿修订引用）。 */

import { request } from "./http";
import type {
  CompileResultDto,
  DryRunProjectionDto,
  PreflightReportDto,
  ProtocolSourceDto,
} from "./types";

const PROJECT = "example-project";

/** 编译/预检来源：受控模板路径（旧协议）或已保存草稿的不可变修订（WP-B）。 */
export type ProtocolSource = string | { draft_id: string; draft_revision: number };

export function protocolSourceBody(source: ProtocolSource): ProtocolSourceDto {
  return typeof source === "string" ? { path: source } : { ...source };
}

export const protocolClient = {
  validate(source: ProtocolSource): Promise<CompileResultDto> {
    return request("/protocols/validate", {
      method: "POST",
      body: JSON.stringify(protocolSourceBody(source)),
    });
  },
  compileAndPreflight(source: ProtocolSource): Promise<PreflightReportDto> {
    return request(`/projects/${PROJECT}/compile`, {
      method: "POST",
      body: JSON.stringify(protocolSourceBody(source)),
    });
  },
  preflight(source: ProtocolSource): Promise<PreflightReportDto> {
    return request(`/projects/${PROJECT}/preflight`, {
      method: "POST",
      body: JSON.stringify(protocolSourceBody(source)),
    });
  },
  dryRun(source: ProtocolSource): Promise<DryRunProjectionDto> {
    return request(`/projects/${PROJECT}/dry-run`, {
      method: "POST",
      body: JSON.stringify(protocolSourceBody(source)),
    });
  },
};
