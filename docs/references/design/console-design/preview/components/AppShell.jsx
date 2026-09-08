/* App Shell — sidebar domain nav + top header + main workspace
   Extended with: Portfolio · Library · Insights · Ops domains,
   command palette, notification bell, workspace switcher, quick-create. */

/* Domain nav — post-consolidation.
   Changes:
   - `Assets` merged into `Library` (Endpoints + Setup now live with prompts/datasets/models)
   - `States` merged into `Ops` (State Matrix + Incidents + Data Health)
   - `Portfolio` gains `Compare` (multi-run diff)
   - `Library` gains `Lineage` (provenance DAG) and keeps Model Registry
   Result: 8 domains instead of 10, no functional loss, one net additional feature per merged domain. */
const DOMAINS = [
  { id: "plan", labelKey: "dom.plan", icon: "book", tabs: [
    { id: "overview", labelKey: "tab.overview" },
    { id: "protocol", labelKey: "tab.protocol" },
    { id: "team", labelKey: "tab.team" },
  ]},
  { id: "portfolio", labelKey: "dom.portfolio", icon: "hex", tabs: [
    { id: "projects", labelKey: "tab.projects" },
    { id: "experiments", labelKey: "tab.experiments" },
    { id: "runs-history", labelKey: "tab.runsHistory" },
    { id: "compare", labelKey: "tab.compare" },
  ]},
  { id: "run", labelKey: "dom.run", icon: "graph", tabs: [
    { id: "timeline", labelKey: "tab.timeline" },
    { id: "approvals", labelKey: "tab.approvals", badge: 4 },
    { id: "workspace", labelKey: "tab.workspace" },
  ]},
  { id: "library", labelKey: "dom.library", icon: "diamond", tabs: [
    { id: "prompts", labelKey: "tab.prompts" },
    { id: "datasets", labelKey: "tab.datasets" },
    { id: "notebooks", labelKey: "tab.notebooks" },
    { id: "model-registry", labelKey: "tab.modelRegistry" },
    { id: "lineage", labelKey: "tab.lineage" },
    { id: "endpoints", labelKey: "tab.endpoints" },
    { id: "setup", labelKey: "tab.setup" },
  ]},
  { id: "evidence", labelKey: "dom.evidence", icon: "diamond", tabs: [
    { id: "claims", labelKey: "tab.claims" },
  ]},
  { id: "insights", labelKey: "dom.insights", icon: "graph", tabs: [
    { id: "reports", labelKey: "tab.reports" },
    { id: "cost-analytics", labelKey: "tab.costAnalytics" },
  ]},
  { id: "ops", labelKey: "dom.opsHealth", icon: "shield", tabs: [
    { id: "alerts", labelKey: "tab.alerts", badge: 2 },
    { id: "incidents", labelKey: "tab.incidents", badge: 1 },
    { id: "schedules", labelKey: "tab.schedules" },
    { id: "integrations", labelKey: "tab.integrations" },
    { id: "data-health", labelKey: "tab.dataHealth" },
    { id: "matrix", labelKey: "tab.matrix" },
  ]},
  { id: "govern", labelKey: "dom.govern", icon: "shield", tabs: [
    { id: "budget", labelKey: "tab.budget" },
    { id: "audit", labelKey: "tab.audit" },
  ]},
];

