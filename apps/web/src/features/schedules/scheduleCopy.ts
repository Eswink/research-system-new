/**
 * 调度页面文案与事实格式化（EC-03）。
 *
 * 一条口径：**没有事实就说没有**。`last_outcome` 为 null 时渲染成"未运行"
 * （而不是"OK"）；没有执行体时按钮禁用并说明原因，而不是点了没反应。
 */

import type { ScheduleEntryDto } from "../../api/types";

/** 无运行事实时的占位（与后端 `ScheduleRuntime.last_outcome_or_unknown` 同口径）。 */
export const OUTCOME_UNKNOWN = "UNKNOWN";

export const MIN_INTERVAL_SECONDS = 1;
export const MAX_INTERVAL_SECONDS = 86400;

export function outcomeOf(row: ScheduleEntryDto): string {
  return row.last_outcome ?? OUTCOME_UNKNOWN;
}

/** 人类可读的最近执行时间（截到分钟；无事实 → null）。 */
export function lastRunText(row: ScheduleEntryDto): string | null {
  if (row.last_run_at === null) return null;
  return row.last_run_at.slice(0, 16).replace("T", " ");
}

/** "3 次 · 最近 2026-09-16 08:00 · OK"。 */
export function factSummary(row: ScheduleEntryDto, zh: boolean): string {
  const minutes = String(row.run_count);
  const runs = zh ? `${minutes} 次` : `${minutes} runs`;
  const when = lastRunText(row) ?? (zh ? "未运行" : "never ran");
  return [runs, when, outcomeOf(row)].join(" · ");
}

export function canTrigger(row: ScheduleEntryDto): boolean {
  return row.enabled && row.executor_attached;
}

export function triggerBlockReason(row: ScheduleEntryDto, zh: boolean): string {
  if (!row.enabled) return zh ? "已停用：启用后才能触发" : "Disabled: enable it first";
  if (!row.executor_attached) {
    return zh ? "本进程没有该作业的执行体" : "No executor for this job in this process";
  }
  return "";
}

export function executorLabel(row: ScheduleEntryDto, zh: boolean): string {
  if (row.executor_attached) return zh ? "已连接" : "attached";
  return zh ? "无执行体" : "none";
}

export function intervalError(value: string, zh: boolean): string | null {
  const seconds = Number(value);
  if (value.trim() === "" || Number.isNaN(seconds)) {
    return zh ? "间隔必须是数字" : "Interval must be a number";
  }
  if (seconds < MIN_INTERVAL_SECONDS || seconds > MAX_INTERVAL_SECONDS) {
    const range = `${String(MIN_INTERVAL_SECONDS)}~${String(MAX_INTERVAL_SECONDS)}`;
    return zh ? `间隔需在 ${range} 秒之间` : `Interval must be ${range} seconds`;
  }
  return null;
}

export const schedulePageCopy = {
  description: (zh: boolean): string =>
    zh
      ? "调度定义（可写）与运行事实：执行体仍是进程内守护线程，定义只决定启停与间隔（下一轮生效）；触发调用与定时相同的 pass。"
      : [
          "Schedule definitions (writable) plus runtime facts: the executor is still the ",
          "in-process daemon thread; a definition only sets enable/interval (next tick) and ",
          "trigger runs the same pass as the timer.",
        ].join(""),
  createTitle: (zh: boolean): string => (zh ? "登记定义" : "New definition"),
  createHint: (zh: boolean): string =>
    zh
      ? "只能绑定既有作业词表（不新增执行路径）"
      : "Bind an existing job only (no new execution path)",
  namePlaceholder: (zh: boolean): string => (zh ? "名称（小写字母/数字/下划线）" : "name_lowercase"),
  intervalPlaceholder: (zh: boolean): string => (zh ? "间隔（秒）" : "interval (s)"),
  create: (zh: boolean): string => (zh ? "登记" : "Create"),
  toggleOn: (zh: boolean): string => (zh ? "启用" : "Enable"),
  toggleOff: (zh: boolean): string => (zh ? "停用" : "Disable"),
  trigger: (zh: boolean): string => (zh ? "触发一次" : "Trigger once"),
  unavailableTitle: (zh: boolean): string => (zh ? "调度写面不可用" : "Scheduling unavailable"),
  empty: (zh: boolean): string => (zh ? "尚无调度定义" : "No schedules"),
};
