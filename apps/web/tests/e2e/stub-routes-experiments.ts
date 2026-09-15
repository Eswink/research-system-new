/**
 * 实验队列/计划 API 替身路由（PLAN-20260915-052 WP-D）。
 *
 * 形状遵循真实 DTO（services/api/dto/experiments.py）：计划列表、队列视图、
 * 入队/改期/取消。替身返回一条已派发条目（含 run 链接）与一条排队条目，
 * 让设计基线覆盖两种主要视觉态；变化态（改期/取消）在用例内覆盖路由。
 */

import type { StubRoute } from "./stub-routes";

const PLAN = {
  id: "plan-stub-1",
  name: "sort-benchmark",
  hypothesis: "policy A lowers p50 latency",
  task_contract_ref: null,
  input_spec_digest: null,
  state: "PREREGISTERED",
  created_at: "2026-09-15T10:00:00+00:00",
  updated_at: "2026-09-15T10:00:00+00:00",
};

const DISPATCHED = {
  id: "queue-entry-1",
  project_id: "example-project",
  plan_id: "plan-stub-1",
  plan_name: "sort-benchmark",
  protocol_path: "m12_reference_research_v1.yaml",
  draft_id: null,
  draft_revision: null,
  state: "DISPATCHED",
  not_before: null,
  claimed_at: "2026-09-15T10:01:00+00:00",
  run_id: "run-stub-1",
  failure_reason: null,
  created_at: "2026-09-15T10:00:00+00:00",
  updated_at: "2026-09-15T10:02:00+00:00",
};

const QUEUED = {
  ...DISPATCHED,
  id: "queue-entry-2",
  protocol_path: null,
  draft_id: "draft-7",
  draft_revision: 3,
  state: "QUEUED",
  not_before: "2026-09-16T09:00:00+00:00",
  claimed_at: null,
  run_id: null,
  created_at: "2026-09-15T10:03:00+00:00",
  updated_at: "2026-09-15T10:03:00+00:00",
};

const DISPATCH_NOTE =
  "派发由控制面队列消费者按排期执行：与 POST /runs 同一条装配链，进程内同步执行、" +
  "串行推进；认领过期（进程中断）的条目会重新派发（at-least-once）。取消/改期只作用于 QUEUED。";

export const EXPERIMENT_QUEUE_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/experiment-plans(\?.*)?$/,
    handler: () => ({ status: 200, body: [PLAN] }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/experiment-queue$/,
    handler: () => ({
      status: 200,
      body: { entries: [DISPATCHED, QUEUED], dispatch_note: DISPATCH_NOTE },
    }),
  },
  {
    method: "POST",
    pattern: /^\/projects\/[^/]+\/experiments\/[^/]+\/queue$/,
    handler: () => ({ status: 201, body: QUEUED }),
  },
  {
    method: "PATCH",
    pattern: /^\/experiment-queue\/[^/]+$/,
    handler: () => ({ status: 200, body: QUEUED }),
  },
  {
    method: "DELETE",
    pattern: /^\/experiment-queue\/[^/]+$/,
    handler: () => ({ status: 200, body: { ...QUEUED, state: "CANCELLED" } }),
  },
];