const AppShell = () => {
  const { t, lang, setLang } = useI18n();
  const [tweaks, setTweak] = useTweaks({
    theme: "dark",
    density: "normal",
    preflightState: "WARN",
    claimsView: "graph",
    projectsView: "list",
    protocolMode: "form",
    protocolErrorLevel: "some",
    protocolLanguages: 7,
    protocolTemperatures: 6,
    protocolAdminMode: false,
  });

  const [activeDomain, setActiveDomain] = useState(() => localStorage.getItem("ros.domain") || "portfolio");
  const [activeTab, setActiveTab] = useState(() => localStorage.getItem("ros.tab") || "projects");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = tweaks.theme;
    document.documentElement.dataset.density = tweaks.density;
  }, [tweaks.theme, tweaks.density]);

  useEffect(() => {
    localStorage.setItem("ros.domain", activeDomain);
    localStorage.setItem("ros.tab", activeTab);
  }, [activeDomain, activeTab]);

  // ⌘K keyboard shortcut
  useEffect(() => {
    const h = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCmdOpen(true);
      }
    };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  }, []);

  // Meta-screens live outside DOMAINS (Settings / Notifications reached from
  // the header, not the sidebar). Fall back to portfolio if the persisted
  // domain no longer exists (e.g. old 'assets' or 'states' route).
  const isMetaScreen = activeDomain === "__settings" || activeDomain === "__notifications";
  const domain = isMetaScreen ? null : (DOMAINS.find(d => d.id === activeDomain) || DOMAINS.find(d => d.id === "portfolio"));
  const validTab = !domain ? null : (domain.tabs.find(tab => tab.id === activeTab) ? activeTab : domain.tabs[0].id);

  useEffect(() => {
    if (domain && !domain.tabs.find(tab => tab.id === activeTab)) {
      setActiveTab(domain.tabs[0].id);
    }
  }, [activeDomain]);

  // Repair a persisted domain that no longer exists post-consolidation.
  // Only run once at mount; meta-screens (__settings / __notifications) and
  // known domains are left alone. Old routes (assets / states) get mapped
  // into the consolidated homes.
  useEffect(() => {
    const startDomain = localStorage.getItem("ros.domain");
    if (!startDomain) return;
    if (startDomain === "__settings" || startDomain === "__notifications") return;
    if (DOMAINS.find(d => d.id === startDomain)) return;
    const mapping = { assets: ["library", "endpoints"], states: ["ops", "matrix"] };
    const [nd, nt] = mapping[startDomain] || ["portfolio", "projects"];
    setActiveDomain(nd);
    setActiveTab(nt);
  }, []);

  // Command palette items — jump to any screen
  const paletteItems = useMemo(() => {
    const items = [];
    DOMAINS.forEach(d => {
      d.tabs.forEach(tab => {
        items.push({
          section: t(d.labelKey),
          icon: d.icon,
          label: t(tab.labelKey),
          hint: `${d.id}/${tab.id}`,
          action: () => { setActiveDomain(d.id); setActiveTab(tab.id); },
        });
      });
    });
    items.push({
      section: t("pal.actions"),
      icon: "external",
      label: t("pal.openCC"),
      hint: t("pal.ccSub"),
      action: () => window.open("Command Center.html", "_blank"),
    });
    items.push({
      section: t("pal.actions"),
      icon: "circle-o",
      label: `${t("pal.switchTheme")} ${tweaks.theme === "dark" ? t("tw.themeLight") : t("tw.themeDark")}`,
      action: () => setTweak("theme", tweaks.theme === "dark" ? "light" : "dark"),
    });
    items.push({
      section: t("pal.actions"),
      icon: "menu",
      label: t("pal.toggleSidebar"),
      action: () => setSidebarCollapsed(!sidebarCollapsed),
    });
    items.push({
      section: t("pal.actions"),
      icon: "circle",
      label: t("pal.openSettings"),
      action: () => { setActiveDomain("__settings"); },
    });
    items.push({
      section: t("pal.actions"),
      icon: "menu",
      label: t("pal.openNotifications"),
      action: () => { setActiveDomain("__notifications"); },
    });

    // ── Cross-object search results — makes ⌘K a real search bar ─────
    (FIX_PROJECTS || []).forEach(p => items.push({
      section: t("pal.projects"), icon: "hex",
      label: p.name, hint: `${p.id} · ${p.status || ""}`,
      action: () => { setActiveDomain("portfolio"); setActiveTab("projects"); },
    }));
    (FIX_RUNS_HISTORY || []).forEach(r => items.push({
      section: t("pal.runs"), icon: "play",
      label: r.label, hint: `${r.id.slice(0, 20)} · ${r.state}`,
      action: () => { setActiveDomain("portfolio"); setActiveTab("runs-history"); },
    }));
    (FIX_CLAIMS || []).forEach(c => items.push({
      section: t("pal.claims"), icon: "diamond",
      label: (c.statement || c.id).slice(0, 60), hint: `${c.id} · ${c.status}`,
      action: () => { setActiveDomain("evidence"); setActiveTab("claims"); },
    }));
    (FIX_REGISTERED_MODELS || []).forEach(m => items.push({
      section: t("pal.models"), icon: "hex",
      label: m.family, hint: `${m.provider} · ${m.id.slice(0, 30)}`,
      action: () => { setActiveDomain("library"); setActiveTab("model-registry"); },
    }));
    (FIX_DATASETS || []).forEach(d => items.push({
      section: t("pal.datasets"), icon: "book",
      label: d.name, hint: `${d.id} · ${d.rows || ""} rows`,
      action: () => { setActiveDomain("library"); setActiveTab("datasets"); },
    }));
    (FIX_PROMPTS || []).forEach(p => items.push({
      section: t("pal.prompts"), icon: "diamond",
      label: p.name, hint: `${p.id} · v${p.version || 1}`,
      action: () => { setActiveDomain("library"); setActiveTab("prompts"); },
    }));

    return items;
  }, [t, tweaks.theme, sidebarCollapsed]);

  return (
    <div style={{ display: "grid", gridTemplateColumns: sidebarCollapsed ? "56px 1fr" : "220px 1fr", height: "100vh", background: "var(--bg-app)" }}>
      {/* ── Sidebar ────────────────────────────────────── */}
      <aside style={{
        background: "var(--bg-panel)",
        borderRight: "1px solid var(--border)",
        display: "flex", flexDirection: "column",
        overflow: "hidden",
      }}>
        {/* Logo */}
        <div style={{
          height: 48, padding: "0 14px",
          display: "flex", alignItems: "center", gap: 10,
          borderBottom: "1px solid var(--border)",
          cursor: "pointer",
        }} onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
          <div style={{
            width: 22, height: 22, borderRadius: 4,
            background: "linear-gradient(135deg, var(--accent), #6BA1FF)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 600, color: "#fff",
            boxShadow: "0 0 0 1px rgba(255,255,255,0.06) inset",
          }}>◇</div>
          {!sidebarCollapsed && (
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 500, letterSpacing: "-0.005em" }}>{t("app.name")}</div>
              <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{t("app.plane")}</div>
            </div>
          )}
        </div>

        {/* Workspace selector */}
        {!sidebarCollapsed && (
          <div style={{ padding: 8, borderBottom: "1px solid var(--border)" }}>
            <WorkspaceSwitcher workspaces={FIX_WORKSPACES}/>
          </div>
        )}

        {/* Domain nav */}
        <div style={{ flex: 1, overflow: "auto", padding: "8px 0" }}>
          {DOMAINS.map(d => (
            <div key={d.id}>
              <button onClick={() => setActiveDomain(d.id)} style={{
                width: "100%", display: "flex", alignItems: "center", gap: 10,
                padding: sidebarCollapsed ? "10px" : "7px 14px",
                justifyContent: sidebarCollapsed ? "center" : "flex-start",
                background: activeDomain === d.id ? "var(--bg-hover)" : "transparent",
                border: "none", cursor: "pointer",
                color: activeDomain === d.id ? "var(--fg)" : "var(--fg-muted)",
                fontFamily: "inherit", fontSize: 12, fontWeight: activeDomain === d.id ? 500 : 400,
                borderLeft: activeDomain === d.id ? "2px solid var(--accent)" : "2px solid transparent",
                textAlign: "left",
              }}>
                <Icon name={d.icon} size={13} style={{ color: activeDomain === d.id ? "var(--accent)" : "inherit" }}/>
                {!sidebarCollapsed && <span>{t(d.labelKey)}</span>}
              </button>
              {activeDomain === d.id && !sidebarCollapsed && (
                <div style={{ padding: "2px 8px 6px" }}>
                  {d.tabs.map(tab => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
                      width: "100%", display: "flex", alignItems: "center", gap: 8,
                      padding: "5px 12px 5px 32px",
                      background: activeTab === tab.id ? "var(--accent-dim)" : "transparent",
                      border: "none", cursor: "pointer",
                      color: activeTab === tab.id ? "var(--accent)" : "var(--fg-muted)",
                      fontFamily: "inherit", fontSize: 11,
                      borderRadius: 4,
                      textAlign: "left",
                    }}>
                      <span>{t(tab.labelKey)}</span>
                      {tab.badge && <span className="chip" style={{ marginLeft: "auto", color: "var(--warn)", borderColor: "var(--warn-line)", fontSize: 9, height: 15 }}>{tab.badge}</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* User */}
        {!sidebarCollapsed && (
          <button onClick={() => setActiveDomain("__settings")} style={{
            padding: 10, borderTop: "1px solid var(--border)",
            display: "flex", alignItems: "center", gap: 8,
            background: activeDomain === "__settings" ? "var(--bg-hover)" : "transparent",
            border: "none", borderLeft: activeDomain === "__settings" ? "2px solid var(--accent)" : "2px solid transparent",
            width: "100%", textAlign: "left", cursor: "pointer",
            color: "inherit", fontFamily: "inherit",
          }}
          onMouseEnter={e => { if (activeDomain !== "__settings") e.currentTarget.style.background = "var(--bg-hover)"; }}
          onMouseLeave={e => { if (activeDomain !== "__settings") e.currentTarget.style.background = "transparent"; }}
          title={t("pal.openSettings")}>
            <div style={{
              width: 24, height: 24, borderRadius: "50%",
              background: "hsl(180, 40%, 40%)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 10, fontFamily: "var(--font-mono)", color: "#fff", fontWeight: 500,
            }}>LT</div>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ fontSize: 11, fontWeight: 500 }}>{lang === "zh-CN" ? "田中 玲央" : "Leo Tanaka"}</div>
              <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{t("usr.email")}</div>
            </div>
            <Icon name="chevron-r" size={10} style={{ color: "var(--fg-faint)" }}/>
          </button>
        )}
      </aside>

      {/* ── Main ─────────────────────────────────────── */}
      <main style={{ display: "flex", flexDirection: "column", minWidth: 0, overflow: "hidden" }}>
        {/* Top header */}
        <header style={{
          height: 48, padding: "0 16px",
          borderBottom: "1px solid var(--border)",
          background: "var(--bg-panel)",
          display: "flex", alignItems: "center", gap: 12,
        }}>
          {/* Breadcrumb */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
            {isMetaScreen ? (
              <>
                <span style={{ color: "var(--fg-faint)" }}>{t("app.name")}</span>
                <Icon name="chevron-r" size={10} style={{ color: "var(--fg-faint)" }}/>
                <span style={{ fontWeight: 500 }}>
                  {activeDomain === "__settings" ? t("st.title") : t("nc.title")}
                </span>
              </>
            ) : (
              <>
                <span style={{ color: "var(--fg-faint)" }}>{t(domain.labelKey)}</span>
                <Icon name="chevron-r" size={10} style={{ color: "var(--fg-faint)" }}/>
                <span style={{ fontWeight: 500 }}>{t(domain.tabs.find(tab => tab.id === validTab)?.labelKey)}</span>
              </>
            )}
          </div>

          <div className="vr" style={{ height: 20 }}/>
          <DigestText value={FIX_RUN.id} label="run:" length={12} prefix={false}/>

          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
            {/* ⌘K Command palette trigger */}
            <button onClick={() => setCmdOpen(true)} style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              padding: "0 10px", height: 26, background: "var(--bg-raised)",
              border: "1px solid var(--border)", borderRadius: 6,
              fontSize: 11, color: "var(--fg-muted)", whiteSpace: "nowrap",
              cursor: "pointer", fontFamily: "inherit",
            }}>
              <Icon name="search" size={11}/>
              <span>{t("app.search")}</span>
              <kbd>⌘K</kbd>
            </button>

            {/* Quick create */}
            <QuickCreate onCreate={(kind) => {
              if (kind === "project") { setActiveDomain("portfolio"); setActiveTab("projects"); }
              if (kind === "experiment") { setActiveDomain("portfolio"); setActiveTab("experiments"); }
              if (kind === "prompt") { setActiveDomain("library"); setActiveTab("prompts"); }
              if (kind === "notebook") { setActiveDomain("library"); setActiveTab("notebooks"); }
              if (kind === "alert") { setActiveDomain("ops"); setActiveTab("alerts"); }
              if (kind === "schedule") { setActiveDomain("ops"); setActiveTab("schedules"); }
            }}/>

            <div className="vr" style={{ height: 20 }}/>

            {/* Big screen link */}
            <button className="btn sm ghost" title={t("pal.openCC")} onClick={() => window.open("Command Center.html", "_blank")}>
              <Icon name="external" size={11}/>
            </button>

            {/* Notification bell */}
            <NotificationBell items={FIX_NOTIFICATIONS} onOpenAll={() => setActiveDomain("__notifications")}/>

            <LangToggle/>

            <button className="btn ghost sm" title={t("app.live")}><LiveIndicator state="live"/></button>

            <div className="vr" style={{ height: 20 }}/>

            <button className="btn sm ghost" title="Toggle theme" onClick={() => setTweak("theme", tweaks.theme === "dark" ? "light" : "dark")}>
              <Icon name={tweaks.theme === "dark" ? "circle" : "circle-o"} size={11}/>
            </button>
          </div>
        </header>

        {/* Workspace */}
        <section style={{ flex: 1, padding: 16, overflow: "hidden", minHeight: 0, display: "flex", flexDirection: "column" }}>
          {/* Meta-screens (not in a domain) */}
          {activeDomain === "__settings" && <SettingsScreen/>}
          {activeDomain === "__notifications" && <NotificationsScreen/>}

          {activeDomain === "plan" && validTab === "overview" && <PlanOverview/>}
          {activeDomain === "plan" && validTab === "protocol" && (
            <DryRunScreen
              preflightState={tweaks.preflightState}
              protocolMode={tweaks.protocolMode}
              protocolErrorLevel={tweaks.protocolErrorLevel}
              protocolLanguages={tweaks.protocolLanguages}
              protocolTemperatures={tweaks.protocolTemperatures}
              protocolAdminMode={tweaks.protocolAdminMode}
            />
          )}
          {activeDomain === "plan" && validTab === "team" && <TeamScreen/>}

          {activeDomain === "portfolio" && validTab === "projects" && <ProjectsScreen/>}
          {activeDomain === "portfolio" && validTab === "experiments" && <ExperimentsScreen/>}
          {activeDomain === "portfolio" && validTab === "runs-history" && <RunsHistoryScreen/>}
          {activeDomain === "portfolio" && validTab === "compare" && <CompareScreen/>}

          {activeDomain === "run" && validTab === "timeline" && <TimelineScreen/>}
          {activeDomain === "run" && validTab === "approvals" && <ApprovalsScreen/>}
          {activeDomain === "run" && validTab === "workspace" && <WorkspaceScreen/>}

          {activeDomain === "library" && validTab === "prompts" && <PromptsScreen/>}
          {activeDomain === "library" && validTab === "datasets" && <DatasetsScreen/>}
          {activeDomain === "library" && validTab === "notebooks" && <NotebooksScreen/>}
          {activeDomain === "library" && validTab === "model-registry" && <ModelRegistryScreen/>}
          {activeDomain === "library" && validTab === "lineage" && <LineageScreen/>}
          {activeDomain === "library" && validTab === "endpoints" && <EndpointsScreen/>}
          {activeDomain === "library" && validTab === "setup" && <SetupScreen/>}

          {activeDomain === "evidence" && validTab === "claims" && <ClaimsScreen initialView={tweaks.claimsView}/>}

          {activeDomain === "insights" && validTab === "reports" && <ReportsScreen/>}
          {activeDomain === "insights" && validTab === "cost-analytics" && <CostAnalyticsScreen/>}

          {activeDomain === "ops" && validTab === "alerts" && <AlertsScreen/>}
          {activeDomain === "ops" && validTab === "incidents" && <IncidentsScreen/>}
          {activeDomain === "ops" && validTab === "schedules" && <SchedulesScreen/>}
          {activeDomain === "ops" && validTab === "integrations" && <IntegrationsScreen/>}
          {activeDomain === "ops" && validTab === "data-health" && <DataHealthScreen/>}
          {activeDomain === "ops" && validTab === "matrix" && <StatesScreen/>}

          {activeDomain === "govern" && validTab === "budget" && <BudgetScreen/>}
          {activeDomain === "govern" && validTab === "audit" && <GovernScreen/>}
        </section>
      </main>

      {/* Command palette */}
      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} items={paletteItems}/>

      {/* Tweaks panel */}
      <TweaksPanel>
        <TweakSection title={t("tw.preview")}>
          <TweakRadio label={t("tw.theme")} value={tweaks.theme} onChange={v => setTweak("theme", v)}
            options={[{ value: "dark", label: t("tw.themeDark") }, { value: "light", label: t("tw.themeLight") }]}/>
          <TweakRadio label={t("tw.density")} value={tweaks.density} onChange={v => setTweak("density", v)}
            options={[{ value: "normal", label: t("tw.densityNormal") }, { value: "compact", label: t("tw.densityCompact") }]}/>
          <TweakRadio label={t("tw.language")} value={lang} onChange={v => setLang(v)}
            options={[{ value: "en", label: "English" }, { value: "zh-CN", label: "简体中文" }]}/>
        </TweakSection>

        <TweakSection title={t("tw.bigScreen")}>
          <TweakButton onClick={() => window.open("Command Center.html", "_blank")}>
            {t("tw.openCC")}
          </TweakButton>
          <div style={{ fontSize: 10, color: "var(--fg-faint)", lineHeight: 1.5, marginTop: 4 }}>
            {t("tw.bigScreenDesc")}
          </div>
        </TweakSection>

        <TweakSection title={t("tw.preflightSection")}>
          <TweakRadio value={tweaks.preflightState} onChange={v => setTweak("preflightState", v)}
            options={[{ value: "PASS", label: "PASS" }, { value: "WARN", label: "WARN" }, { value: "FAIL", label: "FAIL" }]}/>
          <div style={{ fontSize: 10, color: "var(--fg-faint)", lineHeight: 1.5, marginTop: 4 }}>
            {t("tw.preflightHint")}
          </div>
        </TweakSection>

        <TweakSection title={t("tw.protocolSection")}>
          <TweakRadio label={t("tw.pe.mode")} value={tweaks.protocolMode} onChange={v => setTweak("protocolMode", v)}
            options={[{ value: "form", label: "Form" }, { value: "yaml", label: "YAML" }]}/>
          <TweakRadio label={t("tw.pe.errors")} value={tweaks.protocolErrorLevel} onChange={v => setTweak("protocolErrorLevel", v)}
            options={[{ value: "none", label: t("tw.pe.errNone") }, { value: "some", label: t("tw.pe.errSome") }, { value: "many", label: t("tw.pe.errMany") }]}/>
          <TweakSlider label={t("tw.pe.langs")} value={tweaks.protocolLanguages} min={1} max={7} step={1}
            onChange={v => setTweak("protocolLanguages", v)}/>
          <TweakSlider label={t("tw.pe.temps")} value={tweaks.protocolTemperatures} min={1} max={6} step={1}
            onChange={v => setTweak("protocolTemperatures", v)}/>
          <TweakToggle label={t("tw.pe.admin")} value={tweaks.protocolAdminMode}
            onChange={v => setTweak("protocolAdminMode", v)}/>
          <div style={{ fontSize: 10, color: "var(--fg-faint)", lineHeight: 1.5, marginTop: 4 }}>
            {t("tw.pe.hint")}
          </div>
        </TweakSection>

        <TweakSection title={t("tw.claimsSection")}>
          <TweakRadio value={tweaks.claimsView} onChange={v => setTweak("claimsView", v)}
            options={[{ value: "graph", label: t("tw.claimsGraph") }, { value: "table", label: t("tw.claimsTable") }]}/>
        </TweakSection>

        <TweakSuggestionBar suggestions={[
          t("tw.sug.openCC"),
          t("tw.sug.projList"),
          t("tw.sug.cmdK"),
          t("tw.sug.compare"),
        ]}/>
      </TweaksPanel>
    </div>
  );
};

