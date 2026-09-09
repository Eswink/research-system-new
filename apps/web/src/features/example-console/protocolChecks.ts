import type { Protocol, ProtocolIssue } from "./exampleTypes";

interface Rule extends Omit<ProtocolIssue, "message"> {
  message: string;
  fails: (p: Protocol) => boolean;
}

/** Demonstration constraints from the supplied prototype, NOT the real compiler/evaluation gate. */
const RULES: readonly Rule[] = [
  {
    path: "manifest.name",
    section: "manifest",
    severity: "error",
    code: "E-M001",
    message: "Manifest name must be ≥ 3 characters.",
    fails: (p) => p.manifest.name.length < 3,
  },
  {
    path: "manifest.name",
    section: "manifest",
    severity: "error",
    code: "E-M002",
    message: "Only lowercase, digits and hyphens allowed.",
    fails: (p) => p.manifest.name.length > 0 && !/^[a-z0-9-]+$/.test(p.manifest.name),
  },
  {
    path: "objectives",
    section: "objectives",
    severity: "error",
    code: "E-O001",
    message: "At least one objective is required.",
    fails: (p) => p.objectives.length === 0,
  },
  {
    path: "evaluation.languages",
    section: "evaluation",
    severity: "warning",
    code: "W-E001",
    message: "Example per-language gate expects at least two language subsets.",
    fails: (p) =>
      p.evaluation.languages.length < 2 && p.gates.some((g) => g.kind === "QUALITY_GATE"),
  },
  {
    path: "evaluation.n_per_lang",
    section: "evaluation",
    severity: "error",
    code: "E-E001",
    message: "Example rule: n_per_lang ≥ 30 (not a universal statistical-power criterion).",
    fails: (p) => p.evaluation.n_per_lang < 30,
  },
  {
    path: "evaluation.n_per_lang",
    section: "evaluation",
    severity: "warning",
    code: "W-E002",
    message: "Example rule: review sampling assumptions when n_per_lang < 100.",
    fails: (p) => p.evaluation.n_per_lang >= 30 && p.evaluation.n_per_lang < 100,
  },
  {
    path: "evaluation.temperature_grid",
    section: "evaluation",
    severity: "warning",
    code: "W-E003",
    message: "Empty temperature_grid — deterministic only.",
    fails: (p) => p.evaluation.temperature_grid.length === 0,
  },
  {
    path: "budget.hard_stop_on_breach",
    section: "budget",
    severity: "warning",
    code: "W-B002",
    message: "Example hard stop is OFF; this does not change the real budget policy.",
    fails: (p) => !p.budget.hard_stop_on_breach,
  },
  {
    path: "gates",
    section: "gates",
    severity: "error",
    code: "E-G001",
    message: "BUDGET_GATE is mandatory in this example.",
    fails: (p) => !p.gates.some((g) => g.kind === "BUDGET_GATE"),
  },
  {
    path: "gates",
    section: "gates",
    severity: "warning",
    code: "W-G001",
    message: "No example PUBLISH_GATE is configured.",
    fails: (p) => !p.gates.some((g) => g.kind === "PUBLISH_GATE"),
  },
];

export function fieldChecks(protocol: Protocol): ProtocolIssue[] {
  return RULES.filter((rule) => rule.fails(protocol)).map(
    ({ path, section, severity, code, message }) => ({ path, section, severity, code, message }),
  );
}

export function objectiveChecks(protocol: Protocol): ProtocolIssue[] {
  return protocol.objectives.flatMap((objective, index) => {
    const result: ProtocolIssue[] = [];
    if (objective.id.length === 0)
      result.push({
        path: `objectives[${String(index)}].id`,
        section: "objectives",
        severity: "error",
        code: "E-O002",
        message: `Objective #${String(index + 1)} missing id.`,
      });
    if (objective.statement.length < 10)
      result.push({
        path: `objectives[${String(index)}].statement`,
        section: "objectives",
        severity: "warning",
        code: "W-O001",
        message: `Objective #${String(index + 1)} statement is very short.`,
      });
    return result;
  });
}

export function budgetChecks(protocol: Protocol): ProtocolIssue[] {
  const sum = protocol.budget.reservations.reduce((total, row) => total + row.minor, 0);
  const cap = protocol.budget.cap_minor;
  if (sum > cap)
    return [
      {
        path: "budget.reservations",
        section: "budget",
        severity: "error",
        code: "E-B001",
        message:
          `Reservations sum ${(sum / 100000).toFixed(2)}` +
          ` exceeds cap ${(cap / 100000).toFixed(2)}.`,
      },
    ];
  if (sum < cap * 0.5)
    return [
      {
        path: "budget.reservations",
        section: "budget",
        severity: "warning",
        code: "W-B001",
        message: "Example reservations sum is < 50% of cap.",
      },
    ];
  return [];
}
