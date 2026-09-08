/* Runs History — list + two-run diff view. */

const RunsHistoryScreen = () => {
  const { t } = useI18n();
  const [view, setView] = useState("list"); // list | diff
  const [selectedIds, setSelectedIds] = useState(["run_01K5FZ8G3X2QN4M", "run_01K5FZ8G2X1QN3L"]);
  const [q, setQ] = useState("");
  const filtered = q ? FIX_RUNS_HISTORY.filter(r => r.label.toLowerCase().includes(q.toLowerCase())) : FIX_RUNS_HISTORY;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("rh.title")} subtitle={t("rh.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("rh.search")} width={220}/>
        <ViewSwitcher value={view} onChange={setView} views={[
          { value: "list", label: t("rh.viewList"), icon: "menu" },
          { value: "diff", label: t("rh.viewDiff"), icon: "fork" },
        ]}/>
        {view === "list" && <button className="btn sm" disabled={selectedIds.length !== 2} onClick={() => setView("diff")}>
          <Icon name="fork" size={11}/> {t("rh.compare")} {selectedIds.length}/2
        </button>}
      </PageToolbar>

      {view === "list" && (
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden", flex: 1, minHeight: 0 }}>
          <div className="row head" style={{ gridTemplateColumns: "24px 1.4fr 120px 90px 100px 100px 100px 130px" }}>
            <span></span>
            <span>{t("rh.colRun")}</span>
            <span>{t("lbl.state")}</span>
            <span>{t("lbl.duration")}</span>
            <span>{t("lbl.tasks")}</span>
            <span>{t("lbl.spent")}</span>
            <span>{t("lbl.autonomy")}</span>
            <span>{t("lbl.started")}</span>
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {filtered.map(r => {
              const on = selectedIds.includes(r.id);
              return (
                <div key={r.id} className="row" style={{ gridTemplateColumns: "24px 1.4fr 120px 90px 100px 100px 100px 130px", cursor: "pointer", background: on ? "var(--accent-dim)" : undefined, borderLeft: `2px solid ${on ? "var(--accent)" : "transparent"}` }}>
                  <span>
                    <input type="checkbox" checked={on} onChange={() => {
                      setSelectedIds(prev => on ? prev.filter(id => id !== r.id) : (prev.length >= 2 ? [prev[1], r.id] : [...prev, r.id]));
                    }} style={{ accentColor: "var(--accent)" }}/>
                  </span>
                  <div className="row-cell-wrap" style={{ minWidth: 0, overflow: "hidden" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2, overflow: "hidden", whiteSpace: "nowrap" }}>
                      <span style={{ fontSize: 12, fontWeight: 500, fontFamily: "var(--font-mono)", overflow: "hidden", textOverflow: "ellipsis" }}>{r.label}</span>
                      {r.live && <LiveIndicator state="live"/>}
                    </div>
                    <DigestText value={r.id} length={16} prefix={false}/>
                  </div>
                  <span><RunStateBadge state={r.state}/></span>
                  <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>{fmtDuration(r.duration_s)}</span>
                  <span style={{ fontSize: 11, fontFamily: "var(--font-mono)" }}>
                    <span style={{ color: "var(--success)" }}>{r.tasks_done}</span>/<span>{r.tasks_total}</span>
                    {r.tasks_failed > 0 && <span style={{ color: "var(--danger)" }}> · {r.tasks_failed} {t("rh.fail")}</span>}
                  </span>
                  <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>${(r.spent_minor/100000).toFixed(2)}</span>
                  <span className="mono" style={{ fontSize: 9, color: r.autonomy === "GUARDED_AUTONOMOUS" ? "var(--warn)" : "var(--fg-muted)" }}>{r.autonomy.replace("_", " ")}</span>
                  <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>{new Date(r.started_at).toISOString().replace("T", " ").slice(0,16)}</span>
                </div>
              );
            })}
          </div>
          <div style={{ padding: "8px 14px", borderTop: "1px solid var(--border)", background: "var(--bg-raised)", fontSize: 11, color: "var(--fg-muted)", display: "flex", justifyContent: "space-between" }}>
            <span>{selectedIds.length}/2 {t("rh.selected")}</span>
            <span>{filtered.length} {t("rh.runsN")} · {filtered.filter(r => r.state === "SUCCEEDED").length} {t("rh.succeeded")} · {filtered.filter(r => r.state === "FAILED").length} {t("rh.failed")}</span>
          </div>
        </div>
      )}

      {view === "diff" && <RunDiffView aId={selectedIds[0]} bId={selectedIds[1]}/>}
    </div>
  );
};

