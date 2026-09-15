/** 工作区快照只读客户端（PLAN-20260915-058）：能力 / 文件树 / 文件级 diff。 */

import { request } from "./http";
import type {
  RunWorkspaceSnapshotsDto,
  WorkspaceSnapshotCapabilityDto,
  WorkspaceSnapshotDiffDto,
  WorkspaceSnapshotTreeDto,
} from "./types";

export const workspaceSnapshotClient = {
  capability(): Promise<WorkspaceSnapshotCapabilityDto> {
    return request("/workspace-snapshots", { method: "GET" });
  },
  /** run 记录过的快照 digest 与保留状态（不推断 run→工作区绑定）。 */
  forRun(runId: string): Promise<RunWorkspaceSnapshotsDto> {
    return request(`/runs/${encodeURIComponent(runId)}/workspace-snapshots`, { method: "GET" });
  },
  /** 单个保留中快照的文件清单（digest 含 `:`，必须整体编码）。 */
  files(digest: string): Promise<WorkspaceSnapshotTreeDto> {
    return request(`/workspace-snapshots/${encodeURIComponent(digest)}/files`, { method: "GET" });
  },
  /** 两个保留中快照的文件级 diff（只比路径/大小/sha256）。 */
  diff(left: string, right: string): Promise<WorkspaceSnapshotDiffDto> {
    return request(
      `/workspace-snapshots/${encodeURIComponent(left)}/diff/${encodeURIComponent(right)}`,
      { method: "GET" },
    );
  },
};
