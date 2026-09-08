/* Protocol Editor — chrome, banners, section nav, action bar, YAML view. */

// ─── Chrome: title + Segmented toggle + templates ────
const EditorChrome = ({ mode, setMode, dirty, onTemplates }) => {
  const { t } = useI18n();
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      padding: "8px 10px 8px 12px", borderBottom: "1px solid var(--border)",
      flexShrink: 0, minWidth: 0,
    }}>
      <Icon name="book" size={12} style={{ color: "var(--fg-muted)", flexShrink: 0 }}/>
      <span style={{ fontSize: 12, fontWeight: 500, flexShrink: 0 }}>protocol.yaml</span>
      {dirty && <span style={{
        fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--warn)",
        letterSpacing: "0.06em", padding: "1px 6px",
        background: "var(--warn-dim)", border: "1px solid var(--warn-line)",
        borderRadius: 3, flexShrink: 0,
      }}>DIRTY</span>}

      {/* Segmented toggle */}
      <div style={{ marginLeft: "auto", display: "flex", gap: 4, alignItems: "center", flexShrink: 0 }}>
        <SegmentedToggle
          value={mode}
          onChange={setMode}
          options={[
            { value: "form",  icon: "edit",    label: t("pe.mode.form") },
            { value: "yaml",  icon: "code",    label: t("pe.mode.yaml") },
          ]}
        />
        <div className="vr" style={{ height: 16 }}/>
        <button className="btn sm ghost" onClick={onTemplates} title={t("pe.templates.tip")} style={{ padding: "0 6px" }}>
          <Icon name="copy" size={10}/> {t("pe.templates")}
          <Icon name="chevron-d" size={9}/>
        </button>
        <button className="btn sm ghost" title={t("pe.diff.tip")} style={{ padding: "0 6px" }}>
          <Icon name="fork" size={10}/>
        </button>
        <button className="btn sm ghost" title={t("pe.validate.tip")} style={{ padding: "0 6px" }}>
          <Icon name="check" size={10}/>
        </button>
      </div>
    </div>
  );
};

// ─── Segmented toggle ────────────────────────────────
const SegmentedToggle = ({ value, onChange, options }) => (
  <div style={{
    display: "inline-flex", padding: 2, gap: 2,
    background: "var(--bg-sunken)",
    border: "1px solid var(--border)",
    borderRadius: 6,
  }}>
    {options.map(opt => {
      const active = opt.value === value;
      return (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className="btn sm ghost"
          style={{
            height: 22, padding: "0 10px",
            background: active ? "var(--bg-panel)" : "transparent",
            border: active ? "1px solid var(--border-strong)" : "1px solid transparent",
            color: active ? "var(--fg)" : "var(--fg-muted)",
            fontWeight: active ? 500 : 400,
            boxShadow: active ? "var(--shadow-1)" : "none",
          }}
        >
          <PECustomIcon name={opt.icon}/> {opt.label}
        </button>
      );
    })}
  </div>
);

// Custom small icons for the toggle
const PECustomIcon = ({ name }) => {
  const props = { width: 10, height: 10, viewBox: "0 0 10 10", fill: "none", stroke: "currentColor", strokeWidth: 1.4, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (name) {
    case "edit": return <svg {...props}><path d="M6 2 L8 4 L4 8 L1.5 8.5 L2 6 Z"/></svg>;
    case "code": return <svg {...props}><path d="M4 2.5 L1.5 5 L4 7.5"/><path d="M6 2.5 L8.5 5 L6 7.5"/></svg>;
    default: return <svg {...props}></svg>;
  }
};

// ─── Digest banner (dirty warning) ───────────────────
const DigestBanner = () => {
  const { t } = useI18n();
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      padding: "8px 14px",
      background: "var(--warn-dim)",
      borderBottom: "1px solid var(--warn-line)",
      fontSize: 11, color: "var(--warn)",
      flexShrink: 0,
    }}>
      <Icon name="warn-tri" size={11} style={{ flexShrink: 0 }}/>
      <span style={{ lineHeight: 1.45 }}>
        <strong style={{ fontWeight: 500 }}>{t("pe.digest.warn")}</strong>{" "}
        <span style={{ opacity: 0.85 }}>{t("pe.digest.detail")}</span>{" "}
        <span className="mono" style={{ fontSize: 10, opacity: 0.85 }}>
          37b2c9… → <span style={{ color: "var(--warn)" }}>dirty</span>
        </span>
      </span>
    </div>
  );
};