const fmtDuration = (s) => {
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.round(s/60)}m`;
  return `${Math.floor(s/3600)}h ${Math.round((s%3600)/60)}m`;
};

const RunDiffView = ({ aId, bId }) => { const { t } = useI18n();
  const a = FIX_RUNS_HISTORY.find(r => r.id === aId);
  const b = FIX_RUNS_HISTORY.find(r => r.id === bId);
  const diff = FIX_RUN_DIFF;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0, overflow: "auto" }}>
      {/* Header */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 40px 1fr", gap: 0 }}>
        {[a, b].map((r, i) => (
          <React.Fragment key={r.id}>
            {i === 1 && (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                <div style={{ padding: 6, background: "var(--bg-raised)", borderRadius: "50%", border: "1px solid var(--border)" }}>
                  <Icon name="chevron-r" size={14} style={{ color: "var(--fg-faint)" }}/>
                </div>
              </div>
            )}
            <div className="panel" style={{ padding: 14 }}>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{i === 0 ? t("rh.runA") : t("rh.runB")}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <span style={{ fontSize: 14, fontWeight: 500, fontFamily: "var(--font-mono)" }}>{r.label}</span>
                <RunStateBadge state={r.state}/>
              </div>
              <DigestText value={r.id} length={20} prefix={false}/>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, marginTop: 10, fontSize: 11 }}>
                <div>
                  <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{t("rh.duration")}</div>
                  <div style={{ fontFamily: "var(--font-mono)" }}>{fmtDuration(r.duration_s)}</div>
                </div>
                <div>
                  <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{t("rh.tasks")}</div>
                  <div style={{ fontFamily: "var(--font-mono)" }}>{r.tasks_done}/{r.tasks_total}</div>
                </div>
                <div>
                  <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{t("rh.spent")}</div>
                  <div style={{ fontFamily: "var(--font-mono)" }}>${(r.spent_minor/100000).toFixed(2)}</div>
                </div>
              </div>
            </div>
          </React.Fragment>
        ))}
      </div>

      {/* Metric diff */}
      <div className="panel" style={{ overflow: "hidden" }}>
        <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="graph" size={12}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("rh.metricDiff")}</span>
          <span className="chip">{diff.metrics.length} {t("rh.metrics")}</span>
          <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
            {diff.metrics.filter(m => m.better).length} {t("rh.improved")} · {diff.metrics.filter(m => !m.better).length} {t("rh.regressed")}
          </span>
        </div>
        <div>
          {diff.metrics.map(m => (
            <div key={m.key} style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr 1fr 1fr", padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", alignItems: "center", gap: 12 }}>
              <span className="mono" style={{ fontSize: 12 }}>{m.key}</span>
              <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontSize: 12 }}>
                {fmtVal(m.a, m.unit)}
              </span>
              <span style={{ textAlign: "center", color: "var(--fg-faint)" }}>→</span>
              <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontSize: 12 }}>
                {fmtVal(m.b, m.unit)}
              </span>
              <span style={{ textAlign: "right" }}>
                <TrendBadge delta={m.delta} inverted={!m.better} format={v => `${m.delta > 0 ? "+" : "−"}${fmtVal(v, m.unit).replace("$", "").replace("ms", "").replace("%", "").trim()}`}/>
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Manifest diff */}
      <div className="panel" style={{ overflow: "hidden" }}>
        <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="diamond" size={12}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("rh.manifestDiff")}</span>
          <span className="chip">{diff.manifest_diff.filter(m => m.a !== m.b).length} {t("rh.changed")}</span>
        </div>
        <div>
          {diff.manifest_diff.map((m, i) => {
            const changed = String(m.a) !== String(m.b);
            return (
              <div key={i} style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 40px 1fr 1.4fr", padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)", alignItems: "center", gap: 12 }}>
                <span className="mono" style={{ fontSize: 11 }}>{m.field}</span>
                <span className="mono" style={{ fontSize: 11, color: changed ? "var(--danger)" : "var(--fg-muted)", textAlign: "right", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{String(m.a)}</span>
                <span style={{ textAlign: "center", color: "var(--fg-faint)" }}>{changed ? "→" : "="}</span>
                <span className="mono" style={{ fontSize: 11, color: changed ? "var(--success)" : "var(--fg-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{String(m.b)}</span>
                <span style={{ fontSize: 10, color: "var(--fg-faint)" }}>{m.note}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const fmtVal = (v, unit) => {
  if (unit === "$") return `$${v.toFixed(2)}`;
  if (unit === "ms") return `${v}ms`;
  if (unit === "rate") return `${(v * 100).toFixed(1)}%`;
  return String(v);
};

Object.assign(window, { RunsHistoryScreen });
