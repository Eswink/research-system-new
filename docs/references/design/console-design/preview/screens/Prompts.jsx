/* Prompts — three-column library: list · editor · A/B compare
   Inspired by Langfuse / Humanloop conventions. */

const PromptsScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState("pr_01K5FZ8Q3");
  const [mode, setMode] = useState("editor"); // editor | ab
  const [q, setQ] = useState("");
  const selected = FIX_PROMPTS.find(p => p.id === selectedId);
  const filtered = q ? FIX_PROMPTS.filter(p => p.name.toLowerCase().includes(q.toLowerCase())) : FIX_PROMPTS;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("pr.title")} subtitle={t("pr.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("pr.search")} width={220}/>
        <ViewSwitcher value={mode} onChange={setMode} views={[
          { value: "editor", label: t("pr.viewEditor"), icon: "book" },
          { value: "ab", label: t("pr.viewAB"), icon: "fork" },
        ]}/>
        <button className="btn primary sm"><Icon name="plus" size={11}/> {t("pr.new")}</button>
      </PageToolbar>

      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 12, flex: 1, minHeight: 0 }}>
        {/* List */}
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="book" size={12} style={{ color: "var(--fg-muted)" }}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("pr.listHead")}</span>
            <span className="chip">{filtered.length}</span>
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {filtered.map(p => {
              const active = p.id === selectedId;
              return (
                <div key={p.id} onClick={() => setSelectedId(p.id)} style={{
                  padding: "10px 12px", cursor: "pointer",
                  background: active ? "var(--bg-hover)" : "transparent",
                  borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
                  borderBottom: "1px solid var(--border-subtle)",
                }}>
                  <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 4 }}>
                    <PromptStatusBadge status={p.status}/>
                    <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)", marginLeft: "auto" }}>{p.latest_version}</span>
                  </div>
                  <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", fontWeight: 500, marginBottom: 4 }}>{p.name}</div>
                  <div style={{ display: "flex", gap: 10, fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                    <span>{p.versions}v</span>
                    <span>{p.usage_7d.toLocaleString()}/7d</span>
                    {p.avg_latency_ms && <span>{p.avg_latency_ms}ms</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {mode === "editor" ? <PromptEditor prompt={selected}/> : <PromptAB prompt={selected}/>}
      </div>
    </div>
  );
};

const PromptStatusBadge = ({ status }) => {
  const map = {
    PRODUCTION: { tone: "success", icon: "check",     label: "PROD",    filled: true },
    STAGING:    { tone: "warn",    icon: "flask",     label: "STAGING", filled: true },
    DRAFT:      { tone: "neutral", icon: "circle-o",  label: "DRAFT",   dashed: true },
  };
  return <StatusBadge {...(map[status] || map.DRAFT)}/>;
};

const PromptEditor = ({ prompt }) => {
  const { t } = useI18n();
  const [tab, setTab] = useState("template");
  const versions = Array.from({ length: prompt.versions }, (_, i) => `v${prompt.versions - i}`);

  return (
    <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ padding: "10px 16px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 8 }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>
              {prompt.tags.join(" · ")}
            </div>
            <div style={{ fontSize: 15, fontWeight: 500, fontFamily: "var(--font-mono)" }}>{prompt.name}</div>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button className="btn sm"><Icon name="fork" size={10}/> {t("act.fork")}</button>
            <button className="btn sm"><Icon name="external" size={10}/> {t("act.test")}</button>
            <button className="btn primary sm"><Icon name="check" size={10}/> {t("act.publish")}</button>
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "center", fontSize: 11, color: "var(--fg-muted)" }}>
          <PromptStatusBadge status={prompt.status}/>
          <span className="mono">{prompt.latest_version}</span>
          <span>·</span>
          <span>{prompt.versions} {t("pr.versions")}</span>
          <span>·</span>
          <span>{t("pr.updated")} {new Date(prompt.updated_at).toISOString().slice(0,10)} {t("pr.by")} {prompt.updated_by}</span>
        </div>

        <div style={{ display: "flex", gap: 4, marginTop: 10 }}>
          {[["template",t("pr.tabTemplate")],["variables",t("pr.tabVariables")],["history",t("pr.tabHistory")],["metrics",t("pr.tabMetrics")]].map(([v,l]) => (
            <button key={v} onClick={() => setTab(v)} className="btn sm ghost" style={{
              background: tab === v ? "var(--bg-hover)" : "transparent",
              color: tab === v ? "var(--fg)" : "var(--fg-muted)",
              fontWeight: tab === v ? 500 : 400,
              borderColor: tab === v ? "var(--border-strong)" : "transparent",
            }}>{l}</button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: 16 }}>
        {tab === "template" && (
          <div>
            <div style={{ marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase" }}>{t("pr.tabTemplate")} · {prompt.latest_version}</div>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{prompt.template.split("\n").length} {t("pr.lines")} · {prompt.template.length} {t("pr.chars")}</div>
            </div>
            <pre style={{
              background: "var(--bg-sunken)",
              border: "1px solid var(--border)",
              borderRadius: 6,
              padding: 14,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              color: "var(--fg)",
              margin: 0,
              lineHeight: 1.7,
              whiteSpace: "pre-wrap",
            }}>
              {prompt.template.split(/(\{[^}]+\})/g).map((part, i) =>
                part.startsWith("{") ?
                  <span key={i} style={{ background: "var(--accent-dim)", color: "var(--accent)", padding: "1px 4px", borderRadius: 3 }}>{part}</span>
                  : <span key={i}>{part}</span>
              )}
            </pre>
            <div style={{ marginTop: 12, fontSize: 10, color: "var(--fg-muted)", padding: 10, background: "var(--bg-raised)", borderRadius: 6 }}>
              <span style={{ color: "var(--fg-faint)", fontFamily: "var(--font-mono)", letterSpacing: "0.08em" }}>{t("pr.variables")}</span> {prompt.variables.map(v => <span key={v} className="chip" style={{ marginLeft: 4, fontSize: 9 }}>{"{" + v + "}"}</span>)}
            </div>
          </div>
        )}
        {tab === "variables" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {prompt.variables.map(v => (
              <div key={v} style={{ padding: 10, background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 6 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <span className="mono" style={{ color: "var(--accent)", fontSize: 12 }}>{"{" + v + "}"}</span>
                  <span className="chip" style={{ fontSize: 9 }}>{t("pr.varStrReq")}</span>
                </div>
                <TextArea placeholder={t("pr.varExample").replace("{v}", "{" + v + "}")} rows={3} mono/>
              </div>
            ))}
          </div>
        )}
        {tab === "history" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {Array.from({ length: prompt.versions }, (_, i) => {
              const v = prompt.versions - i;
              const isLatest = i === 0;
              return (
                <div key={v} style={{ display: "flex", gap: 10, padding: 10, background: isLatest ? "var(--accent-dim)" : "var(--bg-raised)", border: `1px solid ${isLatest ? "var(--accent-line)" : "var(--border)"}`, borderRadius: 6 }}>
                  <span className="mono" style={{ color: isLatest ? "var(--accent)" : "var(--fg-muted)", fontSize: 12, fontWeight: 500, minWidth: 40 }}>v{v}</span>
                  <div style={{ flex: 1, fontSize: 11, color: "var(--fg-muted)" }}>
                    <div style={{ marginBottom: 3, color: "var(--fg)" }}>
                      {i === 0 ? "Tightened hallucination detection prompt · added confidence field" :
                       i === 1 ? "Switched from `dose` to `dose_mg` for canonical output" :
                       i === 2 ? "Added evidence_span requirement" :
                       "Prompt version " + v}
                    </div>
                    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                      {new Date(new Date(prompt.updated_at).getTime() - i * 86400000 * 3).toISOString().slice(0,10)} · {prompt.updated_by}
                    </div>
                  </div>
                  {isLatest && <span className="chip" style={{ color: "var(--accent)", borderColor: "var(--accent-line)", fontSize: 9 }}>{t("pr.verLatest")}</span>}
                  <button className="btn sm ghost"><Icon name="external" size={10}/></button>
                </div>
              );
            })}
          </div>
        )}
        {tab === "metrics" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
            <MetricCard label={t("pr.metric7d")} value={prompt.usage_7d.toLocaleString()} sub={<span>{t("pr.metric7dSub")} <span className="mono" style={{color: "var(--success)"}}>+12.4%</span> WoW</span>} spark={[3,4,3,5,7,6,8]}/>
            <MetricCard label={t("pr.metricLat")} value={prompt.avg_latency_ms ? `${prompt.avg_latency_ms}ms` : "—"} sub={<span>{t("pr.metricLatP")} {prompt.avg_latency_ms ? Math.round(prompt.avg_latency_ms * 1.8) : "—"}ms</span>} spark={[8,7,9,8,7,8,7]} sparkColor="var(--warn)"/>
            <MetricCard label={t("pr.metricErr")} value="0.42%" sub={<span>{t("pr.metricErrSub")} <span className="mono" style={{color: "var(--danger)"}}>52 {t("pr.metricErrors")}</span></span>} bar={0.042} barColor="var(--danger)"/>
          </div>
        )}
      </div>
    </div>
  );
};

const PromptAB = ({ prompt }) => { const { t } = useI18n();
  const ab = FIX_PROMPT_AB;
  return (
    <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ padding: "10px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
        <Icon name="fork" size={12} style={{ color: "var(--fg-muted)" }}/>
        <span style={{ fontSize: 12, fontWeight: 500 }}>{t("pr.abTitle")} · {prompt.name}</span>
        <span className="chip">n={ab.n_samples}</span>
        {ab.significant && <span className="chip" style={{ color: "var(--success)", borderColor: "var(--success-line)" }}>{t("pr.abSig")}{ab.p_value}</span>}
        <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{t("pr.abWinner")} <span style={{ color: "var(--accent)", fontWeight: 500 }}>{ab.winner.toUpperCase()}</span></span>
      </div>
      <div style={{ flex: 1, overflow: "auto", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0 }}>
        {[["a", ab.a], ["b", ab.b]].map(([k, v]) => (
          <div key={k} style={{ padding: 16, borderRight: k === "a" ? "1px solid var(--border)" : "none", display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                width: 20, height: 20, borderRadius: 4,
                background: k === ab.winner ? "var(--accent)" : "var(--bg-raised)",
                color: k === ab.winner ? "#fff" : "var(--fg-muted)",
                fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 600,
              }}>{k.toUpperCase()}</span>
              <span className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{v.version}</span>
              {k === ab.winner && <span className="chip" style={{ color: "var(--success)", borderColor: "var(--success-line)" }}><Icon name="check" size={9}/> {t("pr.abWinnerLabel")}</span>}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              <MetricCard label={t("pr.abAccuracy")} value={`${(v.accuracy*100).toFixed(1)}%`} bar={v.accuracy} barColor={v.accuracy > 0.87 ? "var(--success)" : "var(--warn)"}/>
              <MetricCard label={t("pr.abLatency")} value={`${v.latency_ms}ms`} bar={v.latency_ms / 2000} barColor="var(--warn)"/>
              <MetricCard label={t("pr.abCost")} value={`$${v.cost_per_1k.toFixed(2)}`} bar={v.cost_per_1k / 1} barColor="var(--accent)"/>
            </div>
            <div>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6 }}>{t("pr.abSample")}</div>
              <pre style={{ background: "var(--bg-sunken)", border: "1px solid var(--border)", padding: 10, borderRadius: 6, fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg)", lineHeight: 1.6, whiteSpace: "pre-wrap", margin: 0 }}>
                {v.sample_output}
              </pre>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

Object.assign(window, { PromptsScreen });
