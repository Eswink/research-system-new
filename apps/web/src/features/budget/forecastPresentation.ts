import type { CostForecastDto, ResourceType } from "../../api/types";

/** 前端展示用的资源类型清单（后端 ResourceType 的展示子集；未知值不伪造）。 */
export const ADJUSTABLE_RESOURCES: readonly ResourceType[] = [
  "MODEL_TOKENS",
  "MODEL_REQUESTS",
  "MODEL_COST",
  "CPU_TIME",
  "GPU_TIME",
  "WALL_CLOCK",
  "AGENT_TURNS",
];

export function forecastRemainingText(
  remaining: number | null,
  unit: string,
  zh: boolean,
): string {
  if (remaining === null) return zh ? "不可计量（≠0）" : "UNKNOWN (not 0)";
  return `${String(remaining)} ${unit}`;
}

/** 指标卡摘要：行数 + 不可计量条目数（null 视图 → "—"，不当作 0）。 */
export function forecastSummary(view: CostForecastDto | null): string {
  if (view === null) return "—";
  const lines = String(view.lines.length);
  if (view.cost_status === "NO_DATA") return `${lines} · NO_DATA`;
  if (view.unknown_cost_entries === 0) return lines;
  return `${lines} · ${String(view.unknown_cost_entries)} UNKNOWN`;
}