// ─── Plan Overview — brief dashboard as landing ────────
const PlanOverview = () => {
  const { t } = useI18n();
  const preflightWarns = FIX_PREFLIGHT.WARN.findings.filter(f => f.severity === "warning").length;
  return (
    <div style={{ height: "100%", overflow: "auto" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--accent)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{t("ov.kicker")}</div>
          <div style={{ fontSize: 22, fontWeight: 500, letterSpacing: "-0.01em", marginBottom: 4 }}>{t("ov.title")}</div>
          <div style={{ fontSize: 12, color: "var(--fg-muted)", display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <DigestText value={FIX_RUN.manifest_digest} label="manifest:" length={12}/>
            <span>·</span>
            <span>{t("ov.objectives")}: <span style={{ color: "var(--fg)" }}>2</span></span>
            <span>·</span>
            <span>{t("ov.team")}: <span className="mono">STANDARD</span> (8 {t("ov.roles")} · {FIX_AGENTS.length} {t("ov.agents")})</span>
            <span>·</span>
            <span>{t("ov.autonomy")}: <span className="mono" style={{ color: "var(--warn)" }}>GUARDED_AUTONOMOUS</span></span>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
          <div className="panel" style={{ padding: 14 }}>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6 }}>{t("ov.preflight")}</div>
            <PreflightBadge status="WARN"/>
            <div style={{ marginTop: 8, fontSize: 12, color: "var(--fg-muted)" }}>{preflightWarns} {t("ov.warnings")}</div>
          </div>
          <div className="panel" style={{ padding: 14 }}>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6 }}>{t("ov.runProgress")}</div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginBottom: 6 }}>
              <span style={{ fontSize: 22, fontFamily: "var(--font-mono)", fontWeight: 500 }}>{FIX_RUN.progress.tasks_done}</span>
              <span style={{ color: "var(--fg-muted)", fontSize: 12 }}>/ {FIX_RUN.progress.tasks_total} {t("ov.tasksDone")}</span>
            </div>
            <div style={{ height: 4, background: "var(--bg-sunken)", borderRadius: 2, overflow: "hidden" }}>
              <div style={{ width: `${FIX_RUN.progress.tasks_done/FIX_RUN.progress.tasks_total*100}%`, height: "100%", background: "var(--accent)" }}/>
            </div>
          </div>
          <div className="panel" style={{ padding: 14 }}>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6 }}>{t("ov.claims")}</div>
            <div style={{ display: "flex", gap: 12 }}>
              <div><span style={{ fontSize: 18, fontFamily: "var(--font-mono)", fontWeight: 500 }}>{FIX_CLAIMS.filter(c=>c.status==="VERIFIED").length}</span> <span style={{ fontSize: 11, color: "var(--fg-muted)" }}>{t("ov.verified")}</span></div>
              <div><span style={{ fontSize: 18, fontFamily: "var(--font-mono)", fontWeight: 500, color: "var(--warn)" }}>{FIX_CLAIMS.filter(c=>c.status==="DISPUTED").length}</span> <span style={{ fontSize: 11, color: "var(--fg-muted)" }}>{t("ov.disputed")}</span></div>
              <div><span style={{ fontSize: 18, fontFamily: "var(--font-mono)", fontWeight: 500, color: "var(--fg-faint)" }}>{FIX_CLAIMS.filter(c=>c.status==="PROPOSED").length}</span> <span style={{ fontSize: 11, color: "var(--fg-muted)" }}>{t("ov.proposed")}</span></div>
            </div>
          </div>
        </div>

        <div className="panel" style={{ padding: 16 }}>
          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>{t("ov.objectives")}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <ObjectiveRow id="obj_hall_rate" statement={t("ov.obj1")} status="ongoing"/>
            <ObjectiveRow id="obj_var_ranking" statement={t("ov.obj2")} status="pending"/>
          </div>
        </div>

        <div className="panel" style={{ padding: 16 }}>
          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>{t("ov.quickJump")}</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
            {[
              ["timeline", t("ov.qj.timeline"), "graph", t("ov.qj.timelineSub")],
              ["approvals", t("ov.qj.approvals"), "shield", t("ov.qj.approvalsSub")],
              ["claims", t("ov.qj.claims"), "diamond", t("ov.qj.claimsSub")],
              ["budget", t("ov.qj.budget"), "warn-tri", t("ov.qj.budgetSub")],
            ].map(([tid, label, icn, sub]) => (
              <div key={tid} style={{ padding: 12, borderRadius: 6, background: "var(--bg-raised)", border: "1px solid var(--border)", cursor: "pointer" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
                  <Icon name={icn} size={11} style={{ color: "var(--accent)" }}/>
                  <span style={{ fontSize: 12, fontWeight: 500 }}>{label}</span>
                </div>
                <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>{sub}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const ObjectiveRow = ({ id, statement, status }) => {
  const { t } = useI18n();
  const label = status === "ongoing" ? t("ov.status.ongoing") : t("ov.status.pending");
  return (
    <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 12, alignItems: "flex-start" }}>
      <Icon name={status === "ongoing" ? "spin" : "circle-o"} size={12} style={{ color: status === "ongoing" ? "var(--accent)" : "var(--fg-faint)", marginTop: 3 }}/>
      <div>
        <div style={{ fontSize: 13, lineHeight: 1.5, marginBottom: 2 }}>{statement}</div>
        <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)" }}>{id}</span>
      </div>
      <span className="chip" style={{ color: status === "ongoing" ? "var(--accent)" : "var(--fg-muted)", borderColor: status === "ongoing" ? "var(--accent-line)" : "var(--border)" }}>{label}</span>
    </div>
  );
};

Object.assign(window, { AppShell, PlanOverview });
