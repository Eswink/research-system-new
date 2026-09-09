/** Reference: screens/ProtocolEditor.jsx; EXAMPLE ONLY. */
export const DEFAULT_PROTOCOL = {
  protocol_version: "1.4",
  manifest: {
    id: "run_01K5FZ8G3X2QN4M",
    name: "multilingual-medical-qa-hallucination",
    autonomy_level: "GUARDED_AUTONOMOUS",
  },
  objectives: [
    {
      id: "obj_hall_rate",
      statement:
        "Quantify hallucination rate of LLMs on multilingual medical dosage QA across 7 languages.",
    },
    {
      id: "obj_var_ranking",
      statement: "Rank models by cross-lingual variance of hallucination behavior.",
    },
  ],
  team: {
    template: "STANDARD",
    overrides: [
      { role: "role_ethics", instances: 1, collapse_when: "" },
      { role: "role_writer", instances: null, collapse_when: "publish_gate_not_reached" },
    ],
  },
  evaluation: {
    benchmarks: ["medhalt-v2", "internal.dosage_probe.v3"],
    languages: ["en", "es", "zh", "ar", "pt", "fr", "ja"],
    n_per_lang: 200,
    temperature_grid: [0.0, 0.1, 0.2, 0.3, 0.5, 0.7],
  },
  budget: {
    cap_minor: 5000000,
    hard_stop_on_breach: true,
    reservations: [
      { resource: "llm_tokens", minor: 2200000 },
      { resource: "gpu_a100_hr", minor: 1800000 },
      { resource: "external_tools", minor: 320000 },
      { resource: "embedding_local", minor: 500000 },
    ],
  },
  gates: [
    { kind: "BUDGET_GATE", at: "60% of cap" },
    { kind: "QUALITY_GATE", at: "after each language subset" },
    { kind: "PUBLISH_GATE", at: "deliverable finalized" },
    { kind: "SECURITY_GATE", at: "any external artifact publish" },
  ],
  policy: {
    heterogeneous_review: "strict",
    memory_write: "gated_by_provenance",
    redact_prompts: true,
  },
};
