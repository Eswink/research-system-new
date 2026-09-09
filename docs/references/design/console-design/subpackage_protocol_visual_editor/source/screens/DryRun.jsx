/* Screen 4: Protocol & Dry Run Gate — the P1 canonical enforcement.
   Left: Protocol YAML source. Right: Preflight report with 6 zones. */

const DryRunScreen = ({
  preflightState = "WARN",
  protocolMode = "form",
  protocolErrorLevel = "some",
  protocolLanguages = 7,
  protocolTemperatures = 6,
  protocolAdminMode = false,
}) => {
  const { t } = useI18n();
  const preflight = FIX_PREFLIGHT[preflightState];
  const [selectedFinding, setSelectedFinding] = useState(0);
  const [ack, setAck] = useState(false);

  const canStart = preflight.status === "PASS" || (preflight.status === "WARN" && ack);
  const errorCount = preflight.findings.filter(f => f.severity === "error").length;
  const warnCount = preflight.findings.filter(f => f.severity === "warning").length;
  const infoCount = preflight.findings.filter(f => f.severity === "info").length;

  const PROTOCOL_YAML = `protocol_version: "1.4"
manifest:
  id: run_01K5FZ8G3X2QN4M
  name: multilingual-medical-qa-hallucination
  autonomy_level: GUARDED_AUTONOMOUS

objectives:
  - id: obj_hall_rate
    statement: Quantify hallucination rate of LLMs on
      multilingual medical dosage QA across 7 languages.
  - id: obj_var_ranking
    statement: Rank models by cross-lingual variance
      of hallucination behavior.

team:
  template: STANDARD          # rigor: methods + stats reviewers required
  overrides:
    - role: role_ethics
      instances: 1
    - role: role_writer
      collapse_when: "publish_gate_not_reached"

evaluation:
  benchmarks:
    - medhalt-v2
    - internal.dosage_probe.v3
  languages: [en, es, zh, ar, pt, fr, ja]
  n_per_lang: 200
  temperature_grid: [0.0, 0.1, 0.2, 0.3, 0.5, 0.7]

budget:
  cap_minor: 5000000        # 50.00 USD
  hard_stop_on_breach: true
  reservations:
    - resource: llm_tokens        ; minor: 2200000
    - resource: gpu_a100_hr       ; minor: 1800000
    - resource: external_tools    ; minor: 320000
    - resource: embedding_local   ; minor: 500000

gates:
  - kind: BUDGET_GATE   ; at: 60% of cap
  - kind: QUALITY_GATE  ; at: after each language subset
  - kind: PUBLISH_GATE  ; at: deliverable finalized
  - kind: SECURITY_GATE ; at: any external artifact publish

policy:
  heterogeneous_review: strict
  memory_write: gated_by_provenance
  redact_prompts: true`;

  // Layout
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(480px, 1fr) minmax(460px, 1.1fr)", gap: 16, flex: 1, minHeight: 0, overflow: "hidden" }}>
      {/* ── Left: Protocol Editor (Form ↔ YAML) ─────────── */}
      <ProtocolEditor
        mode={protocolMode}
        errorLevel={protocolErrorLevel}
        adminMode={protocolAdminMode}
        languagesCount={protocolLanguages}
        temperatureCount={protocolTemperatures}
      />

      {/* ── Right: Preflight report ─────────────────────── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, minHeight: 0 }}>

        {/* Status bar — P1: Start disabled unless PASS/WARN(ack) */}
        <div className="panel" style={{
          padding: 16,
          borderColor: preflight.status === "FAIL" ? "var(--danger-line)" :
                       preflight.status === "WARN" ? "var(--warn-line)" : "var(--success-line)",
          background: preflight.status === "FAIL" ? "linear-gradient(180deg, var(--danger-dim), transparent 60%)" :
                      preflight.status === "WARN" ? "linear-gradient(180deg, var(--warn-dim), transparent 60%)" :
                      "linear-gradient(180deg, var(--success-dim), transparent 60%)",
        }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
                <PreflightBadge status={preflight.status} />
                <span style={{ fontSize: 12, color: "var(--fg-faint)" }}>{t("dr.report")}</span>
                <DigestText value="sha256:preflight_a9c4e21f0b8d47bf12e6c3a9" label="report:" length={8} />
              </div>
              <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 4, letterSpacing: "-0.005em" }}>
                {preflight.status === "PASS" && t("dr.readyPass")}
                {preflight.status === "WARN" && t("dr.readyWarn").replace("{n}", warnCount).replace("{s}", warnCount>1?"s":"").replace("{i}", infoCount)}
                {preflight.status === "FAIL" && t("dr.readyFail").replace("{n}", errorCount).replace("{s}", errorCount>1?"s":"").replace("{w}", warnCount)}
              </div>
              <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                {t("dr.compiledAt")} 2026-08-27T14:02:18Z · plan_id plan_01K5FZ8G3X2 · {t("dr.elapsed")} 2.4s
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
              <button
                className="btn primary"
                disabled={!canStart}
                aria-disabled={!canStart}
                title={canStart ? t("dr.startTip.ok") : t("dr.startTip.blocked")}
                style={{ height: 32, padding: "0 16px", fontWeight: 500 }}
              >
                <Icon name="play" size={11}/> {t("dr.startRun")}
              </button>
              {preflight.status === "WARN" && (
                <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "var(--fg-muted)", cursor: "pointer" }}>
                  <input type="checkbox" checked={ack} onChange={e => setAck(e.target.checked)}
                    style={{ accentColor: "var(--warn)", cursor: "pointer" }}/>
                  {t("dr.ackI")} {warnCount} {t("dr.ackWarn")}{warnCount>1?"s":""}
                </label>
              )}
              {preflight.status === "FAIL" && (
                <span style={{ fontSize: 11, color: "var(--danger)", display: "flex", alignItems: "center", gap: 4 }}>
                  <Icon name="lock" size={10}/> {t("dr.blockedBy")} {errorCount} {t("dr.blockedBy2")}{errorCount>1?"s":""}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Scrollable body — 5 zones */}
        <div style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column", gap: 12 }}>

          {/* Zone: Findings */}
          <section className="panel">
            <ZoneHeader icon="warn-tri" title={t("dr.findings")} count={preflight.findings.length}
              extra={<><span className="chip" style={{ color: "var(--danger)", borderColor: "var(--danger-line)" }}>{errorCount} {t("dr.fErr")}</span>
                       <span className="chip" style={{ color: "var(--warn)", borderColor: "var(--warn-line)" }}>{warnCount} {t("dr.fWarn")}</span>
                       <span className="chip" style={{ color: "var(--accent)", borderColor: "var(--accent-line)" }}>{infoCount} {t("dr.fInfo")}</span></>}
            />
            {preflight.findings.length === 0 ? (
              <div style={{ padding: 24, textAlign: "center", color: "var(--fg-muted)" }}>
                <Icon name="check" size={14} style={{ color: "var(--success)" }}/>
                <div style={{ marginTop: 4 }}>{t("dr.noFindings")}</div>
              </div>
            ) : preflight.findings.map((f, i) => (
              <FindingRow key={i} finding={f} selected={i === selectedFinding} onSelect={() => setSelectedFinding(i)} />
            ))}
          </section>

          {/* Zone: Resolved Plan (role_counts investment) */}
          <section className="panel">
            <ZoneHeader icon="hex" title={t("dr.resolved")} count={FIX_ROLES.filter(r => r.active > 0).length} extra={<span style={{ fontSize: 11, color: "var(--fg-faint)" }}>{FIX_AGENTS.length} {t("dr.agents")} {FIX_ROLES.filter(r => r.active === 0).length} {t("dr.collapsed")}</span>}/>
            <div style={{ padding: "8px 12px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {FIX_ROLES.map(r => (
                <div key={r.id} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "6px 10px", borderRadius: 6,
                  background: r.active === 0 ? "transparent" : "var(--bg-raised)",
                  border: `1px ${r.active === 0 ? "dashed" : "solid"} var(--border)`,
                  opacity: r.active === 0 ? 0.55 : 1,
                }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: r.active === 0 ? "var(--fg-faint)" : "var(--fg)" }}>{r.name}</div>
                    {r.collapsed_reason && <div style={{ fontSize: 10, color: "var(--fg-faint)", fontFamily: "var(--font-mono)" }}>{t("tm.rolesCollapsed")} {r.collapsed_reason}</div>}
                  </div>
                  <span className="chip" style={{ fontFamily: "var(--font-mono)" }}>{r.active}/{r.max}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Zone: Budget */}
          <section className="panel">
            <ZoneHeader icon="diamond" title={t("dr.budgetProj")} extra={preflight.status === "FAIL"
              ? <UnknownValue hint={t("dr.budgetUnknown")} />
              : <span className="mono" style={{ fontSize: 12 }}>{fmtMinor(preflight.estimated_cost_minor)} / {fmtMinor(5000000)}</span>}
            />
            {preflight.status === "FAIL" ? (
              <div style={{ padding: "10px 12px", display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "var(--unknown)" }}>
                <Icon name="q" size={12}/> {t("dr.budgetFail")}
              </div>
            ) : (
              <div style={{ padding: "10px 12px" }}>
                {FIX_BUDGET.reservations.map(r => (
                  <div key={r.id} style={{ display: "grid", gridTemplateColumns: "180px 1fr auto", gap: 12, alignItems: "center", padding: "4px 0", fontSize: 12 }}>
                    <span style={{ color: "var(--fg-muted)" }}>{r.label}</span>
                    <div style={{ height: 6, background: "var(--bg-sunken)", borderRadius: 3, overflow: "hidden" }}>
                      <div style={{ width: `${Math.min(100, r.used_minor / r.reserved_minor * 100)}%`, height: "100%", background: "var(--accent)" }}/>
                    </div>
                    <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>{fmtMinor(r.used_minor)} / {fmtMinor(r.reserved_minor)}</span>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Zone: Approvals (planned) */}
          <section className="panel">
            <ZoneHeader icon="shield" title={t("dr.approvals")} count={4} extra={<span style={{ fontSize: 11, color: "var(--fg-faint)" }}>{t("dr.approvalsHint")}</span>}/>
            <div style={{ padding: "8px 12px", display: "flex", flexDirection: "column", gap: 6 }}>
              {[
                { gate: "BUDGET_GATE", trigger: "at 60% of cap", risk: "medium" },
                { gate: "QUALITY_GATE", trigger: "after each language subset (×7)", risk: "low" },
                { gate: "PUBLISH_GATE", trigger: "before deliverable finalized", risk: "high" },
                { gate: "SECURITY_GATE", trigger: "any external artifact publish", risk: "high" },
              ].map((g, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12, padding: "3px 0" }}>
                  <GateChip type={g.gate}/>
                  <span style={{ color: "var(--fg-muted)" }}>{g.trigger}</span>
                  <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: g.risk === "high" ? "var(--danger)" : g.risk === "medium" ? "var(--warn)" : "var(--fg-faint)" }}>risk: {g.risk}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Zone: Risks */}
          <section className="panel">
            <ZoneHeader icon="warn-tri" title={t("dr.risks")} count={preflight.unresolved_risks.length}/>
            <div style={{ padding: "8px 12px" }}>
              {preflight.unresolved_risks.length === 0 ? (
                <span style={{ fontSize: 12, color: "var(--fg-muted)" }}>{t("dr.risksNone")}</span>
              ) : preflight.unresolved_risks.map((r, i) => (
                <div key={i} style={{ fontSize: 12, color: "var(--fg-muted)", padding: "3px 0", display: "flex", alignItems: "center", gap: 8 }}>
                  <Icon name="warn-tri" size={11} style={{ color: "var(--warn)" }}/> {r}
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

// ─── Sub components ─────────────────────────────────────
const ZoneHeader = ({ icon, title, count, extra }) => (
  <div style={{
    display: "flex", alignItems: "center", gap: 8,
    padding: "8px 12px", borderBottom: "1px solid var(--border)",
  }}>
    <Icon name={icon} size={12} style={{ color: "var(--fg-muted)" }}/>
    <span style={{ fontSize: 12, fontWeight: 500, letterSpacing: "-0.005em" }}>{title}</span>
    {typeof count === "number" && <span className="chip">{count}</span>}
    <span style={{ marginLeft: "auto", display: "inline-flex", gap: 6 }}>{extra}</span>
  </div>
);

const FindingRow = ({ finding, selected, onSelect }) => {
  const sev = finding.severity;
  const color = sev === "error" ? "var(--danger)" : sev === "warning" ? "var(--warn)" : "var(--accent)";
  const icon = sev === "error" ? "x" : sev === "warning" ? "warn-tri" : "circle-o";
  return (
    <div onClick={onSelect} style={{
      display: "grid", gridTemplateColumns: "auto 200px 1fr auto",
      gap: 10, padding: "8px 12px",
      borderBottom: "1px solid var(--border-subtle)",
      background: selected ? "var(--bg-hover)" : "transparent",
      cursor: "pointer",
      alignItems: "flex-start",
    }}>
      <Icon name={icon} size={12} style={{ color, marginTop: 2 }}/>
      <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)", background: "var(--bg-raised)", padding: "1px 6px", borderRadius: 3, alignSelf: "flex-start" }}>{finding.code}</span>
      <div style={{ fontSize: 12, lineHeight: 1.55 }}>{finding.message}</div>
      <button className="btn sm ghost" title="Jump to subject" onClick={(e)=>{e.stopPropagation();}}>
        <Icon name="external" size={10}/> {finding.subject_ref.kind}:{finding.subject_ref.id.slice(0, 12)}…
      </button>
    </div>
  );
};

const fmtMinor = (m) => m == null ? "UNKNOWN" : `$${(m / 100000).toFixed(2)}`;

Object.assign(window, { DryRunScreen });
