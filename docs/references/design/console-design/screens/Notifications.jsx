/* Notifications Center — full-screen view of everything the bell shows.
   Adds filters, mark-all-read, and grouping by day. */

const NotificationsScreen = () => {
  const { t } = useI18n();
  const [filter, setFilter] = useState("all");
  const [readMap, setReadMap] = useState(() => Object.fromEntries(FIX_NOTIFICATIONS.map(n => [n.id, n.read])));

  // Extend seed to give the page density.
  const all = useMemo(() => {
    const seed = FIX_NOTIFICATIONS;
    const extra = [
      { id: "ntf_06", kind: "run", severity: "low", subject: "Run rag · adversarial · v7 succeeded task_ret_bm25", at: "2026-08-27T13:20:12Z", read: true },
      { id: "ntf_07", kind: "alert", severity: "medium", subject: "Endpoint prod-us-east latency p95 breached 1.2s SLO", at: "2026-08-27T12:12:00Z", read: false, ref: "alrt_i_02" },
      { id: "ntf_08", kind: "approval", severity: "low", subject: "Approval processed · increase_budget +$500 auto-granted", at: "2026-08-27T10:03:00Z", read: true },
      { id: "ntf_09", kind: "claim", severity: "high", subject: "Claim clm_h4_zh_delta refuted after re-run — see evidence", at: "2026-08-26T22:14:00Z", read: false, ref: "clm_h4_zh_delta" },
      { id: "ntf_10", kind: "report", severity: "low", subject: "Report weekly-med-qa compiled and posted to Slack", at: "2026-08-26T09:00:00Z", read: true },
      { id: "ntf_11", kind: "system", severity: "low", subject: "System · SSO certificate rotated (auto)", at: "2026-08-26T05:00:00Z", read: true },
      { id: "ntf_12", kind: "run", severity: "medium", subject: "Run steering · final degraded to SUPERVISED autonomy", at: "2026-08-25T18:04:00Z", read: true },
    ];
    return [...seed, ...extra];
  }, []);

  const filtered = all.filter(n => filter === "all" ? true : filter === "unread" ? !readMap[n.id] : n.kind === filter);

  const kindIcons = { alert: "warn-tri", approval: "shield", claim: "diamond", run: "play", report: "book", system: "menu" };
  const sevColors = { high: "var(--danger)", medium: "var(--warn)", low: "var(--fg-muted)" };

  const markAll = () => setReadMap(Object.fromEntries(all.map(n => [n.id, true])));
  const toggleRead = (id) => setReadMap(prev => ({ ...prev, [id]: !prev[id] }));

  // Group by day
  const groups = {};
  filtered.forEach(n => {
    const day = n.at.slice(0, 10);
    (groups[day] = groups[day] || []).push(n);
  });
  const dayKeys = Object.keys(groups).sort((a, b) => b.localeCompare(a));

  const unreadCount = all.filter(n => !readMap[n.id]).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("nc.title")} subtitle={t("nc.subtitle")}>
        <ViewSwitcher value={filter} onChange={setFilter} views={[
          { value: "all", label: `${t("nc.all")} (${all.length})` },
          { value: "unread", label: `${t("nc.unread")} (${unreadCount})` },
          { value: "alert", label: t("nc.alerts") },
          { value: "approval", label: t("nc.approvals") },
          { value: "claim", label: t("nc.claims") },
          { value: "run", label: t("nc.runs") },
        ]}/>
        <button className="btn sm ghost" onClick={markAll}><Icon name="check" size={11}/> {t("nc.markAllRead")}</button>
        <button className="btn sm"><Icon name="external" size={11}/> {t("nc.settings")}</button>
      </PageToolbar>

      {filtered.length === 0 ? (
        <EmptyState icon="check" title={t("nc.emptyTitle")} description={t("nc.emptyDesc")}/>
      ) : (
        <div className="panel" style={{ flex: 1, overflow: "auto" }}>
          {dayKeys.map(day => (
            <div key={day}>
              <div style={{
                padding: "8px 16px", borderBottom: "1px solid var(--border-subtle)",
                background: "var(--bg-sunken)",
                fontSize: 10, fontFamily: "var(--font-mono)",
                color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase",
                position: "sticky", top: 0, zIndex: 1,
              }}>{day} · {groups[day].length} {t("nc.events")}</div>
              {groups[day].map(n => {
                const unread = !readMap[n.id];
                return (
                  <div key={n.id} onClick={() => toggleRead(n.id)} style={{
                    display: "grid",
                    gridTemplateColumns: "8px 24px 90px 100px 1fr 100px 30px",
                    gap: 12, alignItems: "center",
                    padding: "10px 16px",
                    borderBottom: "1px solid var(--border-subtle)",
                    cursor: "pointer",
                    background: unread ? "var(--accent-dim)" : "transparent",
                    transition: "background 120ms",
                  }}>
                    <span style={{
                      width: 6, height: 6, borderRadius: "50%",
                      background: unread ? "var(--accent)" : "transparent",
                    }}/>
                    <Icon name={kindIcons[n.kind] || "circle-o"} size={13} style={{ color: sevColors[n.severity] }}/>
                    <span className="chip" style={{ fontSize: 9, height: 15 }}>{n.kind.toUpperCase()}</span>
                    <StatusBadge
                      tone={n.severity === "high" ? "danger" : n.severity === "medium" ? "warn" : "neutral"}
                      label={n.severity.toUpperCase()}
                      icon={n.severity === "high" ? "warn-tri" : n.severity === "medium" ? "diamond" : "circle-o"}
                      size="sm"/>
                    <span style={{ fontSize: 12, fontWeight: unread ? 500 : 400 }}>{n.subject}</span>
                    <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)" }}>{new Date(n.at).toISOString().slice(11, 16)} UTC</span>
                    <Icon name="chevron-r" size={10} style={{ color: "var(--fg-faint)" }}/>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

Object.assign(window, { NotificationsScreen });
