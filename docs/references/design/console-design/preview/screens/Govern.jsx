/* Screen 10: Audit / Export / Memory */

const GovernScreen = () => {
  const { t } = useI18n();
  const [tab, setTab] = useState("audit");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <div className="panel" style={{ padding: "4px 4px" }}>
        <div style={{ display: "flex", gap: 2 }}>
          {[
            ["audit", t("gv.audit"), "menu", FIX_AUDIT.length],
            ["export", t("gv.export"), "external", 1],
            ["memory", t("gv.memory"), "book", FIX_MEMORY.length],
          ].map(([id, label, icn, count]) => (
            <button key={id} onClick={() => setTab(id)} className="btn ghost" style={{
              background: tab === id ? "var(--bg-hover)" : "transparent",
              color: tab === id ? "var(--fg)" : "var(--fg-muted)",
              border: `1px solid ${tab === id ? "var(--border-strong)" : "transparent"}`,
              fontWeight: tab === id ? 500 : 400,
            }}>
              <Icon name={icn} size={11}/> {label}
              <span className="chip" style={{ marginLeft: 4 }}>{count}</span>
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        {tab === "audit" && <AuditTab/>}
        {tab === "export" && <ExportTab/>}
        {tab === "memory" && <MemoryTab/>}
      </div>
    </div>
  );
};

const AuditTab = () => { const { t } = useI18n(); return (
  <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden", height: "100%" }}>
    <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
      <Icon name="menu" size={12} style={{ color: "var(--fg-muted)" }}/>
      <span style={{ fontSize: 12, fontWeight: 500 }}>{t("gv.auditTrail")}</span>
      <span className="chip">{FIX_AUDIT.length}</span>
      <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
        <Icon name="eye-off" size={10}/> {t("gv.redacted")}
      </span>
    </div>
    <div style={{ flex: 1, overflow: "auto" }}>
      <div className="row head" style={{ gridTemplateColumns: "140px auto 140px 1fr auto 100px" }}>
        <span>{t("lbl.time")}</span><span>{t("lbl.scope")}</span><span>{t("lbl.actor")}</span><span>{t("lbl.verbSubject")}</span><span>{t("lbl.digest")}</span><span></span>
      </div>
      {FIX_AUDIT.map(a => (
        <div key={a.id} className="row" style={{ gridTemplateColumns: "140px auto 140px 1fr auto 100px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--fg-muted)" }}>{a.occurred_at.replace("T"," ").slice(0,19)}</span>
          <span className="chip">{a.scope}</span>
          <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: a.actor.kind === "user" ? "var(--accent)" : a.actor.kind === "policy" ? "var(--unknown)" : "var(--fg-muted)" }}>
            <Icon name={a.actor.kind === "user" ? "circle" : a.actor.kind === "policy" ? "shield" : "hex"} size={9}/> {a.actor.kind}{a.actor.id ? ":"+a.actor.id.slice(0,10) : ""}
          </span>
          <span style={{ fontSize: 12 }}>
            <span className="mono" style={{ color: "var(--accent)" }}>{a.verb}</span>
            <span style={{ color: "var(--fg-muted)", marginLeft: 8 }}>→ {a.subject_ref}</span>
          </span>
          <DigestText value={a.digest} length={8}/>
          <button className="btn sm ghost"><Icon name="external" size={10}/> {t("act.jump")}</button>
        </div>
      ))}
    </div>
  </div>
)};

