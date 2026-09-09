/* Screen 6: Approvals & Interventions */

const ApprovalsScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState(FIX_APPROVALS[1].id); // high-risk model replacement
  const [expanded, setExpanded] = useState({});
  const [processed, setProcessed] = useState({});

  const pending = FIX_APPROVALS.filter(a => !processed[a.id]);
  const selected = FIX_APPROVALS.find(a => a.id === selectedId);
  const riskOrder = { high: 0, medium: 1, low: 2 };
  const sorted = [...pending].sort((a,b) => riskOrder[a.risk] - riskOrder[b.risk]);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 480px", gap: 12, flex: 1, minHeight: 0 }}>
      {/* Queue */}
      <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="shield" size={12} style={{ color: "var(--fg-muted)" }}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ap.queue")}</span>
          <span className="chip">{sorted.length} {t("ap.pending")}</span>
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--fg-muted)" }}>
            <span>{t("ap.autonomy")} <span className="mono" style={{ color: "var(--warn)" }}>GUARDED_AUTONOMOUS</span></span>
          </div>
        </div>
        <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", background: "var(--bg-sunken)", fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.5 }}>
          <Icon name="q" size={10} style={{ color: "var(--fg-faint)" }}/> {t("ap.hint")}
        </div>
        <div style={{ flex: 1, overflow: "auto", padding: 10, display: "flex", flexDirection: "column", gap: 8 }}>
          {sorted.map(a => (
            <ApprovalCard key={a.id} approval={a}
              selected={a.id === selectedId}
              expanded={!!expanded[a.id]}
              onSelect={() => setSelectedId(a.id)}
              onToggle={() => setExpanded(prev => ({ ...prev, [a.id]: !prev[a.id] }))}
              onDecide={(decision) => setProcessed(prev => ({ ...prev, [a.id]: decision }))}
            />
          ))}
        </div>
      </div>

      {/* Detail rail */}
      <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>{t("ap.consequence")}</div>
          <div style={{ fontSize: 14, fontWeight: 500 }}>{selected?.action.verb.replace(/_/g, " ")}</div>
        </div>
        {selected && (
          <div style={{ flex: 1, overflow: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              <GateChip type={selected.policy_source}/>
              <span className={`chip`} style={{
                color: selected.risk === "high" ? "var(--danger)" : selected.risk === "medium" ? "var(--warn)" : "var(--fg-muted)",
                borderColor: selected.risk === "high" ? "var(--danger-line)" : selected.risk === "medium" ? "var(--warn-line)" : "var(--border)",
              }}>{t("ap.risk")} {selected.risk}</span>
              <DigestText value={selected.id} length={14} prefix={false}/>
              <span className="chip" style={{ marginLeft: "auto" }}>v{selected.version} · {t("ap.ifMatch")}</span>
            </div>

            {/* If-Match note */}
            <div style={{ fontSize: 11, color: "var(--fg-muted)", background: "var(--bg-sunken)", padding: 10, borderRadius: 6, lineHeight: 1.55 }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--fg-faint)", marginBottom: 4 }}>{t("ap.action")}</div>
              {JSON.stringify(selected.action, null, 2).split("\n").map((line, i) => (
                <div key={i} style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{line}</div>
              ))}
            </div>

            {/* Consequences */}
            <div>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>{t("ap.willHappen")}</div>
              <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6, fontSize: 12, lineHeight: 1.55 }}>
                <ConsRow icon="graph" tone="warn" label={t("ap.cons.affects").replace("{n}", selected.consequence.affected_tasks).replace("{s}", selected.consequence.affected_tasks !== 1 ? "s" : "")}/>
                <ConsRow icon={selected.consequence.produces_manifest_revision ? "fork" : "check"}
                  tone={selected.consequence.produces_manifest_revision ? "danger" : "success"}
                  label={selected.consequence.produces_manifest_revision ? t("ap.cons.mrYes") : t("ap.cons.mrNo")}/>
                <ConsRow icon="external"
                  tone={selected.consequence.external_side_effects ? "danger" : "success"}
                  label={selected.consequence.external_side_effects ? t("ap.cons.extYes") : t("ap.cons.extNo")}/>
                <ConsRow icon={selected.consequence.produces_fork ? "fork" : "check"}
                  tone={selected.consequence.produces_fork ? "warn" : "success"}
                  label={selected.consequence.produces_fork ? t("ap.cons.forkYes") : t("ap.cons.forkNo")}/>
              </ul>
            </div>

            {/* Context */}
            <div>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>{t("ap.context")}</div>
              <div style={{ background: "var(--bg-sunken)", padding: 10, borderRadius: 6, fontSize: 11, fontFamily: "var(--font-mono)", lineHeight: 1.6 }}>
                {Object.entries(selected.context).map(([k, v]) => (
                  <div key={k}><span style={{ color: "var(--fg-faint)" }}>{k}</span> · <span style={{ color: "var(--fg-muted)" }}>{typeof v === "number" ? (k.includes("minor") ? `$${(v/100000).toFixed(2)}` : v) : String(v)}</span></div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div style={{ display: "flex", gap: 8, marginTop: "auto" }}>
              <button className="btn primary" style={{ flex: 1, height: 34 }}>
                <Icon name="check" size={11}/> {t("act.approve")}
                {selected.risk === "high" && <span style={{ marginLeft: 4, fontSize: 10, opacity: 0.8 }}>{t("ap.confirm")}</span>}
              </button>
              <button className="btn danger" style={{ flex: 1, height: 34 }}>
                <Icon name="x" size={11}/> {t("act.deny")}
              </button>
            </div>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", textAlign: "center" }}>
              Idempotency-Key: <span style={{ color: "var(--fg-muted)" }}>ik_{selected.id.slice(4)}_{Date.now().toString(36).slice(-6)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const ApprovalCard = ({ approval, selected, expanded, onSelect, onToggle, onDecide }) => { const { t } = useI18n();
  const riskTone = approval.risk === "high" ? "danger" : approval.risk === "medium" ? "warn" : "neutral";
  return (
    <div onClick={onSelect} style={{
      padding: 12, borderRadius: 6, cursor: "pointer",
      background: selected ? "var(--bg-hover)" : "var(--bg-raised)",
      border: `1px solid ${selected ? "var(--accent)" : approval.risk === "high" ? "var(--danger-line)" : "var(--border)"}`,
      borderLeft: `3px solid var(--${approval.risk === "high" ? "danger" : approval.risk === "medium" ? "warn" : "fg-muted"})`,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <GateChip type={approval.policy_source}/>
        <StatusBadge tone={riskTone} icon={approval.risk === "high" ? "warn-tri" : "circle"} label={approval.risk} size="sm" filled/>
        <DigestText value={approval.id} length={12} prefix={false}/>
        <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{approval.created_at.slice(11,16)}</span>
      </div>
      <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4, letterSpacing: "-0.005em" }}>
        <span className="mono" style={{ color: "var(--accent)" }}>{approval.action.verb}</span> · {approval.action.reason}
      </div>
      <div style={{ fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.5, marginBottom: 8 }}>
        {approval.action.target && <>target: <span className="mono">{approval.action.target}</span></>}
        {approval.action.delta_minor && <> · Δ ${(approval.action.delta_minor/100000).toFixed(2)}</>}
        {approval.action.from && <> · <span className="mono">{approval.action.from}</span> → <span className="mono">{approval.action.to}</span></>}
      </div>
      <div style={{ display: "flex", gap: 8, fontSize: 10, fontFamily: "var(--font-mono)" }}>
        {approval.consequence.produces_manifest_revision && <span style={{ color: "var(--warn)" }}>{t("ap.badgeMR")}</span>}
        {approval.consequence.external_side_effects && <span style={{ color: "var(--danger)" }}>{t("ap.badgeExt")}</span>}
        <span style={{ marginLeft: "auto", color: "var(--fg-faint)" }}>{t("ap.affectsTask")} {approval.consequence.affected_tasks} {t("lbl.tasks").toLowerCase()}{approval.consequence.affected_tasks !== 1 ? "s" : ""}</span>
      </div>
    </div>
  );
};

const ConsRow = ({ icon, tone, label }) => (
  <li style={{ display: "flex", alignItems: "center", gap: 8 }}>
    <Icon name={icon} size={11} style={{ color: `var(--${tone === "success" ? "success" : tone === "warn" ? "warn" : "danger"})` }}/>
    <span style={{ color: "var(--fg)" }}>{label}</span>
  </li>
);

Object.assign(window, { ApprovalsScreen });
