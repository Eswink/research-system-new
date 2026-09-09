/** 协议编译/预检/试运行客户端（受控模板路径）。 */

import { request } from "./http";
import type { CompileResultDto, DryRunProjectionDto, PreflightReportDto } from "./types";

const PROJECT = "example-project";

export const protocolClient = {
  validate(path: string): Promise<CompileResultDto> {
    return request("/protocols/validate", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },
  compileAndPreflight(path: string): Promise<PreflightReportDto> {
    return request(`/projects/${PROJECT}/compile`, {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },
  preflight(path: string): Promise<PreflightReportDto> {
    return request(`/projects/${PROJECT}/preflight`, {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },
  dryRun(path: string): Promise<DryRunProjectionDto> {
    return request(`/projects/${PROJECT}/dry-run`, {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  },
};
