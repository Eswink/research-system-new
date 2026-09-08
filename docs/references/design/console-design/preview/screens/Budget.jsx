/* Screen 9: Budget & Usage — enforces P4 (UNKNOWN ≠ 0) */

const BudgetScreen = () => {
  const { t } = useI18n();
  const b = FIX_BUDGET;
  const burnRate = 3120000 / 38; // $ minor / min
  const totalReserved = b.reservations.reduce((a, r) => a + r.reserved_minor, 0);
  const totalUsed = b.reservations.reduce((a, r) => a + r.used_minor, 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0, overflow: "auto" }}>
      {/* Metric cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <MetricCard
          label={t("bg.totalSpent")}
          value={`$${(b.actual_cost_minor/100000).toFixed(2)}`}
          sub={<span>of <span className="mono">${(b.budget_cap_minor/100000).toFixed(2)}</span> cap · {((b.actual_cost_minor/b.budget_cap_minor)*100).toFixed(1)}%</span>}
          bar={b.actual_cost_minor / b.budget_cap_minor}
          barColor="var(--accent)"
        />
        <MetricCard
          label={t("bg.reserved")}
          value={`$${(totalReserved/100000).toFixed(2)}`}
          sub={<span><span className="mono">${(totalUsed/100000).toFixed(2)}</span> {t("bg.reservedOf")} ({(totalUsed/totalReserved*100).toFixed(0)}%)</span>}
          bar={totalUsed/totalReserved}
          barColor="var(--success)"
        />
        <MetricCard
          label={t("bg.unknown")}
          value={<span style={{ color: "var(--unknown)" }}>{b.unknown_cost_entries}</span>}
          sub={<span style={{ color: "var(--unknown)" }}>{t("bg.unknownSub")} <span className="mono">cost_status=UNKNOWN</span></span>}
          unknownWarn
        />
        <MetricCard
          label={t("bg.burn")}
          value={`$${(burnRate/100000*60).toFixed(2)}/hr`}
          sub={<span>{t("bg.burnProj")} <span className="mono" style={{ color: "var(--warn)" }}>{t("bg.burnEta")}</span></span>}
          bar={0.86}
          barColor="var(--warn)"
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 12, flex: 1, minHeight: 0 }}>
        {/* Reservations */}
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="diamond" size={12} style={{ color: "var(--fg-muted)" }}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("bg.reservations")}</span>
            <span className="chip">{b.reservations.length}</span>
          </div>
          <div style={{ flex: 1, overflow: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 12 }}>
            {b.reservations.map(r => {
              const pct = r.used_minor / r.reserved_minor;
              const over = pct > 0.9;
              return (
                <div key={r.id}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5, fontSize: 12 }}>
                    <span style={{ fontWeight: 500 }}>{r.label}</span>
                    <span className="mono" style={{ color: "var(--fg-muted)" }}>
                      <span style={{ color: over ? "var(--warn)" : "var(--fg)" }}>${(r.used_minor/100000).toFixed(2)}</span>
                      {" "}/ ${(r.reserved_minor/100000).toFixed(2)}
                      {" "}<span style={{ color: "var(--fg-faint)" }}>· {(pct*100).toFixed(0)}%</span>
                    </span>
                  </div>
                  <div style={{ height: 8, background: "var(--bg-sunken)", borderRadius: 3, overflow: "hidden", position: "relative" }}>
                    <div style={{
                      width: `${Math.min(100, pct * 100)}%`, height: "100%",
                      background: over ? "var(--warn)" : "var(--accent)",
                      transition: "width 300ms",
                    }}/>
                  </div>
                </div>
              );
            })}
            <div style={{ marginTop: 8, padding: 10, background: "var(--unknown-dim)", border: "1px dashed var(--unknown-line)", borderRadius: 6, fontSize: 11, color: "var(--unknown)", lineHeight: 1.55 }}>
              <Icon name="q" size={10}/> <strong>{b.unknown_cost_entries} {t("bg.unknownNote1")}</strong> <span className="mono">cost_status=UNKNOWN</span> {t("bg.unknownNote2")}
            </div>
          </div>
        </div>

        {/* Attribution by model */}
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="hex" size={12} style={{ color: "var(--fg-muted)" }}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("bg.byModel")}</span>
          </div>
          <div style={{ flex: 1, overflow: "auto", padding: 12 }}>
            {(() => {
              const total = b.entries_by_model.reduce((a, e) => a + e.cost_minor, 0);
              return b.entries_by_model.sort((a,b)=>b.cost_minor-a.cost_minor).map((e, i) => {
                const pct = e.cost_minor / total;
                return (
                  <div key={e.model_id} style={{ marginBottom: 12 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: 11, fontFamily: "var(--font-mono)" }}>{e.label}</span>
                      <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>${(e.cost_minor/100000).toFixed(2)}</span>
                    </div>
                    <div style={{ height: 5, background: "var(--bg-sunken)", borderRadius: 2, overflow: "hidden" }}>
                      <div style={{ width: `${pct*100}%`, height: "100%", background: `hsl(${210 + i * 25}, 60%, 55%)` }}/>
                    </div>
                    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", marginTop: 2 }}>
                      {(e.tokens/1000000).toFixed(2)}M tokens · ${(e.cost_minor/100000/(e.tokens/1000)*100).toFixed(3)}/1K tok
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ label, value, sub, bar, barColor, unknownWarn }) => (
  <div className="panel" style={{
    padding: 14,
    border: unknownWarn ? "1px dashed var(--unknown-line)" : "1px solid var(--border)",
    background: unknownWarn ? "var(--unknown-dim)" : "var(--bg-panel)",
  }}>
    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6 }}>{label}</div>
    <div style={{ fontSize: 22, fontWeight: 500, fontFamily: "var(--font-mono)", marginBottom: 6, letterSpacing: "-0.01em" }}>{value}</div>
    <div style={{ fontSize: 11, color: "var(--fg-muted)", marginBottom: bar != null ? 8 : 0 }}>{sub}</div>
    {bar != null && (
      <div style={{ height: 4, background: "var(--bg-sunken)", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: `${Math.min(100, bar * 100)}%`, height: "100%", background: barColor }}/>
      </div>
    )}
  </div>
);

Object.assign(window, { BudgetScreen });
