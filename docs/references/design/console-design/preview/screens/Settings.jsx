/* Settings Screen — personal + workspace settings.
   Sections: Profile · Notifications · API Keys · Security · Preferences */

const SettingsScreen = () => {
  const { t, lang, setLang } = useI18n();
  const [section, setSection] = useState("profile");
  const [prefs, setPrefs] = useState({
    notifyApprovals: true,
    notifyAlerts: true,
    notifyDigest: true,
    notifyClaims: false,
    twoFA: true,
    ssoOnly: false,
    autonomyDefault: "SUPERVISED",
  });

  const sections = [
    { id: "profile", icon: "circle", label: t("st.profile") },
    { id: "notifications", icon: "menu", label: t("st.notifications") },
    { id: "apikeys", icon: "lock", label: t("st.apikeys") },
    { id: "security", icon: "shield", label: t("st.security") },
    { id: "workspace", icon: "hex", label: t("st.workspace") },
    { id: "preferences", icon: "diamond", label: t("st.preferences") },
    { id: "billing", icon: "graph", label: t("st.billing") },
  ];

  const apiKeys = [
    { id: "key_1", label: "prod-writer", scope: "runs:write · claims:read", created: "2026-08-01", last_used: "2026-08-27T14:20:00Z", masked: "sk-••••••••abc7f2" },
    { id: "key_2", label: "readonly-dashboard", scope: "*:read", created: "2026-07-14", last_used: "2026-08-27T13:55:00Z", masked: "sk-••••••••b3d891" },
    { id: "key_3", label: "ci-pipeline", scope: "runs:write · endpoints:invoke", created: "2026-06-02", last_used: null, masked: "sk-••••••••7fa2c1" },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 16, flex: 1, minHeight: 0 }}>
      {/* Section rail */}
      <aside className="panel" style={{ padding: 8, overflow: "auto" }}>
        <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", padding: "6px 10px" }}>{t("st.title")}</div>
        {sections.map(s => (
          <button key={s.id} onClick={() => setSection(s.id)} style={{
            width: "100%", display: "flex", alignItems: "center", gap: 10,
            padding: "8px 10px", fontSize: 12,
            background: section === s.id ? "var(--accent-dim)" : "transparent",
            color: section === s.id ? "var(--accent)" : "var(--fg-muted)",
            border: "none", borderRadius: 4, textAlign: "left",
            fontFamily: "inherit", cursor: "pointer", marginBottom: 2,
          }}>
            <Icon name={s.icon} size={12}/> {s.label}
          </button>
        ))}
      </aside>

      {/* Content */}
      <main className="panel" style={{ padding: 24, overflow: "auto" }}>
        {section === "profile" && (
          <SettingsPage title={t("st.profile")} subtitle={t("st.profileSub")}>
            <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
              <div style={{
                width: 88, height: 88, borderRadius: 8,
                background: "hsl(180, 40%, 40%)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 28, fontFamily: "var(--font-mono)", color: "#fff", fontWeight: 500,
              }}>LT</div>
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>
                <FormRow label={t("st.p.name")}><TextInput value={lang === "zh-CN" ? "田中 玲央" : "Leo Tanaka"} onChange={()=>{}}/></FormRow>
                <FormRow label={t("st.p.email")}><TextInput mono value="leo.tanaka@research.io" onChange={()=>{}}/></FormRow>
                <FormRow label={t("st.p.role")}><Select value="pi" onChange={()=>{}} options={[
                  { value: "pi", label: t("st.p.rolePI") },
                  { value: "researcher", label: t("st.p.roleR") },
                  { value: "reviewer", label: t("st.p.roleRev") },
                  { value: "admin", label: t("st.p.roleAdmin") },
                ]}/></FormRow>
                <FormRow label={t("st.p.timezone")}><Select value="asia_tokyo" onChange={()=>{}} options={[
                  { value: "asia_tokyo", label: "Asia/Tokyo (JST +09:00)" },
                  { value: "america_ny", label: "America/New_York (EDT -04:00)" },
                  { value: "europe_lon", label: "Europe/London (BST +01:00)" },
                ]}/></FormRow>
              </div>
            </div>
          </SettingsPage>
        )}

        {section === "notifications" && (
          <SettingsPage title={t("st.notifications")} subtitle={t("st.notificationsSub")}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <NotifRow label={t("st.n.approvals")} desc={t("st.n.approvalsDesc")} value={prefs.notifyApprovals} onChange={v => setPrefs({...prefs, notifyApprovals: v})}/>
              <NotifRow label={t("st.n.alerts")} desc={t("st.n.alertsDesc")} value={prefs.notifyAlerts} onChange={v => setPrefs({...prefs, notifyAlerts: v})}/>
              <NotifRow label={t("st.n.digest")} desc={t("st.n.digestDesc")} value={prefs.notifyDigest} onChange={v => setPrefs({...prefs, notifyDigest: v})}/>
              <NotifRow label={t("st.n.claims")} desc={t("st.n.claimsDesc")} value={prefs.notifyClaims} onChange={v => setPrefs({...prefs, notifyClaims: v})}/>
            </div>
            <div style={{ marginTop: 20, padding: 12, background: "var(--bg-sunken)", borderRadius: 6, fontSize: 11, color: "var(--fg-muted)" }}>
              <Icon name="q" size={11} style={{ color: "var(--fg-faint)", marginRight: 6 }}/>
              {t("st.n.channel")}: <span className="mono">slack:@leo.tanaka · email:leo.tanaka@research.io</span>
            </div>
          </SettingsPage>
        )}

        {section === "apikeys" && (
          <SettingsPage title={t("st.apikeys")} subtitle={t("st.apikeysSub")}
            action={<button className="btn primary sm"><Icon name="plus" size={11}/> {t("st.k.new")}</button>}>
            <div className="panel" style={{ overflow: "hidden" }}>
              <div className="row head" style={{ gridTemplateColumns: "1.2fr 1.5fr 1fr 130px 130px 60px" }}>
                <span>{t("st.k.label")}</span><span>{t("st.k.scope")}</span><span>{t("st.k.masked")}</span><span>{t("st.k.created")}</span><span>{t("st.k.lastUsed")}</span><span></span>
              </div>
              {apiKeys.map(k => (
                <div key={k.id} className="row" style={{ gridTemplateColumns: "1.2fr 1.5fr 1fr 130px 130px 60px" }}>
                  <span style={{ fontSize: 12, fontWeight: 500 }}>{k.label}</span>
                  <span className="mono" style={{ fontSize: 10, color: "var(--fg-muted)" }}>{k.scope}</span>
                  <span className="mono" style={{ fontSize: 11 }}>{k.masked}</span>
                  <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)" }}>{k.created}</span>
                  <span className="mono" style={{ fontSize: 10, color: k.last_used ? "var(--fg-faint)" : "var(--fg-faint)" }}>
                    {k.last_used ? new Date(k.last_used).toISOString().slice(5, 16).replace("T", " ") : <span className="empty-mark">{t("st.k.never")}</span>}
                  </span>
                  <button className="btn sm ghost" style={{ justifySelf: "start" }}><Icon name="x" size={10}/></button>
                </div>
              ))}
            </div>
          </SettingsPage>
        )}

        {section === "security" && (
          <SettingsPage title={t("st.security")} subtitle={t("st.securitySub")}>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <NotifRow label={t("st.s.twoFA")} desc={t("st.s.twoFADesc")} value={prefs.twoFA} onChange={v => setPrefs({...prefs, twoFA: v})}/>
              <NotifRow label={t("st.s.ssoOnly")} desc={t("st.s.ssoOnlyDesc")} value={prefs.ssoOnly} onChange={v => setPrefs({...prefs, ssoOnly: v})}/>
              <div style={{ padding: 12, background: "var(--warn-dim)", border: "1px solid var(--warn-line)", borderRadius: 6, display: "flex", gap: 10 }}>
                <Icon name="warn-tri" size={13} style={{ color: "var(--warn)", flexShrink: 0, marginTop: 1 }}/>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 500, color: "var(--warn)", marginBottom: 4 }}>{t("st.s.sessionsTitle")}</div>
                  <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>3 {t("st.s.sessions")} · Tokyo · Kyoto · Yokohama</div>
                  <button className="btn sm" style={{ marginTop: 8 }}>{t("st.s.revokeAll")}</button>
                </div>
              </div>
              <FormRow label={t("st.s.defaultAutonomy")} hint={t("st.s.autonomyHint")}>
                <Select value={prefs.autonomyDefault} onChange={v => setPrefs({...prefs, autonomyDefault: v})} options={[
                  { value: "MANUAL", label: "MANUAL" },
                  { value: "SUPERVISED", label: "SUPERVISED" },
                  { value: "GUARDED_AUTONOMOUS", label: "GUARDED_AUTONOMOUS" },
                  { value: "AUTONOMOUS", label: "AUTONOMOUS" },
                ]}/>
              </FormRow>
            </div>
          </SettingsPage>
        )}

        {section === "workspace" && (
          <SettingsPage title={t("st.workspace")} subtitle={t("st.workspaceSub")}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {FIX_WORKSPACES.map(w => (
                <div key={w.id} className="panel" style={{
                  padding: 14, display: "flex", alignItems: "center", gap: 12,
                  borderLeft: w.current ? "3px solid var(--accent)" : "1px solid var(--border)",
                }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 6,
                    background: "var(--bg-raised)", border: "1px solid var(--border)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500,
                  }}>{w.name.slice(0, 2).toUpperCase()}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{w.name}</div>
                    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{w.role.toUpperCase()} · {w.members} {t("st.ws.members")} · {w.plan}</div>
                  </div>
                  {w.current && <StatusBadge tone="success" icon="check" label={t("st.ws.current")} filled/>}
                  {!w.current && <button className="btn sm">{t("st.ws.switch")}</button>}
                </div>
              ))}
              <button className="btn sm ghost" style={{ marginTop: 4 }}><Icon name="plus" size={11}/> {t("st.ws.create")}</button>
            </div>
          </SettingsPage>
        )}

        {section === "preferences" && (
          <SettingsPage title={t("st.preferences")} subtitle={t("st.preferencesSub")}>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <FormRow label={t("st.pf.language")}><Select value={lang} onChange={v => setLang(v)} options={[
                { value: "en", label: "English" }, { value: "zh-CN", label: "简体中文" },
              ]}/></FormRow>
              <FormRow label={t("st.pf.dateFormat")}><Select value="iso" onChange={()=>{}} options={[
                { value: "iso", label: "2026-08-30 14:33 (ISO 8601)" },
                { value: "us", label: "Aug 30, 2026 2:33 PM" },
                { value: "eu", label: "30/08/2026 14:33" },
              ]}/></FormRow>
              <FormRow label={t("st.pf.currency")}><Select value="usd" onChange={()=>{}} options={[
                { value: "usd", label: "USD $ (native)" }, { value: "jpy", label: "JPY ¥ (converted)" }, { value: "eur", label: "EUR € (converted)" },
              ]}/></FormRow>
              <FormRow label={t("st.pf.digest")} hint={t("st.pf.digestHint")}><Select value="daily" onChange={()=>{}} options={[
                { value: "off", label: t("st.pf.digestOff") },
                { value: "daily", label: t("st.pf.digestDaily") },
                { value: "weekly", label: t("st.pf.digestWeekly") },
              ]}/></FormRow>
            </div>
          </SettingsPage>
        )}

        {section === "billing" && (
          <SettingsPage title={t("st.billing")} subtitle={t("st.billingSub")}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 16 }}>
              <MetricCard label={t("st.b.plan")} value="Enterprise" sub={<span>{t("st.b.planSub")}</span>}/>
              <MetricCard label={t("st.b.thisMonth")} value="$12,480" sub={<span>67% {t("st.b.ofCap")}</span>} bar={0.67}/>
              <MetricCard label={t("st.b.seats")} value="24 / 30" sub={<span>{t("st.b.seatsSub")}</span>}/>
            </div>
            <div className="panel" style={{ padding: 14 }}>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>{t("st.b.invoices")}</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {[
                  { period: "2026-08", amount: 12480, status: "current", due: "2026-09-15" },
                  { period: "2026-07", amount: 11820, status: "paid", due: "2026-08-15" },
                  { period: "2026-06", amount: 10940, status: "paid", due: "2026-07-15" },
                ].map(inv => (
                  <div key={inv.period} style={{ display: "grid", gridTemplateColumns: "100px 1fr 120px 100px 60px", gap: 12, padding: "8px 4px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11, alignItems: "center" }}>
                    <span className="mono">{inv.period}</span>
                    <span style={{ color: "var(--fg-muted)" }}>Enterprise · monthly</span>
                    <span className="mono">${inv.amount.toLocaleString()}</span>
                    {inv.status === "current"
                      ? <StatusBadge tone="warn" icon="clock" label={t("st.b.due")} size="sm"/>
                      : <StatusBadge tone="success" icon="check" label={t("st.b.paid")} size="sm" filled/>}
                    <button className="btn sm ghost"><Icon name="external" size={10}/></button>
                  </div>
                ))}
              </div>
            </div>
          </SettingsPage>
        )}
      </main>
    </div>
  );
};

