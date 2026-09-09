/* Screen 3: Team & Model Binding — Template + Role list + Agent grid */

const TeamScreen = () => {
  const { t } = useI18n();
  const [template, setTemplate] = useState("STANDARD");
  const [selectedAgent, setSelectedAgent] = useState(null);

  // Identify heterogeneity conflicts — agents sharing same model_id
  const modelUsage = {};
  FIX_AGENTS.forEach(a => {
    const mid = a.model_binding.model_id || a.resolved_model_id;
    if (!modelUsage[mid]) modelUsage[mid] = [];
    modelUsage[mid].push(a.id);
  });

  const templates = [
    { id: "LEAN", label: "LEAN", roles: 5, desc: t("tm.tmpl.lean.desc"), agents: "5-7" },
    { id: "STANDARD", label: "STANDARD", roles: 8, desc: t("tm.tmpl.std.desc"), agents: "10-14" },
    { id: "RIGOROUS", label: "RIGOROUS", roles: 12, desc: t("tm.tmpl.rig.desc"), agents: "16-24" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0, overflow: "auto" }}>
      {/* Template selector */}
      <div className="panel" style={{ padding: 14 }}>
        <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 8 }}>{t("tm.template")}</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
          {templates.map(tt => (
            <div key={tt.id} onClick={() => setTemplate(tt.id)} style={{
              padding: 12, borderRadius: 6, cursor: "pointer",
              background: template === tt.id ? "var(--accent-dim)" : "var(--bg-raised)",
              border: `1px solid ${template === tt.id ? "var(--accent)" : "var(--border)"}`,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <span className="mono" style={{ fontSize: 12, fontWeight: 500, color: template === tt.id ? "var(--accent)" : "var(--fg)" }}>{tt.label}</span>
                <span className="chip">{tt.roles} {t("tm.tmplRoles")} · {tt.agents} {t("tm.tmplAgents")}</span>
              </div>
              <div style={{ fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.45 }}>{tt.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Roles + Agent grid */}
      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 12, flex: 1, minHeight: 0 }}>
        {/* Roles */}
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="menu" size={12} style={{ color: "var(--fg-muted)" }}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("tm.roles")}</span>
            <span className="chip">{FIX_ROLES.filter(r => r.active > 0).length}/{FIX_ROLES.length}</span>
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {FIX_ROLES.map(r => (
              <div key={r.id} style={{
                padding: "8px 12px",
                borderBottom: "1px solid var(--border-subtle)",
                opacity: r.active === 0 ? 0.55 : 1,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
                  <Icon name={r.active === 0 ? "circle-dash" : "circle"} size={10} style={{ color: r.active === 0 ? "var(--fg-faint)" : "var(--accent)" }}/>
                  <span style={{ fontSize: 12, fontWeight: 500, color: r.active === 0 ? "var(--fg-faint)" : "var(--fg)" }}>{r.name}</span>
                  <span className="chip" style={{ marginLeft: "auto", fontFamily: "var(--font-mono)" }}>{r.active}/{r.max}</span>
                </div>
                {r.collapsed_reason && (
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", marginBottom: 4 }}>
                    {t("tm.rolesCollapsed")} {r.collapsed_reason}
                  </div>
                )}
                <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
                  {r.capabilities.slice(0, 4).map(c => (
                    <span key={c} style={{ fontSize: 9, fontFamily: "var(--font-mono)", padding: "0 4px", height: 14, display: "inline-flex", alignItems: "center", borderRadius: 2, background: "var(--bg-raised)", color: "var(--fg-muted)", border: "1px solid var(--border-subtle)" }}>
                      {c}
                    </span>
                  ))}
                  {r.forbidden.map(c => (
                    <span key={c} title="forbidden capability" style={{ fontSize: 9, fontFamily: "var(--font-mono)", padding: "0 4px", height: 14, display: "inline-flex", alignItems: "center", borderRadius: 2, color: "var(--danger)", border: "1px solid var(--danger-line)", textDecoration: "line-through", opacity: 0.85 }}>
                      <Icon name="ban" size={8} style={{ marginRight: 2 }}/>{c}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Agent grid */}
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="graph" size={12} style={{ color: "var(--fg-muted)" }}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("tm.agents")}</span>
            <span className="chip">{FIX_AGENTS.length}</span>
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--warn)" }}>
              <Icon name="warn-tri" size={11}/> {t("tm.hetConflict")}
            </div>
          </div>
          <div style={{ flex: 1, overflow: "auto", padding: 12, display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 10, alignContent: "start" }}>
            {FIX_AGENTS.map(a => {
              const role = FIX_ROLES.find(r => r.id === a.role_id);
              const modelId = a.model_binding.model_id || a.resolved_model_id;
              const model = FIX_MODELS.find(m => m.id === modelId);
              const shares = modelUsage[modelId]?.filter(id => id !== a.id) || [];
              const isConflict = a.id === "ag_ethics_01"; // preflight-flagged heterogeneity
              return (
                <div key={a.id} onClick={() => setSelectedAgent(a.id)} style={{
                  padding: 12, borderRadius: 6, cursor: "pointer",
                  background: "var(--bg-panel)",
                  border: `1px solid ${isConflict ? "var(--warn-line)" : selectedAgent === a.id ? "var(--accent)" : "var(--border)"}`,
                  position: "relative",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <div style={{
                      width: 22, height: 22, borderRadius: 3,
                      background: `hsl(${(a.id.charCodeAt(3) * 37) % 360}, 40%, 40%)`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 10, fontFamily: "var(--font-mono)", color: "#fff", fontWeight: 500,
                    }}>{a.name.slice(0,2).toUpperCase()}</div>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: 500 }}>{a.name}</div>
                      <div style={{ fontSize: 10, color: "var(--fg-faint)" }}>{role?.name}</div>
                    </div>
                    {isConflict && <span title="Heterogeneity conflict" style={{ display: "inline-flex", padding: 3, borderRadius: 3, background: "var(--warn-dim)", color: "var(--warn)" }}><Icon name="warn-tri" size={10}/></span>}
                  </div>
                  <div style={{ padding: 8, background: "var(--bg-sunken)", borderRadius: 4, marginBottom: 6 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
                      <Icon name="hex" size={10} style={{ color: "var(--fg-muted)" }}/>
                      <span className="mono" style={{ fontSize: 11 }}>{model?.model_id}</span>
                      <span className="chip" style={{ marginLeft: "auto", fontSize: 9 }}>{a.model_binding.kind.slice(0,4).toLowerCase()}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                      <span>temp {a.temperature}</span>
                      {model && !model.provider_fingerprint_available && <span style={{ color: "var(--unknown)" }}>{t("tm.fpUnavail")}</span>}
                    </div>
                  </div>
                  {shares.length > 0 && (
                    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: isConflict ? "var(--warn)" : "var(--fg-faint)", display: "flex", alignItems: "center", gap: 4 }}>
                      <Icon name="graph" size={9}/> {t("tm.sharesWith")} {shares.length} {t("tm.agent")}{shares.length>1?t("tm.agents2"):""}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { TeamScreen });
