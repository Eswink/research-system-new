import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import type { CostViewDto, RunTelemetryDto, TrendViewDto } from "../../src/api/types";
import { OperationsPanel } from "../../src/features/operations/OperationsPanel";
import {
  CostView,
  TelemetryView,
  TrendView,
} from "../../src/features/operations/Views";

const telemetry: RunTelemetryDto = {
  run_id: "run-1",
  manifest_digest: "sha256:manifest",
  exporter_config_digest: "sha256:exporter",
  generated_at: "2026-08-30T00:00:00Z",
  tasks: { total: 1, succeeded: 1, failed: 0, cancelled: 0, queued: 0, leased: 0, other: 0 },
  outbox: { pending: null, status: "UNKNOWN", unavailable_reason: "outbox unavailable" },
  sink: { enabled: false, dropped: 0, unlinked: 0, last_error: null },
};

const cost: CostViewDto = {
  run_id: "run-1",
  pricing_version: "v1",
  pricing_digest: "abc123",
  pricing_frozen: true,
  pricing_degraded_reason: null,
  dimensions: [
    {
      dimension: "model",
      resource_key: "model-a",
      entry_count: 1,
      amount: {
        status: "ESTIMATED",
        minor_units: 125,
        currency: "JPY",
        effective_from: "2026-08-30",
        calculation_method: "unit_price_minor_per_unit",
      },
    },
  ],
  total: {
    status: "ESTIMATED",
    minor_units: 125,
    currency: "JPY",
    effective_from: "2026-08-30",
    calculation_method: "unit_price_minor_per_unit",
  },
};

const trend: TrendViewDto = {
  dataset_id: "dataset-1",
  truncated: true,
  divergences: [],
  missing: [],
  segments: [
    {
      comparisons: [],
      points: [
        {
          report_digest: "sha256:report",
          recorded_at: "2026-08-30T00:00:00Z",
          verdict: "PASS",
          dataset_id: "dataset-1",
          dataset_version: "1.0.0",
          dataset_digest: "sha256:dataset",
          gate_config_id: "gate-1",
          gate_config_version: "1.0.0",
          gate_config_digest: "sha256:gate",
          system_version: "0.4.0",
          comparison_digest: "sha256:comparison",
          run_id: "run-1",
          pass_count: 2,
          fail_count: 0,
          infra_error_count: 0,
          reviewer_failure_count: 1,
          missing: false,
          integrity_error: null,
        },
      ],
    },
  ],
};

test("operations views render server-provided provenance, amounts, and unknown state", () => {
  const html = renderToStaticMarkup(
    createElement(
      "main",
      undefined,
      createElement(TelemetryView, { telemetry }),
      createElement(CostView, { cost }),
      createElement(TrendView, { trend }),
    ),
  );
  assert.match(html, /sha256:manifest/);
  assert.match(html, /UNKNOWN/);
  assert.match(html, /125 JPY minor units/);
  assert.match(html, /reviewer failures 1/);
  assert.match(html, /showing a bounded recent window/);
});

test("operations panel renders controls through its server-state hook", () => {
  const html = renderToStaticMarkup(createElement(OperationsPanel));
  assert.match(html, /data-testid="operations-panel"/);
  assert.match(html, /Load Telemetry &amp; Cost/);
  assert.match(html, /Load Evaluation Trend/);
});