const ExportTab = () => { const { t } = useI18n();
  const evidenceCount = FIX_EVIDENCE.length;
  const claimCount = FIX_CLAIMS.length;
  const usageEntries = FIX_BUDGET.reservations.length;
  const unknownEntries = FIX_BUDGET.unknown_cost_entries;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12, height: "100%", minHeight: 0 }}>
      {/* Bundle preview */}
      <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="external" size={12} style={{ color: "var(--fg-muted)" }}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("gv.exportPreview")}</span>
        </div>
        <div style={{ flex: 1, overflow: "auto", padding: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", gap: 12, fontSize: 12 }}>
            <span style={{ color: "var(--fg-faint)" }}>run_id</span>          <DigestText value={FIX_RUN.id} length={22} prefix={false}/>
            <span style={{ color: "var(--fg-faint)" }}>run_state</span>       <RunStateBadge state="RUNNING"/>
            <span style={{ color: "var(--fg-faint)" }}>manifest_digest</span> <DigestText value={FIX_RUN.manifest_digest} length={16}/>
            <span style={{ color: "var(--fg-faint)" }}>protocol_digest</span> <DigestText value={FIX_RUN.protocol_digest} length={16}/>
            <span style={{ color: "var(--fg-faint)" }}>exported_from</span>   <span className="mono" style={{ fontSize: 11 }}>console.researchos.io · v1.4.2</span>
            <span style={{ color: "var(--fg-faint)" }}>exported_at</span>     <span className="mono" style={{ fontSize: 11 }}>2026-08-27T14:44:03Z</span>
          </div>

          <div className="hr" style={{ margin: "16px 0" }}/>

          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 8 }}>{t("gv.contents")}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <BundleStat label={t("gv.claims")} value={claimCount} sub={`${FIX_CLAIMS.filter(c=>c.status==="VERIFIED").length} ${t("gv.claimsSub")} ${FIX_CLAIMS.filter(c=>c.status==="PROPOSED").length} ${t("gv.claimsSub2")}`}/>
            <BundleStat label={t("gv.evidenceEntries")} value={evidenceCount} sub={`${FIX_EVIDENCE.filter(e=>e.kind==="experiment").length} ${t("gv.evidenceExp")} ${FIX_EVIDENCE.filter(e=>e.kind==="literature").length} ${t("gv.evidenceLit")}`}/>
            <BundleStat label={t("gv.usageEntries")} value={usageEntries} sub={<span style={{ color: "var(--unknown)" }}>{unknownEntries} {t("gv.usageEntriesSub")}</span>} unknown/>
            <BundleStat label={t("gv.approvalsDecided")} value={FIX_APPROVALS.length} sub={t("gv.approvalsSub")}/>
          </div>

          <div className="hr" style={{ margin: "16px 0" }}/>

          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 8 }}>{t("gv.integrity")}</div>
          <div style={{ fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.6 }}>
            {t("gv.integrityMsg")}
          </div>
        </div>
        <div style={{ padding: 12, borderTop: "1px solid var(--border)", display: "flex", gap: 8, alignItems: "center" }}>
          <button className="btn primary" style={{ flex: 1, height: 32 }}>
            <Icon name="external" size={11}/> {t("gv.exportSealed")}
          </button>
          <button className="btn"><Icon name="copy" size={11}/> {t("gv.copyManifest")}</button>
        </div>
      </div>

      {/* Warnings */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, minHeight: 0 }}>
        <div className="panel" style={{ padding: 14 }}>
          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 8 }}>{t("gv.summary")}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Icon name="check" size={12} style={{ color: "var(--success)" }}/> {t("gv.sum1")}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Icon name="warn-tri" size={12} style={{ color: "var(--warn)" }}/> {t("gv.sum2")}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Icon name="q" size={12} style={{ color: "var(--unknown)" }}/> {t("gv.sum3")} <span className="mono">reproduction_available=false</span>{t("gv.sum3b")}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Icon name="q" size={12} style={{ color: "var(--unknown)" }}/> {t("gv.sum4")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const BundleStat = ({ label, value, sub, unknown }) => (
  <div style={{
    padding: 10,
    background: unknown ? "var(--unknown-dim)" : "var(--bg-raised)",
    border: `1px ${unknown ? "dashed" : "solid"} ${unknown ? "var(--unknown-line)" : "var(--border)"}`,
    borderRadius: 6,
  }}>
    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: 18, fontWeight: 500, fontFamily: "var(--font-mono)", marginBottom: 3 }}>{value}</div>
    <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>{sub}</div>
  </div>
);

const MemoryTab = () => { const { t } = useI18n(); return (
  <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden", height: "100%" }}>
    <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
      <Icon name="book" size={12} style={{ color: "var(--fg-muted)" }}/>
      <span style={{ fontSize: 12, fontWeight: 500 }}>{t("gv.memWrites")}</span>
      <span className="chip">{FIX_MEMORY.filter(m => m.status === "pending").length} {t("gv.memPending")}</span>
      <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--fg-muted)" }}>
        {t("gv.memHint")}
      </span>
    </div>
    <div style={{ flex: 1, overflow: "auto", padding: 12, display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: 10, alignContent: "start" }}>
      {FIX_MEMORY.map(m => (
        <div key={m.id} className="panel" style={{
          padding: 12,
          background: m.status === "approved" ? "var(--success-dim)" : "var(--bg-raised)",
          border: `1px solid ${m.status === "approved" ? "var(--success-line)" : "var(--border)"}`,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span className="chip" style={{ color: m.scope === "org" ? "var(--accent)" : "var(--fg-muted)", borderColor: m.scope === "org" ? "var(--accent-line)" : "var(--border)" }}>{m.scope}</span>
            <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)" }}>{t("gv.confidence")} {m.confidence.toFixed(2)}</span>
            {m.status === "approved" && <StatusBadge tone="success" icon="check" label={t("act.approve").toUpperCase()} filled size="sm"/>}
            <DigestText value={m.id} length={6} prefix={false}/>
          </div>
          <div style={{ fontSize: 12, lineHeight: 1.55, marginBottom: 10 }}>{m.statement}</div>
          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", marginBottom: 8 }}>
            {t("gv.provenance")} {m.provenance.slice(0, 2).join(" · ")}{m.provenance.length > 2 ? ` +${m.provenance.length - 2}` : ""}
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button className="btn sm" disabled={m.status === "approved"} style={{ flex: 1, borderColor: "var(--success-line)", color: "var(--success)" }}>
              <Icon name="check" size={10}/> {t("act.approve")}
            </button>
            <button className="btn sm" disabled={m.status === "approved"} style={{ flex: 1, borderColor: "var(--danger-line)", color: "var(--danger)" }}>
              <Icon name="x" size={10}/> {t("act.reject")}
            </button>
            <button className="btn sm ghost" style={{ color: "var(--fg-muted)" }} title={t("gv.deleteReal")}>
              <Icon name="ban" size={10}/> {t("act.delete")}
            </button>
          </div>
        </div>
      ))}
    </div>
  </div>
)};

Object.assign(window, { GovernScreen });
