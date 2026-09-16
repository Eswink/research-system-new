/** ToolPack 面板的文案与解析辅助（PLAN-065）：组件只做呈现，口径集中在这里。 */

import type { ToolPackPermissionDiffDto, ToolPackSubmitResultDto } from "../../api/types";

/** 提交结果的口径：`pending_approval` **不是**"已生效"。 */
export function submitStatusText(outcome: ToolPackSubmitResultDto, zh: boolean): string {
  const status = outcome.status;
  if (status === "pending_approval") {
    return zh
      ? `已登记为待批准更新（${outcome.pack.id}）：权限扩张未生效，` +
          "需在下方横幅批准后才替换生效版本"
      : `Registered as a pending update (${outcome.pack.id}): the expansion is NOT ` +
          "effective until approved below";
  }
  if (status === "installed") {
    return zh
      ? `已安装 ${outcome.pack.id}：digest 由控制面重算校验（不采信请求里的字面量）`
      : `Installed ${outcome.pack.id}: digest recomputed and verified server-side`;
  }
  if (status === "updated") {
    return zh
      ? `已更新 ${outcome.pack.id} 并立即生效（无权限扩张）`
      : `Updated ${outcome.pack.id}; effective now (no expansion)`;
  }
  if (status === "unchanged") {
    return zh
      ? "内容与生效版本一致（digest 相同），未做改动"
      : "Content matches the effective version (same digest); nothing changed";
  }
  return `${zh ? "结果" : "Result"}: ${status}`;
}

export function installHint(zh: boolean): string {
  if (zh) {
    return (
      "提交完整 manifest（JSON，含 digest）：服务端重算内容 digest 并要求与 digest 字段相等，" +
      "不一致返回 422。新增 capability / network domain / credential 属于权限扩张，" +
      "不会立即生效。"
    );
  }
  return (
    "Submit the full manifest (JSON, including digest): the server recomputes the " +
    "content digest and requires it to equal the declared one (422 otherwise). New " +
    "capabilities / network domains / credentials count as an expansion and do NOT " +
    "take effect immediately."
  );
}

export function parseManifest(text: string, zh: boolean): Record<string, unknown> | string {
  try {
    const parsed: unknown = JSON.parse(text);
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
      return zh ? "manifest 必须是 JSON 对象" : "manifest must be a JSON object";
    }
    return parsed as Record<string, unknown>;
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    return `${zh ? "JSON 解析失败" : "JSON parse failed"}: ${detail}`;
  }
}

/** 权限 diff → 人类可读行（空类别不出现；空 diff 给明确说明而不是空白）。 */
export function diffLines(diff: ToolPackPermissionDiffDto, zh: boolean): string[] {
  const groups: [string, string, string[]][] = [
    ["capability", zh ? "新增 capability" : "added capability", diff.added_capabilities],
    ["network", zh ? "新增 network domain" : "added network domain", diff.added_network_domains],
    ["credential", zh ? "新增 credential" : "added credential", diff.added_credentials],
  ];
  const lines = groups
    .filter(([, , values]) => values.length > 0)
    .map(([, label, values]) => `${label}: ${values.join(", ")}`);
  return lines.length > 0 ? lines : [zh ? "无权限差异" : "no permission difference"];
}
