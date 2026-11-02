/**
 * 研究程序（program）控制面客户端（GOAL-20261103-104 EC-03）。
 *
 * 四条路由此前**没有任何前端消费者**：建程序 / 列程序 / 读详情 / 推进一轮。
 * `ProgramDetailDto` / `ProgramCreateDto` / `ProgramAdvanceDto` 早已在 `types.ts` 里
 * （GOAL-20261008-037 建的域面），只是没有 client 接线。
 *
 * `advance` 是**写面**（会真的启动一轮 run）⇒ 与其它写方法一样带幂等键：重试按服务端的
 * idempotency key 去重，语义仍是 at-least-once + 幂等 + 去重（不声称更强的投递保证）。
 */

import { getActiveProjectId } from "./activeProject";
import { newIdempotencyKey, request } from "./http";
import type { ProgramAdvanceDto, ProgramCreateDto, ProgramDetailDto } from "./types";

export const programsClient = {
  /** 本项目下的程序列表（读面：服务端按创建序返回）。 */
  list(projectId: string = getActiveProjectId()): Promise<ProgramDetailDto[]> {
    return request(`/projects/${encodeURIComponent(projectId)}/programs`, { method: "GET" });
  },
  create(
    payload: ProgramCreateDto,
    projectId: string = getActiveProjectId(),
  ): Promise<ProgramDetailDto> {
    return request(
      `/projects/${encodeURIComponent(projectId)}/programs`,
      { method: "POST", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  detail(programId: string): Promise<ProgramDetailDto> {
    return request(`/programs/${encodeURIComponent(programId)}`, { method: "GET" });
  },
  /**
   * 推进一轮：服务端按上一轮的判词决定「继续 / 停」，并回传**决定本身**
   * （`decision.cited_facts` 是被引 canonical 事实的原文）。
   */
  advance(programId: string): Promise<ProgramAdvanceDto> {
    return request(
      `/programs/${encodeURIComponent(programId)}/advance`,
      { method: "POST" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
