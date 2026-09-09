/* Screen 2: Endpoints & Models */

const EndpointsScreen = () => {
  const { t } = useI18n();
  const [selectedEndpointId, setSelectedEndpointId] = useState("ep_anthropic_direct");
  const [filter, setFilter] = useState("all");

  let models = FIX_MODELS.filter(m => m.endpoint_id === selectedEndpointId);
  if (filter === "enabled") models = models.filter(m => m.enabled);
  if (filter === "fp-unavailable") models = models.filter(m => !m.provider_fingerprint_available);
  if (filter === "drift") models = models.filter(m => m.drift_alert);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 12, flex: 1, minHeight: 0 }}>
      {/* Endpoint list */}
      <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="wifi" size={12} style={{ color: "var(--fg-muted)" }}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ep.endpoints")}</span>
          <span className="chip">{FIX_ENDPOINTS.length}</span>
          <button className="btn sm" style={{ marginLeft: "auto" }}><Icon name="plus" size={10}/> {t("ep.add")}</button>
        </div>
        <div style={{ flex: 1, overflow: "auto" }}>
          {FIX_ENDPOINTS.map(ep => {
            const selected = ep.id === selectedEndpointId;
            const healthColor = ep.health === "ok" ? "var(--success)" : ep.health === "fail" ? "var(--danger)" : "var(--unknown)";
            const healthIcon = ep.health === "ok" ? "circle" : ep.health === "fail" ? "x" : "circle-o";
            return (
              <div key={ep.id} onClick={() => setSelectedEndpointId(ep.id)} style={{
                padding: "10px 12px", cursor: "pointer",
                background: selected ? "var(--bg-hover)" : "transparent",
                borderLeft: `2px solid ${selected ? "var(--accent)" : "transparent"}`,
                borderBottom: "1px solid var(--border-subtle)",
                opacity: ep.enabled ? 1 : 0.5,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
                  <Icon name={healthIcon} size={10} style={{ color: healthColor }}/>
                  <span style={{ fontSize: 12, fontWeight: 500 }}>{ep.name}</span>
                  {!ep.enabled && <span className="chip" style={{ marginLeft: "auto", color: "var(--fg-faint)" }}>{t("ep.disabled")}</span>}
                </div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", marginBottom: 3, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{ep.base_url}</div>
                <div style={{ display: "flex", gap: 8, fontSize: 10, color: "var(--fg-muted)" }}>
                  <span>{ep.models_count} {t("ep.models")}</span>
                  <span>·</span>
                  <span style={{ color: healthColor }}>
                    {ep.latency_ms != null ? `${ep.latency_ms}ms` : <span style={{ color: "var(--unknown)" }}>{t("ep.latencyUnknown")}</span>}
                  </span>
                  <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)" }}>
                    {ep.credential === "configured" ? t("ep.credConfig") : t("ep.credMissing")}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Models table */}
      <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="hex" size={12} style={{ color: "var(--fg-muted)" }}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ep.models2")} · {FIX_ENDPOINTS.find(e=>e.id===selectedEndpointId)?.name}</span>
          <span className="chip">{models.length}</span>
          <div style={{ marginLeft: "auto", display: "flex", gap: 4 }}>
            {[["all",t("tl.filterAll")],["enabled",t("ep.filterEnabled")],["fp-unavailable",t("ep.filterFp")],["drift",t("ep.filterDrift")]].map(([v,l]) => (
              <button key={v} onClick={() => setFilter(v)} className="btn sm ghost" style={{
                background: filter === v ? "var(--bg-hover)" : "transparent",
                color: filter === v ? "var(--fg)" : "var(--fg-muted)",
              }}>{l}</button>
            ))}
            <div className="vr" style={{ height: 18, margin: "0 4px" }}/>
            <button className="btn sm"><Icon name="flask" size={10}/> {t("ep.probeAll")}</button>
            <button className="btn sm"><Icon name="search" size={10}/> {t("ep.discover")}</button>
          </div>
        </div>

        <div style={{ flex: 1, overflow: "auto" }}>
          <div className="row head" style={{ gridTemplateColumns: "auto 200px 1fr 90px auto auto 120px auto" }}>
            <span></span><span>{t("ep.colHead.display")}</span><span>{t("ep.colHead.caps")}</span><span>{t("ep.colHead.ctx")}</span><span>{t("ep.colHead.reprod")}</span><span>{t("ep.colHead.enabled")}</span><span>{t("ep.colHead.lastProbe")}</span><span></span>
          </div>
          {models.map(m => (
            <div key={m.id} className="row" style={{ gridTemplateColumns: "auto 200px 1fr 90px auto auto 120px auto" }}>
              <Icon name="hex" size={12} style={{ color: m.enabled ? "var(--accent)" : "var(--fg-faint)" }}/>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 500 }}>{m.display_name}</div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{m.model_id}</div>
                {m.drift_alert && (
                  <div style={{ marginTop: 3, fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--warn)", display: "flex", gap: 4, alignItems: "center" }}>
                    <Icon name="warn-tri" size={9}/> {t("ep.returned")} {m.returned_model_name}
                  </div>
                )}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
                {m.capabilities.map(c => (
                  <span key={c.name} title={`source: ${c.source} · confidence: ${c.confidence != null ? c.confidence : "n/a"}`}
                    style={{
                      display: "inline-flex", alignItems: "center", gap: 3,
                      padding: "1px 5px", height: 16, borderRadius: 3,
                      fontSize: 10, fontFamily: "var(--font-mono)",
                      background: c.status === "degraded" ? "var(--warn-dim)" : c.status === "unknown" ? "var(--unknown-dim)" : "var(--success-dim)",
                      border: `1px solid ${c.status === "degraded" ? "var(--warn-line)" : c.status === "unknown" ? "var(--unknown-line)" : "var(--success-line)"}`,
                      color: c.status === "degraded" ? "var(--warn)" : c.status === "unknown" ? "var(--unknown)" : "var(--success)",
                    }}>
                    {c.name}
                  </span>
                ))}
              </div>
              <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>{(m.context_window/1000).toFixed(0)}k</span>
              <ReproducibilityChip fingerprint={m.system_fingerprint} providerAvailable={m.provider_fingerprint_available} compact={true}/>
              <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11 }}>
                {m.enabled
                  ? <Icon name="check" size={11} style={{ color: "var(--success)" }}/>
                  : <Icon name="ban" size={11} style={{ color: "var(--fg-faint)" }}/>}
                {m.enabled ? t("ep.on") : t("ep.off")}
              </span>
              <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{m.last_probe ? m.last_probe.slice(5,16).replace("T", " ") : <span style={{ color: "var(--unknown)" }}>{t("ep.never")}</span>}</span>
              <button className="btn sm ghost"><Icon name="chevron-r" size={10}/></button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { EndpointsScreen });
