/* Incidents / Postmortem — close the loop between alerts and audit.
   List view + detail with timeline + RCA + action items. */

const INCIDENTS = [
  {
    id: "inc_2026_0827_a",
    title: "prod-us-east endpoint p95 latency breach (1.2s SLO)",
    severity: "sev2",
    status: "resolved",
    opened_at: "2026-08-27T12:12:00Z",
    resolved_at: "2026-08-27T13:44:00Z",
    duration_min: 92,
    commander: "leo.tanaka@research.io",
    scope: ["endpoint:prod-us-east", "run:run_01K5FZ8G3X2QN4M"],
    impact: "3 runs entered SUPERVISED autonomy; 82 requests degraded",
    rca_cause: "Cold-start capacity in us-east region insufficient after gemini failover",
    action_items: [
      { id: "ai_01", text: "Add 20% warm-pool headroom in us-east", owner: "kai.nakamura", status: "in-progress", due: "2026-09-05" },
      { id: "ai_02", text: "Alert threshold for cold-start count > 5/min", owner: "leo.tanaka", status: "done", due: "2026-08-29" },
      { id: "ai_03", text: "Playbook: model-failover runbook v2", owner: "yui.sato", status: "todo", due: "2026-09-12" },
    ],
    timeline: [
      { at: "12:12", event: "Alert fired · rule=lat.p95>1200ms", actor: "system" },
      { at: "12:14", event: "PagerDuty escalation · commander assumed", actor: "leo.tanaka" },
      { at: "12:22", event: "Root cause identified · cold-start capacity", actor: "kai.nakamura" },
      { at: "12:38", event: "Mitigation · manually scaled warm pool +30%", actor: "kai.nakamura" },
      { at: "13:12", event: "Latency recovered to <400ms p95", actor: "system" },
      { at: "13:44", event: "Incident closed · postmortem opened", actor: "leo.tanaka" },
    ],
  },
  {
    id: "inc_2026_0821_b",
    title: "Run prompt-inj · v3 failed with reviewer capacity exhausted",
    severity: "sev3",
    status: "postmortem",
    opened_at: "2026-08-19T22:14:00Z",
    resolved_at: "2026-08-19T23:02:00Z",
    duration_min: 48,
    commander: "yui.sato@research.io",
    scope: ["run:run_01K51G9K3M1F8P"],
    impact: "8/18 tasks failed to receive human review within SLA",
    rca_cause: "Review pool for prompt-injection domain only had 2 qualified reviewers, both offline",
    action_items: [
      { id: "ai_04", text: "Cross-train 3 additional reviewers for prompt-inj domain", owner: "yui.sato", status: "in-progress", due: "2026-09-30" },
      { id: "ai_05", text: "Auto-downgrade autonomy when review pool < 2 online", owner: "leo.tanaka", status: "done", due: "2026-08-26" },
    ],
    timeline: [
      { at: "22:14", event: "Run started · autonomy=SUPERVISED", actor: "system" },
      { at: "22:31", event: "First task awaited review · no reviewer online", actor: "system" },
      { at: "22:55", event: "Reviewer capacity alert · sev3", actor: "system" },
      { at: "23:02", event: "Run failed after 8 tasks timed out", actor: "system" },
    ],
  },
  {
    id: "inc_2026_0817_c",
    title: "Budget cap breach · med-qa project +$680 over cap",
    severity: "sev3",
    status: "open",
    opened_at: "2026-08-17T09:30:00Z",
    resolved_at: null,
    duration_min: null,
    commander: "leo.tanaka@research.io",
    scope: ["project:proj_01K5FZ8G3X2QN4M"],
    impact: "Approval flow triggered; run paused pending PI decision",
    rca_cause: null,
    action_items: [
      { id: "ai_06", text: "Draft budget forecasting policy for arabic subset", owner: "leo.tanaka", status: "todo", due: "2026-09-02" },
    ],
    timeline: [
      { at: "09:30", event: "Budget breach detected · cap=$5000 spent=$5680", actor: "system" },
      { at: "09:31", event: "Run auto-paused, approval requested", actor: "system" },
      { at: "09:45", event: "Awaiting PI review", actor: "system" },
    ],
  },
];

const IncidentsScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState(INCIDENTS[0].id);
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = statusFilter === "all" ? INCIDENTS : INCIDENTS.filter(i => i.status === statusFilter);
  const selected = INCIDENTS.find(i => i.id === selectedId);

  const sevMap = {
    sev1: { color: "var(--danger)", label: "SEV1", icon: "warn-tri" },
    sev2: { color: "var(--warn)", label: "SEV2", icon: "warn-tri" },
    sev3: { color: "var(--fg-muted)", label: "SEV3", icon: "diamond" },
    sev4: { color: "var(--fg-faint)", label: "SEV4", icon: "circle-o" },
  };
  const stMap = {
    open: { tone: "danger", icon: "warn-tri", label: "OPEN" },
    postmortem: { tone: "warn", icon: "clock", label: "POSTMORTEM" },
    resolved: { tone: "success", icon: "check", label: "RESOLVED", filled: true },
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("ic.title")} subtitle={t("ic.subtitle")}>
        <ViewSwitcher value={statusFilter} onChange={setStatusFilter} views={[
          { value: "all", label: `${t("ic.all")} (${INCIDENTS.length})` },
          { value: "open", label: t("ic.open") },
          { value: "postmortem", label: t("ic.postmortem") },
          { value: "resolved", label: t("ic.resolved") },
        ]}/>
        <button className="btn primary sm"><Icon name="plus" size={11}/> {t("ic.declare")}</button>
      </PageToolbar>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <MetricCard label={t("ic.mOpen")} value={INCIDENTS.filter(i => i.status === "open").length} sub={<span>{t("ic.mOpenSub")}</span>}/>
        <MetricCard label={t("ic.mMTTR")} value="82m" sub={<span>{t("ic.mMTTRSub")}</span>}/>
        <MetricCard label={t("ic.mMTTD")} value="4m" sub={<span>{t("ic.mMTTDSub")}</span>}/>
        <MetricCard label={t("ic.mActions")} value="4 / 7" sub={<span>{t("ic.mActionsSub")}</span>} bar={4/7}/>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: 12, flex: 1, minHeight: 0 }}>
        {/* List */}
        <div className="panel" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", fontSize: 12, fontWeight: 500 }}>{t("ic.queue")}</div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {filtered.map(inc => {
              const active = inc.id === selectedId;
              const sev = sevMap[inc.severity];
              const st = stMap[inc.status];
              return (
                <div key={inc.id} onClick={() => setSelectedId(inc.id)} style={{
                  padding: 12, borderBottom: "1px solid var(--border-subtle)",
                  cursor: "pointer",
                  background: active ? "var(--bg-hover)" : "transparent",
                  borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <Icon name={sev.icon} size={12} style={{ color: sev.color }}/>
                    <span className="mono" style={{ fontSize: 10, color: sev.color, fontWeight: 600 }}>{sev.label}</span>
                    <StatusBadge tone={st.tone} icon={st.icon} label={st.label} filled={st.filled} size="sm"/>
                    <span className="mono" style={{ marginLeft: "auto", fontSize: 10, color: "var(--fg-faint)" }}>{inc.id}</span>
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 4 }}>{inc.title}</div>
                  <div style={{ display: "flex", gap: 12, fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
                    <span>{new Date(inc.opened_at).toISOString().slice(5, 16).replace("T", " ")}</span>
                    <span>·</span>
                    <span>{inc.duration_min != null ? `${inc.duration_min}m` : t("ic.ongoing")}</span>
                    <span>·</span>
                    <span>{inc.commander.split("@")[0]}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Detail */}
        {selected && (
          <div className="panel" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <StatusBadge tone={stMap[selected.status].tone} icon={stMap[selected.status].icon} label={stMap[selected.status].label} filled={stMap[selected.status].filled}/>
                <span className="mono" style={{ fontSize: 10, color: sevMap[selected.severity].color, fontWeight: 600 }}>{sevMap[selected.severity].label}</span>
                <span className="mono" style={{ marginLeft: "auto", fontSize: 10, color: "var(--fg-faint)" }}>{selected.id}</span>
              </div>
              <div style={{ fontSize: 15, fontWeight: 500, letterSpacing: "-0.005em" }}>{selected.title}</div>
              <div style={{ marginTop: 8, display: "flex", gap: 12, fontSize: 11, color: "var(--fg-muted)", flexWrap: "wrap" }}>
                <span><span style={{ color: "var(--fg-faint)" }}>{t("ic.commander")}:</span> {selected.commander.split("@")[0]}</span>
                <span><span style={{ color: "var(--fg-faint)" }}>{t("ic.opened")}:</span> {new Date(selected.opened_at).toISOString().slice(0, 16).replace("T", " ")}</span>
                {selected.resolved_at && <span><span style={{ color: "var(--fg-faint)" }}>{t("ic.resolved")}:</span> {new Date(selected.resolved_at).toISOString().slice(0, 16).replace("T", " ")}</span>}
              </div>
            </div>

            <div style={{ flex: 1, overflow: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
              {/* Impact */}
              <Section label={t("ic.impact")}>
                <div style={{ fontSize: 12, lineHeight: 1.5 }}>{selected.impact}</div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
                  {selected.scope.map(s => <span key={s} className="chip mono" style={{ fontSize: 10 }}>{s}</span>)}
                </div>
              </Section>

              {/* Timeline */}
              <Section label={t("ic.timeline")}>
                <div style={{ display: "flex", flexDirection: "column", gap: 6, position: "relative" }}>
                  <div style={{ position: "absolute", left: 10, top: 4, bottom: 4, width: 1, background: "var(--border)" }}/>
                  {selected.timeline.map((ev, i) => (
                    <div key={i} style={{ display: "grid", gridTemplateColumns: "40px 12px 1fr auto", gap: 10, alignItems: "center", position: "relative" }}>
                      <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)", textAlign: "right" }}>{ev.at}</span>
                      <span style={{
                        width: 8, height: 8, borderRadius: "50%",
                        background: ev.actor === "system" ? "var(--warn)" : "var(--accent)",
                        border: "2px solid var(--bg-panel)",
                        gridColumn: 2, justifySelf: "center",
                        boxShadow: "0 0 0 2px var(--bg-panel)",
                      }}/>
                      <span style={{ fontSize: 12 }}>{ev.event}</span>
                      <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)" }}>{ev.actor}</span>
                    </div>
                  ))}
                </div>
              </Section>

              {/* RCA */}
              <Section label={t("ic.rca")}>
                {selected.rca_cause ? (
                  <div style={{
                    padding: 12, background: "var(--bg-raised)",
                    borderLeft: "3px solid var(--danger)", borderRadius: 4,
                    fontSize: 12, lineHeight: 1.6,
                  }}>{selected.rca_cause}</div>
                ) : (
                  <div className="empty-mark" style={{ display: "inline-flex" }}>{t("ic.rcaPending")}</div>
                )}
              </Section>

              {/* Action items */}
              <Section label={`${t("ic.actionItems")} (${selected.action_items.filter(a => a.status === "done").length}/${selected.action_items.length})`}>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {selected.action_items.map(a => {
                    const st = a.status === "done" ? { icon: "check", color: "var(--success)" }
                      : a.status === "in-progress" ? { icon: "spin", color: "var(--accent)" }
                      : { icon: "circle-o", color: "var(--fg-faint)" };
                    return (
                      <div key={a.id} style={{
                        display: "grid",
                        gridTemplateColumns: "14px 1fr 100px 90px",
                        gap: 10, alignItems: "center",
                        padding: "8px 10px",
                        background: "var(--bg-raised)",
                        border: "1px solid var(--border)",
                        borderRadius: 4,
                      }}>
                        <Icon name={st.icon} size={12} style={{ color: st.color }}/>
                        <span style={{ fontSize: 11, textDecoration: a.status === "done" ? "line-through" : "none", color: a.status === "done" ? "var(--fg-muted)" : "var(--fg)" }}>{a.text}</span>
                        <span className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>{a.owner}</span>
                        <span className="mono" style={{ fontSize: 10, color: a.status === "done" ? "var(--fg-faint)" : "var(--warn)" }}>{a.due}</span>
                      </div>
                    );
                  })}
                </div>
              </Section>
            </div>

            <div style={{ padding: 12, borderTop: "1px solid var(--border)", display: "flex", gap: 6 }}>
              <button className="btn sm ghost" style={{ marginLeft: "auto" }}><Icon name="external" size={11}/> {t("ic.export")}</button>
              {selected.status !== "resolved" && <button className="btn primary sm"><Icon name="check" size={11}/> {t("ic.markResolved")}</button>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const Section = ({ label, children }) => (
  <div>
    <div style={{
      fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)",
      letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8,
    }}>{label}</div>
    {children}
  </div>
);

Object.assign(window, { IncidentsScreen });