// ─── Error banner ─────────────────────────────────────
const ErrorBanner = ({ errors, onJump }) => {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(false);
  return (
    <div style={{
      background: "var(--danger-dim)",
      borderBottom: "1px solid var(--danger-line)",
      flexShrink: 0,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 14px", fontSize: 11, color: "var(--danger)" }}>
        <Icon name="x" size={11} style={{ flexShrink: 0 }}/>
        <span><strong style={{ fontWeight: 500 }}>{errors.length} {t("pe.err.block")}</strong> {t("pe.err.msg")}</span>
        <button className="btn sm ghost" style={{ marginLeft: "auto", color: "var(--danger)", height: 20, padding: "0 6px" }}
          onClick={() => setExpanded(v => !v)}>
          {expanded ? t("pe.err.collapse") : t("pe.err.expand")}
          <Icon name={expanded ? "chevron-d" : "chevron-r"} size={9}/>
        </button>
      </div>
      {expanded && (
        <div style={{ padding: "6px 14px 10px", display: "flex", flexDirection: "column", gap: 4 }}>
          {errors.map((e, i) => (
            <button key={i} onClick={() => onJump(e.section)}
              className="btn sm ghost"
              style={{
                justifyContent: "flex-start", height: "auto", padding: "4px 8px",
                background: "transparent", border: "1px solid var(--danger-line)",
                color: "var(--fg)", fontSize: 11, whiteSpace: "normal", textAlign: "left",
              }}>
              <span className="mono" style={{ color: "var(--danger)", flexShrink: 0 }}>{e.code}</span>
              <span style={{ color: "var(--fg-muted)" }}>·</span>
              <span className="mono" style={{ color: "var(--fg-faint)", fontSize: 10, flexShrink: 0 }}>{e.path}</span>
              <span style={{ color: "var(--fg-muted)" }}>·</span>
              <span>{e.message}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Section nav (left) ──────────────────────────────
const SectionNav = ({ active, onChange, errorsBySection, adminMode }) => {
  const { t } = useI18n();
  const sections = [
    { id: "manifest",   labelKey: "pe.sec.manifest",   icon: "shield" },
    { id: "objectives", labelKey: "pe.sec.objectives", icon: "flask" },
    { id: "team",       labelKey: "pe.sec.team",       icon: "hex" },
    { id: "evaluation", labelKey: "pe.sec.evaluation", icon: "graph" },
    { id: "budget",     labelKey: "pe.sec.budget",     icon: "diamond" },
    { id: "gates",      labelKey: "pe.sec.gates",      icon: "circle-o" },
    { id: "policy",     labelKey: "pe.sec.policy",     icon: "lock", locked: !adminMode },
  ];
  const totalErrors = Object.values(errorsBySection).reduce((s, x) => s + x.errors, 0);
  const totalWarns = Object.values(errorsBySection).reduce((s, x) => s + x.warnings, 0);

  return (
    <div style={{
      borderRight: "1px solid var(--border)",
      background: "var(--bg-sunken)",
      display: "flex", flexDirection: "column",
      minHeight: 0,
    }}>
      <div style={{
        fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)",
        letterSpacing: "0.1em", textTransform: "uppercase",
        padding: "10px 12px 6px",
      }}>
        {t("pe.nav.header")}
      </div>
      <div style={{ flex: 1, overflow: "auto" }}>
        {sections.map(s => {
          const isActive = s.id === active;
          const errs = errorsBySection[s.id]?.errors || 0;
          const warns = errorsBySection[s.id]?.warnings || 0;
          return (
            <button
              key={s.id}
              onClick={() => onChange(s.id)}
              style={{
                display: "grid",
                gridTemplateColumns: "12px 1fr auto",
                gap: 8, alignItems: "center",
                width: "100%",
                padding: "7px 12px",
                border: "none", background: isActive ? "var(--bg-panel)" : "transparent",
                borderLeft: `2px solid ${isActive ? "var(--accent)" : "transparent"}`,
                color: isActive ? "var(--fg)" : "var(--fg-muted)",
                fontSize: 12,
                cursor: "pointer",
                textAlign: "left",
                fontFamily: "inherit",
              }}
              onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = "var(--bg-hover)"; }}
              onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = "transparent"; }}
            >
              <Icon name={s.icon} size={11}/>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t(s.labelKey)}</span>
              <span style={{ display: "flex", gap: 3 }}>
                {errs > 0 && <ErrCount tone="danger" n={errs}/>}
                {warns > 0 && errs === 0 && <ErrCount tone="warn" n={warns}/>}
                {s.locked && <Icon name="lock" size={9} style={{ color: "var(--fg-faint)" }}/>}
              </span>
            </button>
          );
        })}
      </div>
      {/* Summary */}
      <div style={{
        borderTop: "1px solid var(--border)",
        padding: "8px 12px",
        display: "flex", flexDirection: "column", gap: 4,
        fontSize: 10, fontFamily: "var(--font-mono)",
        color: "var(--fg-faint)",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>{t("pe.nav.errors")}</span>
          <span style={{ color: totalErrors > 0 ? "var(--danger)" : "var(--success)" }}>{totalErrors}</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>{t("pe.nav.warnings")}</span>
          <span style={{ color: totalWarns > 0 ? "var(--warn)" : "var(--fg-faint)" }}>{totalWarns}</span>
        </div>
      </div>
    </div>
  );
};

const ErrCount = ({ tone, n }) => (
  <span style={{
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    minWidth: 14, height: 14, padding: "0 4px",
    borderRadius: 7,
    background: `var(--${tone}-dim)`,
    border: `1px solid var(--${tone}-line)`,
    color: `var(--${tone})`,
    fontSize: 9, fontFamily: "var(--font-mono)", fontWeight: 500,
  }}>{n}</span>
);

// ─── Action bar (sticky bottom) ──────────────────────
const ActionBar = ({ dirty, canApply, errorCount, warnCount, onDiscard, onApply }) => {
  const { t } = useI18n();
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10,
      padding: "8px 12px",
      borderTop: "1px solid var(--border)",
      background: "var(--bg-raised)",
      flexShrink: 0,
    }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 11 }}>
        {!dirty ? (
          <span style={{ color: "var(--success)", display: "flex", alignItems: "center", gap: 4 }}>
            <Icon name="check" size={10}/> {t("pe.bar.saved")}
          </span>
        ) : errorCount > 0 ? (
          <span style={{ color: "var(--danger)", display: "flex", alignItems: "center", gap: 4 }}>
            <Icon name="x" size={10}/> {errorCount} {t("pe.bar.errors")}
          </span>
        ) : warnCount > 0 ? (
          <span style={{ color: "var(--warn)", display: "flex", alignItems: "center", gap: 4 }}>
            <Icon name="warn-tri" size={10}/> {warnCount} {t("pe.bar.warnings")} · {t("pe.bar.applyOk")}
          </span>
        ) : (
          <span style={{ color: "var(--accent)", display: "flex", alignItems: "center", gap: 4 }}>
            <Icon name="dot" size={10}/> {t("pe.bar.dirty")}
          </span>
        )}
      </div>
      <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
        <button className="btn sm" onClick={onDiscard} disabled={!dirty}>
          {t("pe.bar.discard")}
        </button>
        <button className="btn sm primary" onClick={onApply} disabled={!canApply}
          aria-disabled={!canApply} title={canApply ? "" : errorCount > 0 ? t("pe.bar.applyBlockedErr") : t("pe.bar.applyBlockedNoChange")}>
          <Icon name="check" size={10}/> {t("pe.bar.apply")}
        </button>
      </div>
    </div>
  );
};

// ─── Template picker (dropdown) ──────────────────────
const TemplatePicker = ({ onPick, onClose }) => {
  const { t } = useI18n();
  const items = [
    { id: "prior_study", icon: "book", label: t("pe.tmpl.prior"),    desc: t("pe.tmpl.priorDesc") },
    { id: "stat_heavy",  icon: "shield", label: t("pe.tmpl.stat"),    desc: t("pe.tmpl.statDesc") },
    { id: "minimal",     icon: "flask", label: t("pe.tmpl.minimal"), desc: t("pe.tmpl.minimalDesc") },
    { id: "reset",       icon: "ban",   label: t("pe.tmpl.reset"),   desc: t("pe.tmpl.resetDesc") },
  ];
  return (
    <div style={{
      position: "relative", flexShrink: 0,
      background: "var(--bg-raised)",
      borderBottom: "1px solid var(--border)",
    }}>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "6px 12px", fontSize: 10, fontFamily: "var(--font-mono)",
        color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <span>{t("pe.tmpl.header")}</span>
        <button className="btn sm ghost" style={{ height: 18, padding: "0 6px" }} onClick={onClose}>
          <Icon name="x" size={9}/>
        </button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, padding: 8 }}>
        {items.map(item => (
          <button
            key={item.id}
            onClick={() => onPick(item.id)}
            style={{
              display: "flex", gap: 8, alignItems: "flex-start",
              padding: "8px 10px", background: "var(--bg-panel)",
              border: "1px solid var(--border)", borderRadius: 6,
              cursor: "pointer", color: "var(--fg)",
              textAlign: "left", fontFamily: "inherit",
            }}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = "var(--accent-line)"}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = "var(--border)"}
          >
            <Icon name={item.icon} size={12} style={{ color: "var(--fg-muted)", marginTop: 2, flexShrink: 0 }}/>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 2 }}>{item.label}</div>
              <div style={{ fontSize: 10, color: "var(--fg-faint)", lineHeight: 1.45 }}>{item.desc}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

