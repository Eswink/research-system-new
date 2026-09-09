/* Protocol Visual Editor
   Segmented Toggle: Form (default) ↔ YAML
   Form mode: left section nav, right section body
   Sections: Manifest / Objectives / Team / Evaluation / Budget / Gates / Policy
   Sync: edits stage locally; "Apply" writes back to YAML
   Validation: field-level red border + inline error, top banner summary
   Digest banner: warn when protocol dirty (invalidates reproducibility)
*/

// ─── Defaults & shape helpers ─────────────────────────
const DEFAULT_PROTOCOL = {
  protocol_version: "1.4",
  manifest: {
    id: "run_01K5FZ8G3X2QN4M",
    name: "multilingual-medical-qa-hallucination",
    autonomy_level: "GUARDED_AUTONOMOUS",
  },
  objectives: [
    { id: "obj_hall_rate", statement: "Quantify hallucination rate of LLMs on multilingual medical dosage QA across 7 languages." },
    { id: "obj_var_ranking", statement: "Rank models by cross-lingual variance of hallucination behavior." },
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

const AVAILABLE_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "es", label: "Español" },
  { code: "zh", label: "中文" },
  { code: "ar", label: "العربية" },
  { code: "pt", label: "Português" },
  { code: "fr", label: "Français" },
  { code: "ja", label: "日本語" },
  { code: "de", label: "Deutsch" },
  { code: "hi", label: "हिन्दी" },
  { code: "ru", label: "Русский" },
];

const AVAILABLE_BENCHMARKS = [
  "medhalt-v2",
  "internal.dosage_probe.v3",
  "medqa-usmle",
  "pubmedqa",
  "medmcqa",
  "medhalt-v1",
];

const RESOURCE_TYPES = [
  { id: "llm_tokens", label: "LLM tokens" },
  { id: "gpu_a100_hr", label: "GPU A100 · hr" },
  { id: "gpu_h100_hr", label: "GPU H100 · hr" },
  { id: "external_tools", label: "External tools" },
  { id: "embedding_local", label: "Embedding · local" },
  { id: "storage_gb_mo", label: "Storage · GB·mo" },
];

const GATE_KINDS = ["BUDGET_GATE", "QUALITY_GATE", "PUBLISH_GATE", "SECURITY_GATE", "ETHICS_GATE"];

const TEMPLATES = {
  current: { label: "Current draft", description: "Working revision" },
  prior_study: { label: "Prior study · Med QA", description: "Reuse last month's Med QA baseline" },
  stat_heavy: { label: "STAT-heavy", description: "STANDARD + adversarial reviewers + ethics gate" },
  minimal: { label: "Minimal exploratory", description: "Single language · no QUALITY_GATE" },
  reset: { label: "Reset to canonical defaults", description: "1.4 canonical protocol shape" },
};

