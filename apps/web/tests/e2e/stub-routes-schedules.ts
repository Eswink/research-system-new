/**
 * 调度写面替身（PLAN-20260915-066 EC-03 / AC-05）。
 *
 * 与真后端同一因果：定义（配置）与运行事实（本进程观测）分开呈现；trigger 立即
 * 写回运行事实；停用后 trigger 409、且守护线程读的 `due()` 不再授予它。静态替身
 * 表达不了状态迁移，因此用模块级可变状态 + `resetScheduleStub()`。
 *
 * 替身里的执行体接线镜像测试装配：只有 lease_recovery 有执行体（其余三项在
 * console 上表现为"无执行体"且触发按钮禁用）。权威口径由后端测试与 live 套件证明。
 */

import type { StubRoute } from "./stub-routes";

const NOW = "2026-09-16T00:00:00Z";
const MIN_INTERVAL = 1;
const MAX_INTERVAL = 86400;
const NAME_RE = /^[a-z][a-z0-9_]{2,40}$/;

const JOB_PURPOSE: Record<string, string> = {
  lease_recovery: "恢复过期 lease 并推进 LOST 转换",
  outbox_relay: "中继 transactional outbox 事件",
  retention: "按 retention policy 清理 artifact",
  worker_reaper: "把心跳过期的 worker 标记为 LOST",
};

interface StubSchedule {
  name: string;
  job: string;
  interval_seconds: number;
  enabled: boolean;
  builtin: boolean;
  note: string;
  executor_attached: boolean;
  run_count: number;
  last_run_at: string | null;
  last_outcome: string | null;
  last_error: string | null;
  next_due_at: string | null;
}

const NOTE =
  "执行体仍是进程内守护线程：定义只决定 enabled/interval（下一轮生效），" +
  "trigger 调用与定时 pass 相同的函数并写下同一份运行事实；新增定义只能绑定既有 " +
  "job 词表——控件不新增执行路径，没有执行体的作业会在读面标注 executor_attached=false。";

function builtin(name: string, interval: number, attached: boolean): StubSchedule {
  return {
    name,
    job: name,
    interval_seconds: interval,
    enabled: true,
    builtin: true,
    note: "",
    executor_attached: attached,
    run_count: 0,
    last_run_at: null,
    last_outcome: null,
    last_error: null,
    next_due_at: null,
  };
}

let schedules: StubSchedule[] = [];

/** 每个用例前复位（定义与运行事实跨用例会串味）。 */
export function resetScheduleStub(): void {
  schedules = [
    builtin("lease_recovery", 30, true),
    builtin("outbox_relay", 5, false),
    builtin("retention", 3600, false),
    builtin("worker_reaper", 15, false),
  ];
}

resetScheduleStub();

type StubResult = { status: number; body: unknown };

interface Draft {
  name: string;
  job: string;
  interval: number;
  note: string;
}

function conflict(detail: string): StubResult {
  return { status: 409, body: { title: "Schedule Conflict", detail } };
}

function invalid(detail: string): StubResult {
  return { status: 422, body: { title: "Invalid Schedule Definition", detail } };
}

function notFound(name: string): StubResult {
  const body = { title: "Schedule Not Found", detail: `unknown schedule: ${name}` };
  return { status: 404, body };
}

function find(name: string): StubSchedule | undefined {
  return schedules.find((item) => item.name === name);
}

function replace(next: StubSchedule): StubSchedule {
  schedules = schedules.map((item) => (item.name === next.name ? next : item));
  return next;
}

function validate(draft: Draft): StubResult | null {
  if (!NAME_RE.test(draft.name)) return invalid("schedule name must match ^[a-z][a-z0-9_]{2,40}$");
  if (!(draft.job in JOB_PURPOSE)) return invalid(`unknown job: ${draft.job}`);
  const outOfRange = draft.interval < MIN_INTERVAL || draft.interval > MAX_INTERVAL;
  if (Number.isNaN(draft.interval) || outOfRange) {
    const range = `${String(MIN_INTERVAL)}..${String(MAX_INTERVAL)}`;
    return invalid(`interval_seconds must be within [${range}]`);
  }
  if (draft.note.length > 200) return invalid("note must be <= 200 characters");
  return null;
}

function draftOf(raw: Record<string, unknown>, fallbackJob?: string): Draft {
  return {
    name: String(raw.name ?? ""),
    job: String(raw.job ?? fallbackJob ?? ""),
    interval: Number(raw.interval_seconds),
    note: String(raw.note ?? ""),
  };
}

function create(raw: Record<string, unknown>): StubResult {
  const draft = draftOf(raw);
  const bad = validate(draft);
  if (bad !== null) return bad;
  if (find(draft.name) !== undefined) {
    return conflict(`schedule name already exists: ${draft.name}`);
  }
  const created: StubSchedule = {
    ...builtin(draft.name, draft.interval, draft.job === "lease_recovery"),
    job: draft.job,
    enabled: raw.enabled !== false,
    builtin: false,
    note: draft.note,
  };
  schedules = [...schedules, created];
  return { status: 201, body: created };
}

function update(name: string, raw: Record<string, unknown>): StubResult {
  const current = find(name);
  if (current === undefined) return notFound(name);
  const draft = draftOf({ ...raw, name }, current.job);
  if (raw.interval_seconds !== undefined && raw.interval_seconds !== null) {
    const bad = validate(draft);
    if (bad !== null) return bad;
  }
  const flip = raw.enabled === undefined || raw.enabled === null;
  const enabled = flip ? current.enabled : Boolean(raw.enabled);
  return {
    status: 200,
    body: replace({
      ...current,
      enabled,
      interval_seconds: Number(raw.interval_seconds ?? current.interval_seconds),
      next_due_at: enabled ? NOW : null,
    }),
  };
}

function trigger(name: string): StubResult {
  const current = find(name);
  if (current === undefined) return notFound(name);
  if (!current.enabled) return conflict(`schedule is disabled: ${name}`);
  if (!current.executor_attached) {
    return conflict(`no executor attached for job ${current.job}: ${name}`);
  }
  const ran = replace({
    ...current,
    run_count: current.run_count + 1,
    last_run_at: NOW,
    last_outcome: "OK",
    last_error: null,
    next_due_at: NOW,
  });
  return { status: 200, body: ran };
}

export const SCHEDULE_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/ops\/schedules$/,
    handler: () => ({
      status: 200,
      body: {
        schedules,
        jobs: Object.entries(JOB_PURPOSE).map(([job, purpose]) => ({ job, purpose })),
        note: NOTE,
        management_available: true,
        management_reason: null,
      },
    }),
  },
  {
    method: "POST",
    pattern: /^\/ops\/schedules$/,
    handler: (_url, body) => create((body ?? {}) as Record<string, unknown>),
  },
  {
    method: "PATCH",
    pattern: /^\/ops\/schedules\/[^/]+$/,
    handler: (url, body) => {
      const name = decodeURIComponent(url.pathname.split("/").at(-1) ?? "");
      return update(name, (body ?? {}) as Record<string, unknown>);
    },
  },
  {
    method: "POST",
    pattern: /^\/ops\/schedules\/[^/]+\/trigger$/,
    handler: (url) => trigger(decodeURIComponent(url.pathname.split("/").at(-2) ?? "")),
  },
];
