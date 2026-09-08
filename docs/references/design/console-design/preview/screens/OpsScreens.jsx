/* Four ops/assets screens bundled to keep file count sane:
   AlertsScreen · SchedulesScreen · IntegrationsScreen · ModelRegistryScreen */

// ═══════════════════════════════════════════════════════════════════════════
// Alerts Center
// ═══════════════════════════════════════════════════════════════════════════

const AlertsScreen = () => {
  const { t } = useI18n();
  const [tab, setTab] = useState("inbox");
  const [drawer, setDrawer] = useState(null);
  const [rules, setRules] = useState(FIX_ALERT_RULES);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("al.title")} subtitle={t("al.subtitle")}>
        <ViewSwitcher value={tab} onChange={setTab} views={[
          { value: "inbox", label: t("al.viewInbox"), icon: "menu" },
          { value: "rules", label: t("al.viewRules"), icon: "shield" },
          { value: "channels", label: t("al.viewChannels"), icon: "wifi" },
        ]}/>
        <button className="btn primary sm" onClick={() => setDrawer({ mode: "create-rule" })}><Icon name="plus" size={11}/> {t("al.new")}</button>
      </PageToolbar>

      {tab === "inbox" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 4 }}>
          <MetricCard label={t("al.mFiring")} value={FIX_ALERT_INBOX.filter(a => a.state === "firing").length} sub={<span>{t("al.mFiringSub")}</span>}/>
          <MetricCard label={t("al.mAcked")} value={FIX_ALERT_INBOX.filter(a => a.state === "acknowledged").length} sub={<span>{t("al.mAckedSub")}</span>}/>
          <MetricCard label={t("al.mResolved")} value={FIX_ALERT_INBOX.filter(a => a.state === "resolved").length} sub={<span>{t("al.mResolvedSub")}</span>}/>
          <MetricCard label={t("al.mRules")} value={rules.filter(r => r.enabled).length} sub={<span>{t("al.mRulesSub").replace("{n}", rules.length)}</span>}/>
        </div>
      )}

      {tab === "inbox" && (
        <div className="panel" style={{ overflow: "hidden", flex: 1 }}>
          <div className="row head" style={{ gridTemplateColumns: "24px 90px 130px minmax(220px, 1.6fr) 110px 110px 90px" }}>
            <span></span><span>{t("lbl.severity")}</span><span>{t("lbl.state")}</span><span>{t("lbl.subject")}</span><span>{t("lbl.rule")}</span><span>{t("lbl.firedAt")}</span><span>{t("lbl.ackBy")}</span>
          </div>
          <div style={{ overflow: "auto" }}>
            {FIX_ALERT_INBOX.map(a => (
              <div key={a.id} className="row" style={{ gridTemplateColumns: "24px 90px 130px minmax(220px, 1.6fr) 110px 110px 90px" }}>
                <span><Icon name={a.state === "firing" ? "warn-tri" : a.state === "acknowledged" ? "clock" : "check"} size={11} style={{
                  color: a.state === "firing" ? "var(--danger)" : a.state === "acknowledged" ? "var(--warn)" : "var(--success)"
                }}/></span>
                <span><StatusBadge tone={a.severity === "high" ? "danger" : a.severity === "medium" ? "warn" : "neutral"} label={a.severity.toUpperCase()} icon={a.severity === "high" ? "warn-tri" : a.severity === "medium" ? "diamond" : "circle-o"} filled/></span>
                <span><StatusBadge tone={a.state === "firing" ? "danger" : a.state === "acknowledged" ? "warn" : "success"} label={a.state.toUpperCase()} icon={a.state === "firing" ? "warn-tri" : a.state === "acknowledged" ? "clock" : "check"}/></span>
                <span style={{ fontSize: 12 }}>{a.subject}</span>
                <span className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>{a.rule_id}</span>
                <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)" }}>{new Date(a.fired_at).toISOString().replace("T"," ").slice(5,16)}</span>
                <span style={{ fontSize: 10, color: "var(--fg-muted)" }}>{a.ack_by ? a.ack_by.split("@")[0] : "—"}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "rules" && (
        <div className="panel" style={{ overflow: "hidden", flex: 1 }}>
          <div className="row head" style={{ gridTemplateColumns: "50px minmax(240px, 1.6fr) 90px 100px minmax(160px, 1fr) 110px 60px" }}>
            <span>{t("al.colOn")}</span><span>{t("lbl.rule")}</span><span>{t("lbl.severity")}</span><span>{t("lbl.scope")}</span><span>{t("lbl.channels")}</span><span>{t("lbl.suppress")}</span><span>7d</span>
          </div>
          <div style={{ overflow: "auto" }}>
            {rules.map(r => (
              <div key={r.id} className="row" style={{ gridTemplateColumns: "50px minmax(240px, 1.6fr) 90px 100px minmax(160px, 1fr) 110px 60px", cursor: "pointer" }}>
                <span>
                  <Toggle on={r.enabled} onToggle={() => setRules(rs => rs.map(x => x.id === r.id ? { ...x, enabled: !x.enabled } : x))}/>
                </span>
                <div className="row-cell-wrap" style={{ minWidth: 0, overflow: "hidden" }}>
                  <div style={{ fontSize: 12, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{r.name}</div>
                  <div className="mono" style={{ fontSize: 10, color: "var(--fg-faint)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{r.condition}</div>
                </div>
                <span><StatusBadge tone={r.severity === "high" ? "danger" : r.severity === "medium" ? "warn" : "neutral"} label={r.severity.toUpperCase()} icon={r.severity === "high" ? "warn-tri" : "circle-o"} size="sm"/></span>
                <span className="chip" style={{ fontSize: 9 }}>{r.scope}</span>
                <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.channels.join(" · ")}</span>
                <span className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>{r.suppress_min}{t("al.window")}</span>
                <span className="mono" style={{ fontSize: 10, color: r.fire_count_7d > 3 ? "var(--warn)" : "var(--fg-muted)" }}>{r.fire_count_7d}×</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "channels" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
          {[
            { name: "Slack · #research-ops", type: "chat", status: "healthy", stats: "12 alerts / 24h" },
            { name: "Slack · #platform", type: "chat", status: "healthy", stats: "3 alerts / 24h" },
            { name: "PagerDuty · oncall-a", type: "pager", status: "degraded", stats: "on-call not set for weekends" },
            { name: "Email · pi@research.io", type: "email", status: "healthy", stats: "1 alert / 24h" },
            { name: "Webhook · audit-bus", type: "webhook", status: "healthy", stats: "62 events / 24h" },
          ].map(c => (
            <div key={c.name} className="panel" style={{ padding: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <Icon name={c.type === "chat" ? "menu" : c.type === "pager" ? "warn-tri" : c.type === "email" ? "external" : "wifi"} size={12} style={{ color: "var(--accent)" }}/>
                <span style={{ fontSize: 12, fontWeight: 500, flex: 1 }}>{c.name}</span>
                <StatusBadge tone={c.status === "healthy" ? "success" : "warn"} label={c.status.toUpperCase()} icon={c.status === "healthy" ? "check" : "warn-tri"} size="sm"/>
              </div>
              <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>{c.stats}</div>
            </div>
          ))}
        </div>
      )}

      <Drawer open={!!drawer} onClose={() => setDrawer(null)} title={t("al.new")} subtitle={t("al.newSub")} width={520}
        footer={<>
          <button className="btn ghost" onClick={() => setDrawer(null)}>{t("act.cancel")}</button>
          <button className="btn primary" style={{ marginLeft: "auto" }} onClick={() => setDrawer(null)}><Icon name="check" size={11}/> {t("al.createRule")}</button>
        </>}>
        <FormRow label={t("lbl.name")} required><TextInput placeholder={t("al.form.namePh")}/></FormRow>
        <FormRow label={t("lbl.scope")}><Select value="budget" onChange={() => {}} options={[
          { value: "budget", label: "Budget" }, { value: "endpoint", label: "Endpoint" }, { value: "model", label: "Model" }, { value: "run", label: "Run" }, { value: "claim", label: "Claim" },
        ]}/></FormRow>
        <FormRow label={t("lbl.condition")} hint={t("al.form.condHint")}><TextArea mono rows={2} placeholder={t("al.form.condPh")}/></FormRow>
        <FormRow label={t("lbl.severity")}><Select value="medium" onChange={() => {}} options={[
          { value: "high", label: t("al.form.sevHigh") }, { value: "medium", label: t("al.form.sevMid") }, { value: "low", label: t("al.form.sevLow") },
        ]}/></FormRow>
        <FormRow label={t("lbl.channels")}><TagInput tags={["slack:#research-ops"]} onChange={() => {}}/></FormRow>
        <FormRow label={t("lbl.suppression")} hint={t("al.form.suppressHint")}><TextInput mono placeholder="30"/></FormRow>
      </Drawer>
    </div>
  );
};

const Toggle = ({ on, onToggle }) => (
  <button onClick={onToggle} style={{
    width: 28, height: 14, borderRadius: 7,
    background: on ? "var(--accent)" : "var(--bg-sunken)",
    border: `1px solid ${on ? "var(--accent)" : "var(--border-strong)"}`,
    padding: 0, cursor: "pointer", position: "relative",
  }}>
    <div style={{
      width: 10, height: 10, borderRadius: "50%",
      background: "#fff",
      position: "absolute", top: 1, left: on ? 15 : 1,
      transition: "left 140ms",
    }}/>
  </button>
);

// ═══════════════════════════════════════════════════════════════════════════
// Schedules
// ═══════════════════════════════════════════════════════════════════════════

const SchedulesScreen = () => {
  const { t } = useI18n();
  const [drawer, setDrawer] = useState(null);
  const [schedules, setSchedules] = useState(FIX_SCHEDULES);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("sc.title")} subtitle={t("sc.subtitle")}>
        <button className="btn primary sm" onClick={() => setDrawer({})}><Icon name="plus" size={11}/> {t("sc.new")}</button>
      </PageToolbar>

      <div className="panel" style={{ overflow: "hidden" }}>
        <div className="row head" style={{ gridTemplateColumns: "50px minmax(200px, 1.5fr) 130px 90px 130px 130px 100px" }}>
          <span>{t("al.colOn")}</span><span>{t("sc.colSchedule")}</span><span>{t("lbl.cron")}</span><span>{t("lbl.target")}</span><span>{t("lbl.lastRun")}</span><span>{t("lbl.nextRun")}</span><span>{t("lbl.streak")}</span>
        </div>
        <div style={{ overflow: "auto" }}>
          {schedules.map(s => (
            <div key={s.id} className="row" style={{ gridTemplateColumns: "50px minmax(200px, 1.5fr) 130px 90px 130px 130px 100px" }}>
              <span><Toggle on={s.enabled} onToggle={() => setSchedules(prev => prev.map(x => x.id === s.id ? { ...x, enabled: !x.enabled } : x))}/></span>
              <div className="row-cell-wrap" style={{ minWidth: 0, overflow: "hidden" }}>
                <div style={{ fontSize: 12, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{s.name}</div>
                {s.depends_on.length > 0 && (
                  <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {t("sc.dependsOn")} {s.depends_on.join(", ")}
                  </div>
                )}
              </div>
              <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>{s.cron}</span>
              <span className="chip" style={{ fontSize: 9 }}>{s.target}</span>
              <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)" }}>{s.last_run ? new Date(s.last_run).toISOString().replace("T"," ").slice(5,16) : "—"}</span>
              <span className="mono" style={{ fontSize: 10, color: s.next_run ? "var(--accent)" : "var(--fg-faint)" }}>{s.next_run ? new Date(s.next_run).toISOString().replace("T"," ").slice(5,16) : t("sc.manual")}</span>
              <span className="mono" style={{ fontSize: 11, color: s.success_streak > 10 ? "var(--success)" : "var(--fg-muted)" }}>{s.success_streak} ✓</span>
            </div>
          ))}
        </div>
      </div>

      {/* Dependency graph */}
      <div className="panel" style={{ padding: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <Icon name="graph" size={12}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("sc.depGraph")}</span>
        </div>
        <div style={{ background: "var(--bg-sunken)", borderRadius: 6, padding: 12 }}>
          <ForceGraph
            nodes={schedules.map(s => ({ id: s.id, label: s.name.slice(0, 26), group: s.enabled ? "on" : "off" }))}
            edges={schedules.flatMap(s => s.depends_on.map(d => ({ from: d, to: s.id })))}
            width={780} height={220}
            groupColors={{ on: "var(--accent)", off: "var(--fg-faint)" }}
          />
        </div>
      </div>

      <Drawer open={!!drawer} onClose={() => setDrawer(null)} title={t("sc.new")} subtitle={t("sc.newSub")} width={480}
        footer={<>
          <button className="btn ghost" onClick={() => setDrawer(null)}>{t("act.cancel")}</button>
          <button className="btn primary" style={{ marginLeft: "auto" }} onClick={() => setDrawer(null)}><Icon name="check" size={11}/> {t("act.create")}</button>
        </>}>
        <FormRow label={t("lbl.name")} required><TextInput placeholder={t("sc.form.namePh")}/></FormRow>
        <FormRow label={t("lbl.cronExpr")} required hint={t("sc.form.cronHint")}><TextInput mono placeholder={t("sc.form.cronPh")}/></FormRow>
        <FormRow label={t("lbl.target")}><Select value="experiment" onChange={() => {}} options={[
          { value: "experiment", label: t("sc.form.tgtExp") }, { value: "probe", label: t("sc.form.tgtProbe") }, { value: "report", label: t("sc.form.tgtRep") }, { value: "graph", label: t("sc.form.tgtGraph") },
        ]}/></FormRow>
        <FormRow label={t("lbl.dependsOn")}><TagInput tags={[]} onChange={() => {}}/></FormRow>
      </Drawer>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// Integrations
// ═══════════════════════════════════════════════════════════════════════════

const IntegrationsScreen = () => {
  const { t } = useI18n();
  const [tab, setTab] = useState("all");
  const filtered = tab === "all" ? FIX_INTEGRATIONS : FIX_INTEGRATIONS.filter(i => i.status === tab);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0, overflow: "auto" }}>
      <PageToolbar title={t("in.title")} subtitle={t("in.subtitle")}>
        <ViewSwitcher value={tab} onChange={setTab} views={[
          { value: "all", label: t("in.viewAll") },
          { value: "connected", label: t("in.viewConn") },
          { value: "available", label: t("in.viewAvail") },
          { value: "disconnected", label: t("in.viewDisc") },
        ]}/>
      </PageToolbar>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 12 }}>
        {filtered.map(int => (
          <div key={int.id} className="panel" style={{ padding: 14, display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 6,
                background: "var(--bg-raised)", border: "1px solid var(--border)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 600, color: "var(--accent)",
              }}>{int.name.slice(0, 2).toUpperCase()}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{int.name}</div>
                <div className="mono" style={{ fontSize: 9, color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{int.category.toUpperCase()}</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
              {int.status === "connected" && <StatusBadge tone="success" icon="check" label={t("in.stat.connected")} size="sm" filled/>}
              {int.status === "available" && <StatusBadge tone="neutral" icon="circle-o" label={t("in.stat.available")} size="sm" dashed/>}
              {int.status === "disconnected" && <StatusBadge tone="danger" icon="x" label={t("in.stat.disconnected")} size="sm"/>}
              {int.health === "degraded" && <StatusBadge tone="warn" icon="warn-tri" label={t("in.stat.degraded")} size="sm"/>}
            </div>
            {int.status === "connected" && Object.keys(int.meta).length > 0 && (
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", lineHeight: 1.5 }}>
                {Object.entries(int.meta).slice(0, 2).map(([k, v]) => (
                  <div key={k}><span style={{ color: "var(--fg-faint)" }}>{k}:</span> {v}</div>
                ))}
              </div>
            )}
            {int.issue && <div style={{ fontSize: 10, color: "var(--warn)" }}>{int.issue}</div>}
            {int.disconnect_reason && <div style={{ fontSize: 10, color: "var(--danger)" }}>{int.disconnect_reason}</div>}
            <div style={{ marginTop: "auto", paddingTop: 6, display: "flex", gap: 6 }}>
              {int.status === "connected" && <button className="btn sm ghost">{t("act.configure")}</button>}
              {int.status === "available" && <button className="btn sm primary" style={{ width: "100%" }}><Icon name="plus" size={10}/> {t("act.connect")}</button>}
              {int.status === "disconnected" && <button className="btn sm" style={{ width: "100%" }}><Icon name="spin" size={10}/> {t("act.reconnect")}</button>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// Model Registry
// ═══════════════════════════════════════════════════════════════════════════

const ModelRegistryScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState("mdl_claude_opus_41");
  const [q, setQ] = useState("");
  const [drawer, setDrawer] = useState(null);
  const filtered = q ? FIX_REGISTERED_MODELS.filter(m => m.family.toLowerCase().includes(q.toLowerCase()) || m.provider.toLowerCase().includes(q.toLowerCase())) : FIX_REGISTERED_MODELS;
  const selected = FIX_REGISTERED_MODELS.find(m => m.id === selectedId);

  // Column tracks — `minmax(140px, …fr)` guarantees the model column keeps
  // enough room for the family label + tag chips even when the panel is
  // narrow, while `min-width: 0` on cells (see tokens.css) stops content
  // from pushing the track wider than allotted and breaking row alignment.
  // Layout: model | provider | released | context | license.
  // The 30d-usage column moved to the DETAIL panel (a full sparkline
  // already lives there) — removing it from the master list keeps the
  // remaining columns readable in a two-pane layout without a horizontal
  // scrollbar. Widened provider (→92) and license (→100) so "Anthropic"
  // / "apache-2.0" fit on one line at any panel width. Model column has
  // a stronger min-width so family + tag chips never wrap.
  const cols = "minmax(160px, 1.6fr) 92px 90px 60px 100px";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("mr.title")} subtitle={t("mr.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("mr.search")} width={220}/>
        <button className="btn primary sm" onClick={() => setDrawer({})}><Icon name="plus" size={11}/> {t("mr.register")}</button>
      </PageToolbar>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 12, flex: 1, minHeight: 0 }}>
        <div className="panel" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div className="row head" style={{ gridTemplateColumns: cols }}>
            <span>{t("mr.col.model")}</span><span>{t("mr.col.provider")}</span><span>{t("mr.col.family")}</span><span>{t("mr.col.context")}</span><span>{t("mr.col.license")}</span>
          </div>
          <div style={{ overflow: "auto", flex: 1 }}>
            {filtered.map(m => {
              const active = m.id === selectedId;
              return (
                <div key={m.id} className="row" onClick={() => setSelectedId(m.id)}
                  style={{ gridTemplateColumns: cols, cursor: "pointer", background: active ? "var(--bg-hover)" : undefined, borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}` }}>
                  <div className="row-cell-wrap" style={{ minWidth: 0, overflow: "hidden" }}>
                    <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{m.family}</div>
                    <div style={{ display: "flex", gap: 3, marginTop: 2, overflow: "hidden", whiteSpace: "nowrap" }}>
                      {m.tags.slice(0, 2).map(tag => <span key={tag} className="chip" style={{ fontSize: 9, height: 14, flexShrink: 0 }}>{tag}</span>)}
                      {m.tags.length > 2 && <span style={{ fontSize: 9, color: "var(--fg-faint)", flexShrink: 0, alignSelf: "center" }}>+{m.tags.length - 2}</span>}
                    </div>
                  </div>
                  <span style={{ fontSize: 11, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{m.provider}</span>
                  <span className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>{m.released}</span>
                  <span className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>{(m.context/1000).toFixed(0)}k</span>
                  <span className="chip" style={{ fontSize: 9, justifySelf: "start", maxWidth: "100%", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{m.license.slice(0, 14)}</span>
                </div>
              );
            })}
          </div>
        </div>

        {selected && (
          <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)" }}>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{selected.provider} · {selected.released}</div>
              <div style={{ fontSize: 15, fontWeight: 500, fontFamily: "var(--font-mono)" }}>{selected.family}</div>
              <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                {selected.tags.map(tag => <span key={tag} className="chip" style={{ background: "var(--accent-dim)", color: "var(--accent)", borderColor: "var(--accent-line)" }}>{tag}</span>)}
              </div>
              {selected.warning && (
                <div style={{ marginTop: 10, padding: 10, background: "var(--warn-dim)", border: "1px solid var(--warn-line)", borderRadius: 6, fontSize: 11, color: "var(--warn)", display: "flex", gap: 6 }}>
                  <Icon name="warn-tri" size={12}/> {selected.warning}
                </div>
              )}
            </div>
            <div style={{ flex: 1, overflow: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
              {/* Specs */}
              <div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6, textTransform: "uppercase" }}>{t("mr.section.specs")}</div>
                <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 12px", fontSize: 11, fontFamily: "var(--font-mono)" }}>
                  <span style={{ color: "var(--fg-faint)" }}>{t("mr.spec.context")}</span><span>{selected.context.toLocaleString()} {t("mr.tokens")}</span>
                  <span style={{ color: "var(--fg-faint)" }}>{t("mr.spec.license")}</span><span>{selected.license}</span>
                  <span style={{ color: "var(--fg-faint)" }}>{t("mr.spec.costIn")}</span><span>{selected.cost_1k_in != null ? `$${selected.cost_1k_in.toFixed(4)}` : <UnknownValue/>}</span>
                  <span style={{ color: "var(--fg-faint)" }}>{t("mr.spec.costOut")}</span><span>{selected.cost_1k_out != null ? `$${selected.cost_1k_out.toFixed(4)}` : <UnknownValue/>}</span>
                </div>
              </div>

              {/* Evals */}
              <div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6, textTransform: "uppercase" }}>{t("mr.section.evals")}</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {Object.entries(selected.evals).map(([k, v]) => (
                    <div key={k} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)", minWidth: 80 }}>{k}</span>
                      <div style={{ flex: 1, height: 6, background: "var(--bg-sunken)", borderRadius: 3, overflow: "hidden" }}>
                        {v != null && <div style={{ width: `${v * 100}%`, height: "100%", background: v >= 0.9 ? "var(--success)" : v >= 0.8 ? "var(--accent)" : "var(--warn)" }}/>}
                      </div>
                      <span className="mono" style={{ fontSize: 11, minWidth: 60, textAlign: "right", color: v == null ? "var(--fg-faint)" : "var(--fg)" }}>
                        {v == null ? t("mr.unknown") : `${(v * 100).toFixed(1)}%`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Usage */}
              <div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6, textTransform: "uppercase" }}>{t("mr.section.usage")}</div>
                <div style={{ padding: 12, background: "var(--bg-raised)", borderRadius: 6 }}>
                  <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 22, fontFamily: "var(--font-mono)", fontWeight: 500 }}>{selected.our_usage_30d > 0 ? `${(selected.our_usage_30d/1e6).toFixed(2)}M` : "0"}</span>
                    <span style={{ fontSize: 11, color: "var(--fg-muted)" }}>{t("mr.tokens")}</span>
                  </div>
                  <Sparkline data={selected.our_usage_30d > 0 ? Array.from({length: 30}, (_, i) => Math.max(0, selected.our_usage_30d / 30 * (0.7 + Math.sin(i * 0.6) * 0.3))) : [0,0,0,0,0]} width={340} height={40}/>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <Drawer open={!!drawer} onClose={() => setDrawer(null)} title={t("mr.register")} subtitle={t("mr.drawer.subtitle")} width={480}
        footer={<>
          <button className="btn ghost" onClick={() => setDrawer(null)}>{t("act.cancel")}</button>
          <button className="btn primary" style={{ marginLeft: "auto" }} onClick={() => setDrawer(null)}><Icon name="check" size={11}/> {t("act.register")}</button>
        </>}>
        <FormRow label={t("mr.form.family")} required><TextInput mono placeholder="e.g. claude-opus"/></FormRow>
        <FormRow label={t("mr.form.provider")} required><Select value="Anthropic" onChange={() => {}} options={[
          { value: "Anthropic", label: "Anthropic" }, { value: "OpenAI", label: "OpenAI" }, { value: "Google", label: "Google" }, { value: "Meta", label: "Meta" }, { value: "Alibaba", label: "Alibaba" }, { value: "custom", label: t("mr.form.providerOther") },
        ]}/></FormRow>
        <FormRow label={t("mr.form.modelId")} required hint={t("mr.form.modelIdHint")}><TextInput mono placeholder="claude-opus-4-1-20250805"/></FormRow>
        <FormRow label={t("mr.form.released")}><TextInput mono placeholder="2025-08-05"/></FormRow>
        <FormRow label={t("mr.form.context")}><TextInput mono placeholder="200000"/></FormRow>
        <FormRow label={t("mr.form.license")}><TextInput placeholder="proprietary · MIT · apache-2.0"/></FormRow>
        <FormRow label={t("mr.form.tags")}><TagInput tags={[]} onChange={() => {}}/></FormRow>
      </Drawer>
    </div>
  );
};

Object.assign(window, { AlertsScreen, SchedulesScreen, IntegrationsScreen, ModelRegistryScreen });