// ─── Validation ───────────────────────────────────────
const validate = (p, adminMode, errorLevel) => {
  const errors = [];
  const warnings = [];

  // Manifest
  if (!p.manifest.name || p.manifest.name.length < 3) {
    errors.push({ path: "manifest.name", section: "manifest", severity: "error", code: "E-M001", message: "Manifest name must be ≥ 3 characters." });
  }
  if (p.manifest.name && !/^[a-z0-9-]+$/.test(p.manifest.name)) {
    errors.push({ path: "manifest.name", section: "manifest", severity: "error", code: "E-M002", message: "Only lowercase, digits and hyphens allowed." });
  }

  // Objectives
  if (!p.objectives || p.objectives.length === 0) {
    errors.push({ path: "objectives", section: "objectives", severity: "error", code: "E-O001", message: "At least one objective is required." });
  }
  p.objectives.forEach((o, i) => {
    if (!o.id) errors.push({ path: `objectives[${i}].id`, section: "objectives", severity: "error", code: "E-O002", message: `Objective #${i+1} missing id.` });
    if (!o.statement || o.statement.length < 10) warnings.push({ path: `objectives[${i}].statement`, section: "objectives", severity: "warning", code: "W-O001", message: `Objective #${i+1} statement is very short.` });
  });

  // Evaluation
  if (p.evaluation.languages.length < 2 && p.gates.some(g => g.kind === "QUALITY_GATE")) {
    warnings.push({ path: "evaluation.languages", section: "evaluation", severity: "warning", code: "W-E001", message: "QUALITY_GATE per-language subset with only 1 language is degenerate." });
  }
  if (p.evaluation.n_per_lang < 30) {
    errors.push({ path: "evaluation.n_per_lang", section: "evaluation", severity: "error", code: "E-E001", message: "n_per_lang < 30 has insufficient statistical power." });
  } else if (p.evaluation.n_per_lang < 100) {
    warnings.push({ path: "evaluation.n_per_lang", section: "evaluation", severity: "warning", code: "W-E002", message: "n_per_lang < 100 — CI will be wide." });
  }
  if (p.evaluation.temperature_grid.length === 0) {
    warnings.push({ path: "evaluation.temperature_grid", section: "evaluation", severity: "warning", code: "W-E003", message: "Empty temperature_grid — deterministic only." });
  }

  // Budget
  const sum = p.budget.reservations.reduce((s, r) => s + (r.minor || 0), 0);
  if (sum > p.budget.cap_minor) {
    errors.push({ path: "budget.reservations", section: "budget", severity: "error", code: "E-B001", message: `Reservations sum ${(sum/100000).toFixed(2)} exceeds cap ${(p.budget.cap_minor/100000).toFixed(2)}.` });
  } else if (sum < p.budget.cap_minor * 0.5) {
    warnings.push({ path: "budget.reservations", section: "budget", severity: "warning", code: "W-B001", message: "Reservations sum is < 50% of cap — under-planned." });
  }
  if (!p.budget.hard_stop_on_breach) {
    warnings.push({ path: "budget.hard_stop_on_breach", section: "budget", severity: "warning", code: "W-B002", message: "hard_stop_on_breach is OFF — run may exceed cap silently." });
  }

  // Gates
  const kinds = p.gates.map(g => g.kind);
  if (!kinds.includes("BUDGET_GATE")) errors.push({ path: "gates", section: "gates", severity: "error", code: "E-G001", message: "BUDGET_GATE is mandatory." });
  if (!kinds.includes("PUBLISH_GATE")) warnings.push({ path: "gates", section: "gates", severity: "warning", code: "W-G001", message: "No PUBLISH_GATE — deliverables ship unreviewed." });

  // ── Simulated tweak: crank up error volume ──
  if (errorLevel === "many") {
    errors.push({ path: "manifest.name", section: "manifest", severity: "error", code: "E-M099", message: "Simulated: name collides with existing run in workspace." });
    errors.push({ path: "team.overrides", section: "team", severity: "error", code: "E-T001", message: "Simulated: role_ethics without capacity binding." });
    errors.push({ path: "policy.heterogeneous_review", section: "policy", severity: "error", code: "E-P001", message: "Simulated: admin approval required for policy change." });
  }

  return { errors, warnings };
};