// ─── YAML view (read-only render of current state) ───
const YamlView = ({ text }) => (
  <div style={{ flex: 1, overflow: "auto", padding: 12, background: "var(--bg-sunken)", minHeight: 0 }}>
    <pre style={{
      margin: 0, fontFamily: "var(--font-mono)", fontSize: 12,
      lineHeight: 1.65, color: "var(--fg-muted)",
    }}>{text.split("\n").map((line, i) => {
      const kwMatch = line.match(/^(\s*)([\w_]+):/);
      const commentMatch = line.match(/(.*)(#.*)$/);
      let content;
      if (commentMatch) {
        content = (<><span>{commentMatch[1]}</span><span style={{ color: "var(--fg-faint)", fontStyle: "italic" }}>{commentMatch[2]}</span></>);
      } else if (kwMatch) {
        const [, indent, key] = kwMatch;
        const rest = line.slice(indent.length + key.length + 1);
        content = (<><span>{indent}</span><span style={{ color: "var(--accent)" }}>{key}</span>:<span style={{ color: "var(--fg)" }}>{rest}</span></>);
      } else {
        content = line;
      }
      return (
        <div key={i} style={{ display: "flex", gap: 12 }}>
          <span style={{ color: "var(--fg-faint)", opacity: 0.5, userSelect: "none", width: 26, textAlign: "right", flexShrink: 0 }}>{i + 1}</span>
          <span style={{ whiteSpace: "pre" }}>{content}</span>
        </div>
      );
    })}</pre>
  </div>
);

// ─── Form field shell with label + tooltip + error ──
const Field = ({ label, hint, tooltip, error, children, locked, badge }) => (
  <div style={{ marginBottom: 14 }}>
    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 5 }}>
      <label style={{ fontSize: 11, color: "var(--fg-muted)", letterSpacing: "0.02em" }}>{label}</label>
      {tooltip && <TooltipIcon text={tooltip}/>}
      {locked && <Icon name="lock" size={9} style={{ color: "var(--fg-faint)" }}/>}
      {badge}
    </div>
    {children}
    {error && (
      <div style={{ marginTop: 4, fontSize: 10, color: "var(--danger)", fontFamily: "var(--font-mono)", display: "flex", gap: 4, alignItems: "flex-start" }}>
        <Icon name="x" size={9} style={{ marginTop: 1 }}/>
        <span><span style={{ opacity: 0.75 }}>{error.code}</span> · {error.message}</span>
      </div>
    )}
    {hint && !error && (
      <div style={{ marginTop: 4, fontSize: 10, color: "var(--fg-faint)", lineHeight: 1.4 }}>{hint}</div>
    )}
  </div>
);

