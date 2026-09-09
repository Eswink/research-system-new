/* Compare Screen — side-by-side diff of runs / experiments.
   Uses existing FIX_RUNS_HISTORY + FIX_RUN_DIFF fixtures.
   Interactions: pick 2–4 runs from a picker rail, view diff of
   metrics + manifest + claims + cost. Toggle "hide unchanged". */

const CompareScreen = () => {
  const { t } = useI18n();
  const allRuns = FIX_RUNS_HISTORY;
  const [selected, setSelected] = useState(() => [allRuns[0].id, allRuns[1].id]);
  const [hideUnchanged, setHideUnchanged] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);

  const selectedRuns = selected.map(id => allRuns.find(r => r.id === id)).filter(Boolean);
  const base = selectedRuns[0];

  const toggleRun = (id) => {
    setSelected(prev => {
      if (prev.includes(id)) return prev.length > 1 ? prev.filter(x => x !== id) : prev;
      if (prev.length >= 4) return [...prev.slice(1), id];
      return [...prev, id];
    });
  };

  // Build metric matrix from FIX_RUN_DIFF (real numbers) — extend synthetically for extra runs
  const metricKeys = FIX_RUN_DIFF.metrics.map(m => m.key);
  const metricValues = (runIdx, key) => {
    const m = FIX_RUN_DIFF.metrics.find(x => x.key === key);
    if (!m) return null;
    // Runs 0 uses .a, run 1 uses .b, runs 2–3 fabricate small deltas.
    if (runIdx === 0) return m.a;
    if (runIdx === 1) return m.b;
    const jitter = 1 + (runIdx * 0.07 - 0.1);
    return typeof m.a === "number" ? +(m.a * jitter).toFixed(m.unit === "ms" || m.unit === "count" ? 0 : 3) : null;
  };
  const bestFor = (key) => {
    const m = FIX_RUN_DIFF.metrics.find(x => x.key === key);
    if (!m) return null;
    const vals = selectedRuns.map((_, i) => metricValues(i, key));
    const goodDir = m.better; // if a<b better=true means a is better (i.e. lower=better for rates/cost/latency/failed)
    // We infer: for the fixture, negative delta = better means lower is better.
    const lowerIsBetter = (m.delta < 0) === m.better;
    return lowerIsBetter ? Math.min(...vals) : Math.max(...vals);
  };

  const manifestFields = FIX_RUN_DIFF.manifest_diff;
  const visibleManifest = hideUnchanged
    ? manifestFields.filter(f => f.note !== "unchanged")
    : manifestFields;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("cmp.title")} subtitle={t("cmp.subtitle")}>
        <label style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11, color: "var(--fg-muted)", cursor: "pointer" }}>
          <input type="checkbox" checked={hideUnchanged} onChange={e => setHideUnchanged(e.target.checked)}/>
          {t("cmp.hideUnchanged")}
        </label>
        <button className="btn sm" onClick={() => setPickerOpen(true)}>
          <Icon name="plus" size={11}/> {t("cmp.pickRuns")} ({selectedRuns.length}/4)
        </button>
        <button className="btn primary sm"><Icon name="external" size={11}/> {t("cmp.exportDiff")}</button>
      </PageToolbar>

      {/* Selected chips */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        {selectedRuns.map((r, i) => (
          <div key={r.id} style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            padding: "4px 10px", height: 26,
            background: "var(--bg-raised)", border: "1px solid var(--border)",
            borderLeft: `2px solid ${["var(--accent)", "var(--warn)", "var(--success)", "var(--unknown)"][i]}`,
            borderRadius: 4, fontSize: 11,
          }}>
            <span className="mono" style={{ color: "var(--fg-faint)", fontSize: 10 }}>{String.fromCharCode(65 + i)}</span>
            <span style={{ fontWeight: 500 }}>{r.label}</span>
            <RunStateBadge state={r.state}/>
            <button className="btn sm ghost" onClick={() => toggleRun(r.id)} style={{ height: 18, padding: "0 4px" }}>
              <Icon name="x" size={9}/>
            </button>
          </div>
        ))}
      </div>

      {/* Grid: metrics diff (top) · manifest diff (bottom-left) · summary cards (bottom-right) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12, flex: 1, minHeight: 0, overflow: "auto" }}>
        {/* Metrics matrix */}
        <div className="panel" style={{ overflow: "hidden" }}>
          <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="graph" size={12}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("cmp.metrics")}</span>
            <span className="chip" style={{ marginLeft: "auto" }}>{metricKeys.length} {t("cmp.rows")}</span>
          </div>
          <div style={{ overflow: "auto" }}>
            {/* Header */}
            <div className="row head" style={{ gridTemplateColumns: `1.4fr repeat(${selectedRuns.length}, 1fr) 80px` }}>
              <span>{t("cmp.metric")}</span>
              {selectedRuns.map((r, i) => (
                <span key={r.id}>{String.fromCharCode(65 + i)} · {r.label.split(" · ").pop()}</span>
              ))}
              <span>Δ (A→B)</span>
            </div>
            {metricKeys.map(key => {
              const meta = FIX_RUN_DIFF.metrics.find(m => m.key === key);
              const values = selectedRuns.map((_, i) => metricValues(i, key));
              const best = bestFor(key);
              const fmt = (v) => {
                if (v == null) return <UnknownValue/>;
                if (meta.unit === "$") return `$${v.toFixed(2)}`;
                if (meta.unit === "ms") return `${Math.round(v)} ms`;
                if (meta.unit === "rate") return `${(v * 100).toFixed(1)}%`;
                return v;
              };
              const delta = values.length >= 2 && values[0] != null && values[1] != null ? values[1] - values[0] : null;
              return (
                <div key={key} className="row" style={{ gridTemplateColumns: `1.4fr repeat(${selectedRuns.length}, 1fr) 80px` }}>
                  <div className="mono" style={{ fontSize: 11 }}>{key}</div>
                  {values.map((v, i) => {
                    const isBest = v === best && values.filter(x => x === best).length === 1;
                    return (
                      <div key={i} className="mono" style={{ fontSize: 11, display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ color: isBest ? "var(--success)" : "var(--fg)", fontWeight: isBest ? 500 : 400 }}>{fmt(v)}</span>
                        {isBest && <Icon name="check" size={9} style={{ color: "var(--success)" }}/>}
                      </div>
                    );
                  })}
                  <div>
                    {delta != null && (
                      <TrendBadge delta={delta * (meta.unit === "rate" ? 100 : 1)} inverted={meta.better === (delta < 0)}
                        format={(v) => meta.unit === "$" ? `${v > 0 ? "+" : "-"}$${v.toFixed(2)}` : meta.unit === "ms" ? `${v > 0 ? "+" : ""}${Math.round(v)}` : meta.unit === "rate" ? `${v > 0 ? "+" : ""}${v.toFixed(1)}pp` : v.toFixed(1)}/>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Manifest + summary */}
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 12 }}>
          <div className="panel" style={{ overflow: "hidden" }}>
            <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
              <Icon name="book" size={12}/>
              <span style={{ fontSize: 12, fontWeight: 500 }}>{t("cmp.manifest")}</span>
              <span className="chip" style={{ marginLeft: "auto" }}>
                {manifestFields.filter(f => f.note !== "unchanged").length} {t("cmp.changed")} / {manifestFields.length} {t("cmp.total")}
              </span>
            </div>
            <div style={{ overflow: "auto" }}>
              <div className="row head" style={{ gridTemplateColumns: "1.2fr 1fr 1fr 100px" }}>
                <span>{t("cmp.field")}</span><span>A</span><span>B</span><span>{t("cmp.note")}</span>
              </div>
              {visibleManifest.map(f => (
                <div key={f.field} className="row" style={{ gridTemplateColumns: "1.2fr 1fr 1fr 100px" }}>
                  <div className="mono" style={{ fontSize: 11 }}>{f.field}</div>
                  <div className="mono" style={{ fontSize: 11, color: f.a !== f.b ? "var(--fg)" : "var(--fg-faint)" }}>{String(f.a).slice(0, 30)}</div>
                  <div className="mono" style={{ fontSize: 11, color: f.a !== f.b ? "var(--accent)" : "var(--fg-faint)" }}>{String(f.b).slice(0, 30)}</div>
                  <div style={{ fontSize: 10, color: f.note === "unchanged" ? "var(--fg-faint)" : "var(--warn)" }}>{f.note}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel" style={{ padding: 14, display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase" }}>{t("cmp.verdict")}</div>
            <div style={{ fontSize: 13, lineHeight: 1.5 }}>
              {t("cmp.verdictLine1")}: <span style={{ color: "var(--success)", fontWeight: 500 }}>A ({base?.label})</span> {t("cmp.verdictLine2")}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 8 }}>
              {selectedRuns.map((r, i) => (
                <div key={r.id} style={{ padding: 10, background: "var(--bg-sunken)", borderRadius: 6, borderLeft: `2px solid ${["var(--accent)", "var(--warn)", "var(--success)", "var(--unknown)"][i]}` }}>
                  <div style={{ fontSize: 10, color: "var(--fg-faint)", fontFamily: "var(--font-mono)" }}>{String.fromCharCode(65 + i)}</div>
                  <div style={{ fontSize: 11, fontWeight: 500, marginTop: 2 }}>{r.label}</div>
                  <div style={{ fontSize: 10, color: "var(--fg-muted)", marginTop: 4, fontFamily: "var(--font-mono)" }}>
                    ${(r.spent_minor / 1e6).toFixed(2)}M · {r.claims_new} claims · {r.tasks_done}/{r.tasks_total}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: "auto", display: "flex", gap: 6 }}>
              <button className="btn sm" style={{ flex: 1 }}><Icon name="fork" size={10}/> {t("cmp.forkFromA")}</button>
              <button className="btn sm primary" style={{ flex: 1 }}><Icon name="external" size={10}/> {t("cmp.openReport")}</button>
            </div>
          </div>
        </div>
      </div>

      {/* Picker drawer */}
      <Drawer open={pickerOpen} onClose={() => setPickerOpen(false)} title={t("cmp.pickerTitle")} subtitle={t("cmp.pickerSub")} width={520}>
        <div style={{ fontSize: 11, color: "var(--fg-muted)", marginBottom: 10 }}>{t("cmp.pickerHint")}</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {allRuns.map(r => {
            const on = selected.includes(r.id);
            const idx = selected.indexOf(r.id);
            return (
              <label key={r.id} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "8px 10px", borderRadius: 6, cursor: "pointer",
                background: on ? "var(--accent-dim)" : "var(--bg-raised)",
                border: `1px solid ${on ? "var(--accent-line)" : "var(--border)"}`,
              }}>
                <input type="checkbox" checked={on} onChange={() => toggleRun(r.id)}/>
                {on && <span className="mono" style={{ fontSize: 10, color: "var(--accent)", minWidth: 14 }}>{String.fromCharCode(65 + idx)}</span>}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500 }}>{r.label}</div>
                  <div className="mono" style={{ fontSize: 10, color: "var(--fg-faint)" }}>{r.id.slice(0, 20)} · {new Date(r.started_at).toISOString().slice(0, 10)}</div>
                </div>
                <RunStateBadge state={r.state}/>
              </label>
            );
          })}
        </div>
      </Drawer>
    </div>
  );
};

Object.assign(window, { CompareScreen });