// ─── Serialization (state → YAML text) ────────────────
const serialize = (p) => {
  const lines = [];
  lines.push(`protocol_version: "${p.protocol_version}"`);
  lines.push(`manifest:`);
  lines.push(`  id: ${p.manifest.id}`);
  lines.push(`  name: ${p.manifest.name}`);
  lines.push(`  autonomy_level: ${p.manifest.autonomy_level}`);
  lines.push(``);
  lines.push(`objectives:`);
  p.objectives.forEach(o => {
    lines.push(`  - id: ${o.id}`);
    // simple 60-char wrap for readability
    const s = o.statement || "";
    if (s.length <= 60) {
      lines.push(`    statement: ${s}`);
    } else {
      lines.push(`    statement: ${s.slice(0, 60).trim()}`);
      let rest = s.slice(60);
      while (rest.length > 60) {
        lines.push(`      ${rest.slice(0, 60).trim()}`);
        rest = rest.slice(60);
      }
      if (rest.trim()) lines.push(`      ${rest.trim()}`);
    }
  });
  lines.push(``);
  lines.push(`team:`);
  lines.push(`  template: ${p.team.template}          # rigor: methods + stats reviewers required`);
  if (p.team.overrides.length) {
    lines.push(`  overrides:`);
    p.team.overrides.forEach(o => {
      lines.push(`    - role: ${o.role}`);
      if (o.instances != null) lines.push(`      instances: ${o.instances}`);
      if (o.collapse_when) lines.push(`      collapse_when: "${o.collapse_when}"`);
    });
  }
  lines.push(``);
  lines.push(`evaluation:`);
  lines.push(`  benchmarks:`);
  p.evaluation.benchmarks.forEach(b => lines.push(`    - ${b}`));
  lines.push(`  languages: [${p.evaluation.languages.join(", ")}]`);
  lines.push(`  n_per_lang: ${p.evaluation.n_per_lang}`);
  lines.push(`  temperature_grid: [${p.evaluation.temperature_grid.map(t => t.toFixed(1)).join(", ")}]`);
  lines.push(``);
  lines.push(`budget:`);
  lines.push(`  cap_minor: ${p.budget.cap_minor}        # ${(p.budget.cap_minor/100000).toFixed(2)} USD`);
  lines.push(`  hard_stop_on_breach: ${p.budget.hard_stop_on_breach}`);
  lines.push(`  reservations:`);
  p.budget.reservations.forEach(r => {
    lines.push(`    - resource: ${r.resource.padEnd(18, " ")}; minor: ${r.minor}`);
  });
  lines.push(``);
  lines.push(`gates:`);
  p.gates.forEach(g => {
    lines.push(`  - kind: ${g.kind.padEnd(14, " ")}; at: ${g.at}`);
  });
  lines.push(``);
  lines.push(`policy:`);
  lines.push(`  heterogeneous_review: ${p.policy.heterogeneous_review}`);
  lines.push(`  memory_write: ${p.policy.memory_write}`);
  lines.push(`  redact_prompts: ${p.policy.redact_prompts}`);
  return lines.join("\n");
};

