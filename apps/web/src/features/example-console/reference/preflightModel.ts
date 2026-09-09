import FIX_PREFLIGHT from "../data/preflight.json";

interface Finding {
  code: string;
  severity: string;
  message: string;
  subject_ref: { kind: string; id: string };
}

export interface ExamplePreflight {
  status: string;
  estimated_cost_minor: number | null;
  reserved_budget_ref: string | null;
  findings: Finding[];
  unresolved_risks: string[];
}

type Tone = "success" | "warn" | "danger";

const REPORTS = FIX_PREFLIGHT as unknown as Record<string, ExamplePreflight>;

/**
 * Verdict vocabulary derives from the fixture's own finding severities; no
 * status word is hardcoded in component code (production boundary contract).
 */
function severityTone(report: ExamplePreflight): Tone {
  if (report.findings.some((finding) => finding.severity === "error")) return "danger";
  if (report.findings.some((finding) => finding.severity === "warning")) return "warn";
  return "success";
}

function reportsByTone(): Record<Tone, ExamplePreflight> {
  const entries = Object.values(REPORTS);
  const firstWith = (tone: Tone): ExamplePreflight => {
    const match = entries.find((report) => severityTone(report) === tone);
    if (match === undefined) throw new Error(`example preflight fixture lacks a ${tone} report`);
    return match;
  };
  return { success: firstWith("success"), warn: firstWith("warn"), danger: firstWith("danger") };
}

const TONE_REPORTS = reportsByTone();

export type ExamplePreflightKind = keyof typeof TONE_REPORTS;

export function examplePreflight(kind: ExamplePreflightKind): ExamplePreflight {
  return TONE_REPORTS[kind];
}

export function preflightTone(report: ExamplePreflight): Tone {
  return severityTone(report);
}

export function preflightCounts(report: ExamplePreflight) {
  return {
    errorCount: report.findings.filter((finding) => finding.severity === "error").length,
    warnCount: report.findings.filter((finding) => finding.severity === "warning").length,
    infoCount: report.findings.filter((finding) => finding.severity === "info").length,
  };
}

/** Start unlocks only when nothing errored and every warning is acknowledged. */
export function canStartPreflight(report: ExamplePreflight, ack: boolean): boolean {
  const tone = severityTone(report);
  return tone === "success" || (tone === "warn" && ack);
}

const TONE_BY_STATUS: Readonly<Record<string, Tone>> = Object.freeze(
  Object.fromEntries(Object.values(REPORTS).map((r) => [r.status, severityTone(r)])),
);

/** Maps a status string to its tone; an unlisted status is treated as a warning. */
export function preflightToneByStatus(status: string): Tone {
  return TONE_BY_STATUS[status] ?? "warn";
}

/** Whether an acknowledged warnings gate is blocking, i.e. the report has errors. */
export function isBlocked(report: ExamplePreflight): boolean {
  return severityTone(report) === "danger";
}

/** Whether the report is clean (no errors, no warnings): nothing to acknowledge. */
export function isReady(report: ExamplePreflight): boolean {
  return severityTone(report) === "success";
}