const TooltipIcon = ({ text }) => {
  const [open, setOpen] = useState(false);
  return (
    <span style={{ position: "relative" }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <Icon name="q" size={10} style={{ color: "var(--fg-faint)", cursor: "help" }}/>
      {open && (
        <div style={{
          position: "absolute", bottom: "calc(100% + 6px)", left: -8,
          background: "var(--bg-panel)",
          border: "1px solid var(--border-strong)",
          borderRadius: 6, padding: "8px 10px",
          fontSize: 11, color: "var(--fg-muted)",
          width: 260, boxShadow: "var(--shadow-2)",
          zIndex: 100, lineHeight: 1.5,
          fontWeight: 400, letterSpacing: 0,
        }}>{text}</div>
      )}
    </span>
  );
};

// ─── Section header ───────────────────────────────────
const SectionHeader = ({ title, subtitle, extra }) => (
  <div style={{
    display: "flex", alignItems: "flex-start", justifyContent: "space-between",
    gap: 12, marginBottom: 16, paddingBottom: 10,
    borderBottom: "1px solid var(--border-subtle)",
  }}>
    <div>
      <div style={{ fontSize: 15, fontWeight: 500, letterSpacing: "-0.005em", marginBottom: 2 }}>{title}</div>
      {subtitle && <div style={{ fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.5 }}>{subtitle}</div>}
    </div>
    {extra}
  </div>
);

// Input helpers
const INPUT = {
  width: "100%", height: 28, padding: "0 10px",
  background: "var(--bg-sunken)", color: "var(--fg)",
  border: "1px solid var(--border)", borderRadius: 6,
  fontSize: 12, outline: "none",
  fontFamily: "inherit",
};
const INPUT_ERR = { ...INPUT, borderColor: "var(--danger-line)", background: "var(--danger-dim)" };
const INPUT_MONO = { ...INPUT, fontFamily: "var(--font-mono)" };

Object.assign(window, {
  EditorChrome, SegmentedToggle, DigestBanner, ErrorBanner,
  SectionNav, ActionBar, TemplatePicker, YamlView,
  Field, TooltipIcon, SectionHeader,
  INPUT, INPUT_ERR, INPUT_MONO,
});
