/* Screen 11: State Matrix — demonstrates the required state matrix.
   empty / loading / error / partial / forbidden / stale / live */

const StatesScreen = () => { const { t } = useI18n();
  const states = [
    {
      id: "empty", tone: "neutral", icon: "circle-o",
      title: t("sm.empty"),
      desc: t("sm.emptyDesc"),
      demo: <StateDemo>
        <div style={{ textAlign: "center", padding: "20px 12px" }}>
          <div style={{ display: "inline-flex", padding: 10, borderRadius: "50%", background: "var(--bg-raised)", border: "1px dashed var(--border-strong)", marginBottom: 10 }}>
            <Icon name="flask" size={16} style={{ color: "var(--fg-faint)" }}/>
          </div>
          <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 3 }}>{t("sm.demo.emptyTitle")}</div>
          <div style={{ fontSize: 11, color: "var(--fg-muted)", marginBottom: 10 }}>{t("sm.demo.emptyDesc")}</div>
          <button className="btn primary sm"><Icon name="plus" size={10}/> {t("sm.demo.emptyCta")}</button>
        </div>
      </StateDemo>
    },
    {
      id: "loading", tone: "info", icon: "spin",
      title: t("sm.loading"),
      desc: t("sm.loadingDesc"),
      demo: <StateDemo>
        <div style={{ padding: "14px 12px", display: "flex", flexDirection: "column", gap: 8 }}>
          {[0.9, 0.7, 0.85, 0.6].map((w, i) => (
            <div key={i} style={{ height: 10, width: `${w * 100}%`, background: "var(--bg-raised)", borderRadius: 3, animation: "shimmer 1.6s ease-in-out infinite", animationDelay: `${i * 0.1}s` }}/>
          ))}
        </div>
      </StateDemo>
    },
    {
      id: "error", tone: "danger", icon: "x",
      title: t("sm.error"),
      desc: t("sm.errorDesc"),
      demo: <StateDemo>
        <div style={{ padding: "14px 12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--danger)", fontSize: 12, marginBottom: 6 }}>
            <Icon name="x" size={12}/> {t("sm.demo.errTitle")}
          </div>
          <div style={{ fontSize: 11, color: "var(--fg-muted)", fontFamily: "var(--font-mono)", lineHeight: 1.5, marginBottom: 8 }}>
            error_class: <span style={{ color: "var(--danger)" }}>UPSTREAM_TIMEOUT</span><br/>
            error_message_redacted: "endpoint responded 504 after 60s (retryable=true)"
          </div>
          <button className="btn sm"><Icon name="spin" size={10}/> {t("act.retry")}</button>
        </div>
      </StateDemo>
    },
    {
      id: "partial", tone: "warn", icon: "warn-tri",
      title: t("sm.partial"),
      desc: t("sm.partialDesc"),
      demo: <StateDemo>
        <div style={{ padding: "14px 12px" }}>
          <div style={{ fontSize: 12, marginBottom: 8 }}>{t("sm.demo.partialShowing")} <span className="mono" style={{ color: "var(--warn)" }}>4/7</span> {t("sm.demo.partialLangs")}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
            <span><Icon name="check" size={9} style={{ color: "var(--success)" }}/> en · es · zh · ar</span>
            <span><Icon name="q" size={9} style={{ color: "var(--unknown)" }}/> pt · fr · ja</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 11, color: "var(--warn)", background: "var(--warn-dim)", padding: 8, borderRadius: 4 }}>
            {t("sm.demo.partialNote")}
          </div>
        </div>
      </StateDemo>
    },
    {
      id: "forbidden", tone: "danger", icon: "lock",
      title: t("sm.forbidden"),
      desc: t("sm.forbiddenDesc"),
      demo: <StateDemo>
        <div style={{ padding: "20px 12px", textAlign: "center" }}>
          <Icon name="lock" size={18} style={{ color: "var(--fg-faint)", marginBottom: 8 }}/>
          <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 3 }}>{t("sm.demo.forbiddenTitle")}</div>
          <div style={{ fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.55 }}>
            {t("sm.demo.forbiddenDesc")} <span className="mono" style={{ color: "var(--danger)" }}>budget.write.expand</span>{t("sm.demo.forbiddenDesc2")}
          </div>
        </div>
      </StateDemo>
    },
    {
      id: "stale", tone: "warn", icon: "clock",
      title: t("sm.stale"),
      desc: t("sm.staleDesc"),
      demo: <StateDemo>
        <div style={{ padding: "14px 12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "var(--warn)", marginBottom: 8 }}>
            <Icon name="clock" size={11}/> {t("sm.demo.staleTitle")}
          </div>
          <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", lineHeight: 1.55, marginBottom: 8 }}>
            last_updated: 2026-08-27T13:44:11Z<br/>
            <span style={{ color: "var(--fg-faint)" }}>~ 20 min {t("sm.demo.staleAgo")}</span>
          </div>
          <button className="btn sm"><Icon name="spin" size={10}/> {t("act.refresh")}</button>
        </div>
      </StateDemo>
    },
    {
      id: "live", tone: "success", icon: "dot",
      title: t("sm.live"),
      desc: t("sm.liveDesc"),
      demo: <StateDemo>
        <div style={{ padding: "14px 12px" }}>
          <div style={{ marginBottom: 8 }}><LiveIndicator state="live"/></div>
          <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", lineHeight: 1.7 }}>
            <div><span style={{ color: "var(--fg-faint)" }}>14:42:11</span> evidence.proposed · ev_006</div>
            <div style={{ animation: "stream-in 400ms" }}><span style={{ color: "var(--fg-faint)" }}>14:42:14</span> tool.called · pubmed.search</div>
          </div>
        </div>
      </StateDemo>
    },
  ];

  return (
    <div style={{ flex: 1, minHeight: 0, overflow: "auto" }}>
      <div style={{ padding: 16, borderBottom: "1px solid var(--border)", background: "var(--bg-panel)" }}>
        <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--accent)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>
          {t("sm.contract")}
        </div>
        <div style={{ fontSize: 15, fontWeight: 500, letterSpacing: "-0.005em" }}>{t("sm.title")}</div>
        <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 4, maxWidth: 720 }}>
          {t("sm.desc")}
        </div>
      </div>
      <div style={{ padding: 16, display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 12 }}>
        {states.map(s => (
          <div key={s.id} className="panel" style={{ overflow: "hidden" }}>
            <div style={{ padding: "10px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
              <StatusBadge tone={s.tone === "info" ? "neutral" : s.tone} icon={s.icon} label={s.title} size="sm" filled/>
              <span style={{ fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.45 }}>{s.desc}</span>
            </div>
            <div>{s.demo}</div>
          </div>
        ))}
      </div>
      <style>{`
        @keyframes shimmer {
          0%, 100% { opacity: 0.5; }
          50%      { opacity: 1; }
        }
      `}</style>
    </div>
  );
};

const StateDemo = ({ children }) => (
  <div style={{ background: "var(--bg-sunken)", minHeight: 140 }}>{children}</div>
);

Object.assign(window, { StatesScreen });
