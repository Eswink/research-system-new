/* Cost Analytics — multi-dimensional cost pivot with Sankey */

const CostAnalyticsScreen = () => {
  const { t } = useI18n();
  const [pivot, setPivot] = useState("model"); // model | project | task
  const [range, setRange] = useState("30d");

  // Compute totals from COST_DAILY
  const totals = useMemo(() => {
    const t = {};
    FIX_COST_DAILY.forEach(row => {
      Object.entries(row).forEach(([k, v]) => {
        if (k === "date") return;
        t[k] = (t[k] || 0) + v;
      });
    });
    return t;
  }, []);
  const grandTotal = Object.values(totals).reduce((a, b) => a + b, 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0, overflow: "auto" }}>
      <PageToolbar title={t("ca.title")} subtitle={t("ca.subtitle")}>
        <ViewSwitcher value={range} onChange={setRange} views={[
          { value: "7d", label: "7d" },
          { value: "30d", label: "30d" },
          { value: "90d", label: "90d" },
        ]}/>
        <button className="btn sm"><Icon name="external" size={11}/> {t("act.exportCsv")}</button>
      </PageToolbar>

      {/* Top metric strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <MetricCard label={t("ca.totalSpend")} value={`$${(grandTotal/100).toFixed(2)}`} sub={<span>{t("ca.totalSpendSub")}</span>} trend={12.4}/>
        <MetricCard label={t("ca.avgDaily")} value={`$${(grandTotal/30/100).toFixed(2)}`} sub={<span>{t("ca.avgDailyProj")} <span className="mono">${(grandTotal/100*1.03).toFixed(0)}</span></span>} spark={FIX_COST_DAILY.map(d => Object.values(d).slice(1).reduce((a,b) => a+b, 0))}/>
        <MetricCard label={t("ca.unknownCost")} value={<span style={{ color: "var(--unknown)" }}>{FIX_BUDGET.unknown_cost_entries}</span>} sub={<span style={{ color: "var(--unknown)" }}>{t("ca.unknownCostSub")} <span className="mono">cost_status=UNKNOWN</span></span>} unknownWarn/>
        <MetricCard label={t("ca.topModel")} value="Opus 4.1" sub={<span>$1,104 · <span className="mono" style={{ color: "var(--warn)" }}>35.4%</span> {t("ca.topModelSub")}</span>}/>
      </div>

      {/* Sankey */}
      <div className="panel" style={{ padding: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <Icon name="graph" size={12}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ca.flow")}</span>
          <span className="chip">sankey</span>
          <div style={{ marginLeft: "auto", display: "flex", gap: 8, fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
            <span><div style={{ display: "inline-block", width: 8, height: 8, background: "var(--fg-muted)", borderRadius: 2, marginRight: 4, verticalAlign: "middle" }}/>{t("ca.legendProject")}</span>
            <span><div style={{ display: "inline-block", width: 8, height: 8, background: "var(--accent)", borderRadius: 2, marginRight: 4, verticalAlign: "middle" }}/>{t("ca.legendModel")}</span>
            <span><div style={{ display: "inline-block", width: 8, height: 8, background: "var(--success)", borderRadius: 2, marginRight: 4, verticalAlign: "middle" }}/>{t("ca.legendTask")}</span>
          </div>
        </div>
        <div style={{ background: "var(--bg-sunken)", borderRadius: 6, padding: 12, overflow: "auto" }}>
          <Sankey nodes={FIX_COST_SANKEY.nodes} flows={FIX_COST_SANKEY.flows} width={880} height={360}/>
        </div>
      </div>

      {/* Line chart + bar breakdown */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 12 }}>
        <div className="panel" style={{ padding: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <Icon name="graph" size={12}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ca.daily")}</span>
            <span className="chip">{t("ca.last30d")}</span>
          </div>
          <LineSeries
            data={["gpt-4o", "sonnet-4", "opus-4.1", "gemini-2.5", "qwen3-235b"].map(m => ({
              label: m, values: FIX_COST_DAILY.map(d => Math.round(d[m] / 100)),
            }))}
            xLabels={FIX_COST_DAILY.map((d, i) => i % 5 === 0 ? d.date.slice(5) : "").filter((x,i) => i % 5 === 0)}
            width={720}
            height={220}
            yFormat={v => `$${v}`}
          />
          <div style={{ display: "flex", gap: 14, marginTop: 10, fontSize: 10, fontFamily: "var(--font-mono)", flexWrap: "wrap" }}>
            {[["gpt-4o","var(--accent)"], ["sonnet-4","var(--success)"], ["opus-4.1","var(--warn)"], ["gemini-2.5","var(--unknown)"], ["qwen3-235b","var(--danger)"]].map(([n,c]) => (
              <span key={n} style={{ display: "flex", alignItems: "center", gap: 4, color: "var(--fg-muted)" }}>
                <div style={{ width: 10, height: 2, background: c, borderRadius: 1 }}/> {n}
              </span>
            ))}
          </div>
        </div>

        <div className="panel" style={{ padding: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <Icon name="hex" size={12}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ca.spendByModel")}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
            <Donut values={Object.entries(totals).map(([k, v], i) => ({
              label: k, value: v,
              color: ["var(--accent)","var(--success)","var(--warn)","var(--unknown)","var(--danger)"][i],
            }))} size={140} thickness={20} center={
              <>
                <div style={{ fontSize: 20, fontFamily: "var(--font-mono)", fontWeight: 500 }}>${(grandTotal/100).toFixed(0)}</div>
                <div style={{ fontSize: 9, color: "var(--fg-faint)", fontFamily: "var(--font-mono)", letterSpacing: "0.1em" }}>{t("ca.total")}</div>
              </>
            }/>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
              {Object.entries(totals).sort((a, b) => b[1] - a[1]).map(([k, v], i) => {
                const pct = (v / grandTotal * 100).toFixed(1);
                const color = ["var(--accent)","var(--success)","var(--warn)","var(--unknown)","var(--danger)"][i];
                return (
                  <div key={k} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}>
                    <div style={{ width: 8, height: 8, background: color, borderRadius: 2 }}/>
                    <span style={{ fontFamily: "var(--font-mono)", flex: 1 }}>{k}</span>
                    <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>${(v/100).toFixed(0)}</span>
                    <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg-faint)", width: 44, textAlign: "right" }}>{pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Table pivot */}
      <div className="panel" style={{ overflow: "hidden" }}>
        <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="menu" size={12}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ca.pivot")}</span>
          <div style={{ display: "flex", gap: 4, marginLeft: 8 }}>
            {[["model",t("ca.byModel")],["project",t("ca.byProject")],["task",t("ca.byTask")]].map(([v,l]) => (
              <button key={v} onClick={() => setPivot(v)} className="btn sm ghost" style={{
                background: pivot === v ? "var(--bg-hover)" : "transparent",
                color: pivot === v ? "var(--fg)" : "var(--fg-muted)",
                fontWeight: pivot === v ? 500 : 400,
                borderColor: pivot === v ? "var(--border-strong)" : "transparent",
              }}>{l}</button>
            ))}
          </div>
        </div>
        <div className="row head" style={{ gridTemplateColumns: "1.5fr 100px 100px 100px 100px 100px 120px" }}>
          <span>{pivot}</span>
          <span>{t("ca.requests")}</span>
          <span>{t("ca.tokens")}</span>
          <span>{t("ca.spend")}</span>
          <span>{t("ca.avg1k")}</span>
          <span>{t("ca.share")}</span>
          <span>{t("ca.trend7d")}</span>
        </div>
        {(pivot === "model" ? FIX_BUDGET.entries_by_model : pivot === "project" ? FIX_PROJECTS.slice(0, 4).map(p => ({ label: p.name, cost_minor: p.spent_minor, tokens: p.spent_minor * 30 })) : [
          { label: "literature", cost_minor: 720000, tokens: 4200000 },
          { label: "experiments", cost_minor: 1240000, tokens: 6800000 },
          { label: "review", cost_minor: 620000, tokens: 1400000 },
          { label: "writeup", cost_minor: 240000, tokens: 800000 },
        ]).map((e, i) => {
          const share = e.cost_minor / grandTotal / 100 * 100;
          return (
            <div key={i} className="row" style={{ gridTemplateColumns: "1.5fr 100px 100px 100px 100px 100px 120px" }}>
              <span style={{ fontSize: 12, fontWeight: 500 }}>{e.label}</span>
              <span className="mono" style={{ fontSize: 11 }}>{Math.round(e.tokens/1000).toLocaleString()}k</span>
              <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>{Math.round(e.tokens/1000).toLocaleString()}k</span>
              <span className="mono" style={{ fontSize: 12, fontWeight: 500 }}>${(e.cost_minor/100000).toFixed(2)}</span>
              <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>${(e.cost_minor/e.tokens*1000/100).toFixed(3)}</span>
              <span>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ flex: 1, height: 3, background: "var(--bg-sunken)", borderRadius: 2, minWidth: 40 }}>
                    <div style={{ width: `${Math.min(share, 100)}%`, height: "100%", background: "var(--accent)", borderRadius: 2 }}/>
                  </div>
                  <span className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>{share.toFixed(1)}%</span>
                </div>
              </span>
              <span><Sparkline data={Array.from({length: 7}, (_, k) => Math.sin(i * 2 + k * 0.7) * 20 + e.cost_minor / 100000 / 30 * (1 + k*0.05))} width={100} height={22}/></span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

Object.assign(window, { CostAnalyticsScreen });
