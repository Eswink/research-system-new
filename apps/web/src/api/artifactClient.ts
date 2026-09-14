/** Artifact 只读客户端（WP-C）：列表 / 元数据 / 内容（预览走文本 fetch）。 */

import { API_BASE, request } from "./http";
import type { ArtifactDiffDto, ArtifactDto } from "./types";

export const artifactClient = {
  listForRun(runId: string): Promise<ArtifactDto[]> {
    return request(`/runs/${encodeURIComponent(runId)}/artifacts`, { method: "GET" });
  },
  /** 两制品内容 diff（PLAN-047；不可比时 200 + available=false + reason）。 */
  diff(leftId: string, rightId: string): Promise<ArtifactDiffDto> {
    return request(
      `/artifacts/${encodeURIComponent(leftId)}/diff/${encodeURIComponent(rightId)}`,
      { method: "GET" },
    );
  },
  get(artifactId: string): Promise<ArtifactDto> {
    return request(`/artifacts/${encodeURIComponent(artifactId)}`, { method: "GET" });
  },
  /** 下载/预览直链（浏览器原生处理 Content-Disposition；不经 JSON 包装层）。 */
  contentUrl(artifactId: string): string {
    return `${API_BASE}/artifacts/${encodeURIComponent(artifactId)}/content`;
  },
  /** 小体量文本预览（>512KB 拒绝，防止把大 blob 拉进内存）。 */
  async contentText(artifactId: string): Promise<string> {
    const response = await fetch(this.contentUrl(artifactId));
    if (!response.ok) throw new Error(`artifact content unavailable (${String(response.status)})`);
    const text = await response.text();
    if (text.length > 512 * 1024) return `${text.slice(0, 512 * 1024)}\n… truncated`;
    return text;
  },
};
