/* Data Health — schema drift, label distribution, PII scan, staleness.
   Sits alongside Datasets but focuses on quality signals. */

const DH_METRICS = [
  { id: "d_medqa_zh_v4", dataset: "medqa · zh · v4", rows: 42800, drift: 0.03, freshness_d: 2, pii_hits: 0, label_skew: 0.12, schema_ok: true },
  { id: "d_medqa_es_v4", dataset: "medqa · es · v4", rows: 38200, drift: 0.14, freshness_d: 3, pii_hits: 2, label_skew: 0.28, schema_ok: true },
  { id: "d_medqa_ar_v4", dataset: "medqa · ar · v4", rows: 12400, drift: 0.31, freshness_d: 12, pii_hits: 0, label_skew: 0.48, schema_ok: false },
  { id: "d_adv_ret_v7", dataset: "adversarial-retrieval · v7", rows: 8400, drift: 0.07, freshness_d: 1, pii_hits: 0, label_skew: 0.09, schema_ok: true },
  { id: "d_steering_v3", dataset: "steering-eval · v3", rows: 2100, drift: 0.02, freshness_d: 24, pii_hits: 0, label_skew: 0.15, schema_ok: true },
  { id: "d_prompt_inj_v2", dataset: "prompt-injection · v2", rows: 5600, drift: 0.09, freshness_d: 6, pii_hits: 4, label_skew: 0.19, schema_ok: true },
];

const DataHealthScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState(DH_METRICS[2].id); // arabic (has issues)

  const selected = DH_METRICS.find(d => d.id === selectedId);
  const health = (m) => {
    let issues = 0;
    if (m.drift > 0.15) issues++;
    if (m.freshness_d > 10) issues++;
    if (m.pii_hits > 0) issues++;
    if (m.label_skew > 0.35) issues++;
    if (!m.schema_ok) issues++;
    if (issues === 0) return { tone: "success", label: "HEALTHY", icon: "check" };
    if (issues <= 2) return { tone: "warn", label: "DEGRADED", icon: "warn-tri" };
    return { tone: "danger", label: "UNHEALTHY", icon: "x" };
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("dh.title")} subtitle={t("dh.subtitle")}>
        <button className="btn sm"><Icon name="spin" size={11}/> {t("dh.rescanAll")}</button>
        <button className="btn primary sm"><Icon name="external" size={11}/> {t("dh.exportReport")}</button>
      </PageToolbar>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <MetricCard label={t("dh.mHealthy")} value={DH_METRICS.filter(d => health(d).label === "HEALTHY").length} sub={<span>/ {DH_METRICS.length} {t("dh.datasets")}</span>}/>
        <MetricCard label={t("dh.mDrifting")} value={DH_METRICS.filter(d => d.drift > 0.15).length} sub={<span>{t("dh.mDriftingSub")}</span>} bar={DH_METRICS.filter(d => d.drift > 0.15).length / DH_METRICS.length} barColor="var(--warn)"/>
        <MetricCard label={t("dh.mPII")} value={DH_METRICS.reduce((a, d) => a + d.pii_hits, 0)} sub={<span>{t("dh.mPIISub")}</span>} barColor="var(--danger)"/>
        <MetricCard label={t("dh.mStale")} value={DH_METRICS.filter(d => d.freshness_d > 10).length} sub={<span>{t("dh.mStaleSub")}</span>}/>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 12, flex: 1, minHeight: 0 }}>
        <div className="panel" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", fontSize: 12, fontWeight: 500 }}>{t("dh.overview")}</div>
          <div style={{ overflow: "auto" }}>
            <div className="row head" style={{ gridTemplateColumns: "minmax(180px, 1.6fr) 70px 60px 60px 50px 60px 100px" }}>
              <span>{t("dh.dataset")}</span><span>{t("dh.rows")}</span><span>{t("dh.drift")}</span><span>{t("dh.fresh")}</span><span>{t("dh.pii")}</span><span>{t("dh.skew")}</span><span>{t("dh.health")}</span>
            </div>
            {DH_METRICS.map(d => {
              const h = health(d);
              const active = d.id === selectedId;
              return (
                <div key={d.id} onClick={() => setSelectedId(d.id)} className="row" style={{
                  gridTemplateColumns: "minmax(180px, 1.6fr) 70px 60px 60px 50px 60px 100px",
                  cursor: "pointer",
                  background: active ? "var(--bg-hover)" : undefined,
                  borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
                }}>
                  <div className="row-cell-wrap" style={{ minWidth: 0, overflow: "hidden" }}>
                    <div style={{ fontSize: 12, fontWeight: 500, fontFamily: "var(--font-mono)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{d.dataset}</div>
                    {!d.schema_ok && <div style={{ fontSize: 10, color: "var(--danger)", marginTop: 2, display: "flex", alignItems: "center", gap: 4, whiteSpace: "nowrap" }}><Icon name="warn-tri" size={9}/> {t("dh.schemaBroken")}</div>}
                  </div>
                  <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>{d.rows.toLocaleString()}</span>
                  <span className="mono" style={{ fontSize: 11, color: d.drift > 0.15 ? "var(--warn)" : "var(--fg)" }}>{(d.drift * 100).toFixed(1)}%</span>
                  <span className="mono" style={{ fontSize: 11, color: d.freshness_d > 10 ? "var(--warn)" : "var(--fg-muted)" }}>{d.freshness_d}d</span>
                  <span className="mono" style={{ fontSize: 11, color: d.pii_hits > 0 ? "var(--danger)" : "var(--fg-muted)" }}>{d.pii_hits}</span>
                  <span className="mono" style={{ fontSize: 11, color: d.label_skew > 0.35 ? "var(--warn)" : "var(--fg-muted)" }}>{d.label_skew.toFixed(2)}</span>
                  <StatusBadge tone={h.tone} icon={h.icon} label={h.label} size="sm" filled={h.tone !== "neutral"}/>
                </div>
              );
            })}
          </div>
        </div>

        {selected && (
          <div className="panel" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)" }}>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{t("dh.detail")}</div>
              <div style={{ fontSize: 14, fontWeight: 500, fontFamily: "var(--font-mono)" }}>{selected.dataset}</div>
            </div>
            <div style={{ flex: 1, overflow: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 14 }}>
              {/* Drift chart */}
              <div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>{t("dh.driftTrend")} · 30d</div>
                <div style={{ padding: 12, background: "var(--bg-raised)", borderRadius: 6 }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginBottom: 6 }}>
                    <span style={{ fontSize: 22, fontFamily: "var(--font-mono)", fontWeight: 500, color: selected.drift > 0.15 ? "var(--warn)" : "var(--fg)" }}>{(selected.drift * 100).toFixed(1)}%</span>
                    <span style={{ fontSize: 11, color: "var(--fg-muted)" }}>PSI</span>
                    <span className="mono" style={{ marginLeft: "auto", fontSize: 10, color: "var(--fg-faint)" }}>threshold: 15%</span>
                  </div>
                  <Sparkline data={Array.from({ length: 30 }, (_, i) => Math.max(0.01, selected.drift * (0.6 + Math.sin(i * 0.5) * 0.4 + i / 60)))} width={340} height={44} stroke={selected.drift > 0.15 ? "var(--warn)" : "var(--accent)"} fill={selected.drift > 0.15 ? "var(--warn-dim)" : "var(--accent-dim)"}/>
                </div>
              </div>

              {/* Label distribution */}
              <div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>{t("dh.labelDist")}</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {[
                    { name: "class_a", pct: 0.42 },
                    { name: "class_b", pct: 0.31 },
                    { name: "class_c", pct: 0.18 },
                    { name: "class_d", pct: 0.09 },
                  ].map(c => (
                    <div key={c.name} style={{ display: "grid", gridTemplateColumns: "80px 1fr 50px", gap: 8, alignItems: "center" }}>
                      <span className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>{c.name}</span>
                      <div style={{ height: 8, background: "var(--bg-sunken)", borderRadius: 2, overflow: "hidden" }}>
                        <div style={{ width: `${c.pct * 100}%`, height: "100%", background: "var(--accent)" }}/>
                      </div>
                      <span className="mono" style={{ fontSize: 10, textAlign: "right", color: "var(--fg-muted)" }}>{(c.pct * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* PII scan */}
              {selected.pii_hits > 0 && (
                <div>
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>{t("dh.piiScan")}</div>
                  <div style={{ padding: 12, background: "var(--danger-dim)", border: "1px solid var(--danger-line)", borderRadius: 6, fontSize: 11, color: "var(--danger)", display: "flex", gap: 8 }}>
                    <Icon name="warn-tri" size={13}/>
                    <div>
                      <div style={{ fontWeight: 500, marginBottom: 4 }}>{selected.pii_hits} {t("dh.piiFound")}</div>
                      <div style={{ color: "var(--fg-muted)", fontSize: 10 }}>{t("dh.piiHint")}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Schema */}
              <div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>{t("dh.schema")}</div>
                {selected.schema_ok ? (
                  <StatusBadge tone="success" icon="check" label={t("dh.schemaOk")} filled/>
                ) : (
                  <div style={{ padding: 12, background: "var(--warn-dim)", border: "1px solid var(--warn-line)", borderRadius: 6, fontSize: 11 }}>
                    <div style={{ color: "var(--warn)", fontWeight: 500, marginBottom: 6 }}>{t("dh.schemaMissing")}</div>
                    <div className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>+ column "context_length" (int)</div>
                    <div className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>- column "region" (str)</div>
                  </div>
                )}
              </div>
            </div>

            <div style={{ padding: 12, borderTop: "1px solid var(--border)", display: "flex", gap: 6 }}>
              <button className="btn sm"><Icon name="spin" size={11}/> {t("dh.rescan")}</button>
              <button className="btn sm ghost" style={{ marginLeft: "auto" }}><Icon name="external" size={11}/> {t("dh.openDataset")}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

Object.assign(window, { DataHealthScreen });
