/**
 * 预算页 API 替身路由（PLAN-20260914-046 WP-C）。
 *
 * usage / cost-forecast / interventions 三条是有状态替身：调整后 forecast 的
 * 预留额度随之变化，从而让 e2e 能验证"调整真实生效并反映到预测"。
 * 形状遵循真实 DTO；UNKNOWN 条目保留（证明页面不把不可计量渲染成 0）。
 */

import type { StubRoute, Handler } from "./stub-routes";

const TOKENS = "tokens";
const SECONDS = "seconds";

/** 替身内状态：只服务页面对账，不冒充后端账本。 */
const state = {
  reservedTokens: 1000,
  reservedGpuSeconds: 60,
  reservationRef: "budget-reservation:stub-initial",
};

function runIdOf(url: URL): string {
  return url.pathname.split("/")[2] ?? "";
}

function entries(runId: string) {
  return [
    {
      entry_id: "e-stub-tokens",
      resource_type: "MODEL_TOKENS",
      quantity: 400,
      unit: TOKENS,
      cost_status: "ESTIMATED",
      estimated_cost_minor: 240,
      actual_cost_minor: null,
      currency: "USD",
      quantity_status: "KNOWN",
      unavailable_reason: null,
      attempt: 1,
      run_id: runId,
      model_id: null,
      task_id: null,
    },
    {
      entry_id: "e-stub-gpu-unknown",
      resource_type: "GPU_TIME",
      quantity: 0,
      unit: SECONDS,
      cost_status: "UNKNOWN",
      estimated_cost_minor: null,
      actual_cost_minor: null,
      currency: "USD",
      quantity_status: "UNKNOWN",
      unavailable_reason: "gpu metering unavailable",
      attempt: 1,
      run_id: runId,
      model_id: null,
      task_id: null,
    },
  ];
}

function reservations(runId: string) {
  return [
    {
      id: `budget:${runId}:MODEL_TOKENS:stub`,
      scope: `run:${runId}`,
      resource_type: "MODEL_TOKENS",
      quantity: state.reservedTokens,
      unit: TOKENS,
    },
    {
      id: `budget:${runId}:GPU_TIME:stub`,
      scope: `run:${runId}`,
      resource_type: "GPU_TIME",
      quantity: state.reservedGpuSeconds,
      unit: SECONDS,
    },
  ];
}

function forecast(runId: string) {
  return {
    run_id: runId,
    lines: [
      {
        resource_type: "GPU_TIME",
        unit: SECONDS,
        reserved: state.reservedGpuSeconds,
        consumed: null,
        remaining: null,
        data_status: "UNKNOWN",
        entry_count: 1,
        unknown_entry_count: 1,
      },
      {
        resource_type: "MODEL_TOKENS",
        unit: TOKENS,
        reserved: state.reservedTokens,
        consumed: 400,
        remaining: state.reservedTokens - 400,
        data_status: "KNOWN",
        entry_count: 1,
        unknown_entry_count: 0,
      },
    ],
    consumed_cost_minor: null,
    currency: "USD",
    cost_status: "MONETARY_UNAVAILABLE",
    unknown_cost_entries: 1,
    attribution: "RESERVATION_REF",
    unattributed_reserved: 0,
    forecast_scope: "RESERVED_ONLY",
    scope_note:
      "forecast covers reserved quota minus recorded usage only; " +
      "un-reserved future spend is not extrapolated",
  };
}

const adjustHandler: Handler = (url, body) => {
  const runId = runIdOf(url);
  const payload = (body ?? {}) as { adjustments?: { resource_type?: string; quantity?: number }[] };
  const line = payload.adjustments?.[0];
  if (line?.resource_type === "MODEL_TOKENS" && typeof line.quantity === "number") {
    state.reservedTokens = line.quantity;
  }
  state.reservationRef = "budget-reservation:stub-adjusted";
  return {
    status: 200,
    body: {
      run_id: runId,
      released_ref: "budget-reservation:stub-initial",
      reservation_ref: state.reservationRef,
      reservations: reservations(runId),
    },
  };
};

export const BUDGET_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/usage$/,
    handler: (url) => ({
      status: 200,
      body: {
        entries: entries(runIdOf(url)),
        total_estimated_cost_minor: null,
        total_currency: "USD",
        known_cost_subtotal_minor: 240,
        unknown_cost_entries: 1,
        reservations: reservations(runIdOf(url)),
      },
    }),
  },
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/cost-forecast$/,
    handler: (url) => ({ status: 200, body: forecast(runIdOf(url)) }),
  },
  {
    method: "POST",
    pattern: /^\/runs\/[^/]+\/interventions$/,
    handler: adjustHandler,
  },
  // PLAN-20260915-057（G12）：项目级成本预测——一天进样本、一天 USAGE_UNKNOWN 被排除，
  // 让设计基线与交互用例同时覆盖"外推 + 排除原因"两种视觉态。
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/cost-forecast$/,
    handler: (url) => ({ status: 200, body: projectForecast(url.pathname.split("/")[2] ?? "") }),
  },
];

const MONEY_STAMP = {
  currency: "USD",
  effective_from: "2026-01-01",
  calculation_method: "pricing_version_table",
};

function projectForecast(projectId: string) {
  return {
    project_id: projectId,
    from_date: null,
    to_date: null,
    truncated: false,
    days: [
      {
        date: "2026-09-13",
        amount: { status: "ACTUAL", minor_units: 1200, ...MONEY_STAMP },
        mixed_pricing: false,
        included_in_projection: true,
        exclusion_reason: null,
      },
      {
        date: "2026-09-14",
        amount: { status: "USAGE_UNKNOWN", minor_units: null, ...MONEY_STAMP },
        mixed_pricing: false,
        included_in_projection: false,
        exclusion_reason: "USAGE_UNKNOWN",
      },
    ],
    projection: {
      method: "MEAN_OF_VALUED_DAYS",
      horizon_days: 7,
      valued_days: 1,
      excluded_days: 1,
      observed_minor: 1200,
      observed_status: "ACTUAL",
      currency: "USD",
      pricing_version: "unpriced_v1",
      daily_mean_minor: 1200,
      projected_minor: 8400,
      unavailable_reason: null,
      note: "projection = mean of the valued daily amounts in the window × horizon",
    },
    unattributed_entries: 0,
    attribution_note: null,
    scope_note: "project-scope time-series projection",
  };
}
