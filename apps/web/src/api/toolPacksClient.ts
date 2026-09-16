/** ToolPack 供应链写面客户端（GOAL-003 / PLAN-20260915-065）。
 *
 * 写面约束与主 client 一致：mutating 带 Idempotency-Key。
 * 语义提醒（与后端同源）：`install` 是"提交"，成功不等于"已生效"——
 * 权限扩张会返回 `pending_approval` 且**生效 digest 不变**，需要再调 approveUpdate。
 */

import { newIdempotencyKey, request } from "./http";
import type {
  ToolPackListDto,
  ToolPackSubmitResultDto,
} from "./types";

function packPath(packId: string, action: string): string {
  return `/tool-packs/${encodeURIComponent(packId)}/${action}`;
}

export const toolPacksClient = {
  list(): Promise<ToolPackListDto> {
    return request("/tool-packs", { method: "GET" });
  },
  /** 提交安装/更新：manifest 文档（含 digest）由控制面重算校验。 */
  install(manifest: Record<string, unknown>): Promise<ToolPackSubmitResultDto> {
    return request(
      "/tool-packs/install",
      { method: "POST", body: JSON.stringify({ manifest }) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  /** 批准待批准的权限扩张：此刻新版本才成为生效版本。 */
  approveUpdate(packId: string): Promise<ToolPackSubmitResultDto> {
    return request(
      packPath(packId, "approve-update"),
      { method: "POST" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  revoke(packId: string, reason: string): Promise<ToolPackSubmitResultDto> {
    return request(
      packPath(packId, "revoke"),
      { method: "POST", body: JSON.stringify({ reason }) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