// ─── Main editor ──────────────────────────────────────
const ProtocolEditor = ({ mode: initialMode = "form", errorLevel = "some", adminMode = false, languagesCount = 7, temperatureCount = 6 }) => {
  const { t } = useI18n();
  const [mode, setMode] = useState(initialMode);
  const [protocol, setProtocol] = useState(() => {
    const base = JSON.parse(JSON.stringify(DEFAULT_PROTOCOL));
    base.evaluation.languages = base.evaluation.languages.slice(0, languagesCount);
    base.evaluation.temperature_grid = base.evaluation.temperature_grid.slice(0, temperatureCount);
    return base;
  });
  const [committed, setCommitted] = useState(protocol);
  const [activeSection, setActiveSection] = useState("manifest");
  const [templateOpen, setTemplateOpen] = useState(false);

  // Sync mode / demo-tweak-driven data when tweaks change from outside
  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);
  useEffect(() => {
    setProtocol(prev => {
      const next = JSON.parse(JSON.stringify(prev));
      next.evaluation.languages = DEFAULT_PROTOCOL.evaluation.languages.slice(0, languagesCount);
      next.evaluation.temperature_grid = DEFAULT_PROTOCOL.evaluation.temperature_grid.slice(0, temperatureCount);
      return next;
    });
    setCommitted(prev => {
      const next = JSON.parse(JSON.stringify(prev));
      next.evaluation.languages = DEFAULT_PROTOCOL.evaluation.languages.slice(0, languagesCount);
      next.evaluation.temperature_grid = DEFAULT_PROTOCOL.evaluation.temperature_grid.slice(0, temperatureCount);
      return next;
    });
  }, [languagesCount, temperatureCount]);

  const { errors, warnings } = useMemo(() => validate(protocol, adminMode, errorLevel), [protocol, adminMode, errorLevel]);
  const errorsBySection = useMemo(() => {
    const grouped = {};
    [...errors, ...warnings].forEach(e => {
      if (!grouped[e.section]) grouped[e.section] = { errors: 0, warnings: 0 };
      if (e.severity === "error") grouped[e.section].errors++;
      else grouped[e.section].warnings++;
    });
    return grouped;
  }, [errors, warnings]);

  const dirty = useMemo(() => JSON.stringify(protocol) !== JSON.stringify(committed), [protocol, committed]);
  const canApply = errors.length === 0 && dirty;

  // helper: setter for nested paths
  const setP = (updater) => setProtocol(prev => {
    const next = JSON.parse(JSON.stringify(prev));
    updater(next);
    return next;
  });

  const yamlText = useMemo(() => serialize(protocol), [protocol]);

  return (
    <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden", minHeight: 0 }}>
      {/* ── Chrome ─────────────────────────────────── */}
      <EditorChrome
        mode={mode} setMode={setMode}
        dirty={dirty}
        onTemplates={() => setTemplateOpen(v => !v)}
      />
      {templateOpen && <TemplatePicker onClose={() => setTemplateOpen(false)} onPick={(id) => {
        if (id === "reset") setProtocol(JSON.parse(JSON.stringify(DEFAULT_PROTOCOL)));
        setTemplateOpen(false);
      }}/>}

      {/* ── Digest banner (only when dirty) ─────── */}
      {dirty && <DigestBanner />}

      {/* ── Error banner (only when errors) ───── */}
      {errors.length > 0 && <ErrorBanner errors={errors} onJump={(section) => { setMode("form"); setActiveSection(section); }} />}

      {/* ── Body ───────────────────────────────────── */}
      {mode === "yaml" ? (
        <YamlView text={yamlText} />
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "148px minmax(0, 1fr)", flex: 1, minHeight: 0, overflow: "hidden" }}>
          <SectionNav
            active={activeSection}
            onChange={setActiveSection}
            errorsBySection={errorsBySection}
            adminMode={adminMode}
          />
          <div style={{ overflow: "auto", padding: "16px 18px 80px", position: "relative" }}>
            {activeSection === "manifest" && <ManifestSection value={protocol} setP={setP} errors={errors} adminMode={adminMode}/>}
            {activeSection === "objectives" && <ObjectivesSection value={protocol} setP={setP} errors={errors}/>}
            {activeSection === "team" && <TeamSection value={protocol} setP={setP} errors={errors}/>}
            {activeSection === "evaluation" && <EvaluationSection value={protocol} setP={setP} errors={errors} warnings={warnings}/>}
            {activeSection === "budget" && <BudgetSection value={protocol} setP={setP} errors={errors} warnings={warnings}/>}
            {activeSection === "gates" && <GatesSection value={protocol} setP={setP} errors={errors}/>}
            {activeSection === "policy" && <PolicySection value={protocol} setP={setP} adminMode={adminMode}/>}
          </div>
        </div>
      )}

      {/* ── Sticky action bar ─────────────────────── */}
      <ActionBar
        dirty={dirty}
        canApply={canApply}
        errorCount={errors.length}
        warnCount={warnings.length}
        onDiscard={() => setProtocol(committed)}
        onApply={() => setCommitted(protocol)}
      />
    </div>
  );
};

Object.assign(window, {
  ProtocolEditor,
  DEFAULT_PROTOCOL,
  AVAILABLE_LANGUAGES,
  AVAILABLE_BENCHMARKS,
  RESOURCE_TYPES,
  GATE_KINDS,
  TEMPLATES,
});