const SettingsPage = ({ title, subtitle, action, children }) => (
  <div style={{ maxWidth: 720 }}>
    <div style={{ display: "flex", alignItems: "flex-end", gap: 12, marginBottom: 20 }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 18, fontWeight: 500, letterSpacing: "-0.005em" }}>{title}</div>
        {subtitle && <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 4 }}>{subtitle}</div>}
      </div>
      {action}
    </div>
    {children}
  </div>
);

const NotifRow = ({ label, desc, value, onChange }) => (
  <div style={{
    display: "flex", alignItems: "center", gap: 12,
    padding: "12px 14px",
    background: "var(--bg-raised)",
    border: "1px solid var(--border)",
    borderRadius: 6,
  }}>
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 12, fontWeight: 500 }}>{label}</div>
      {desc && <div style={{ fontSize: 11, color: "var(--fg-muted)", marginTop: 2 }}>{desc}</div>}
    </div>
    <button onClick={() => onChange(!value)} style={{
      width: 36, height: 18, borderRadius: 9,
      background: value ? "var(--accent)" : "var(--bg-sunken)",
      border: `1px solid ${value ? "var(--accent)" : "var(--border-strong)"}`,
      padding: 0, cursor: "pointer", position: "relative",
    }}>
      <div style={{
        width: 12, height: 12, borderRadius: "50%",
        background: "#fff",
        position: "absolute", top: 2, left: value ? 20 : 2,
        transition: "left 140ms",
      }}/>
    </button>
  </div>
);

Object.assign(window, { SettingsScreen });
