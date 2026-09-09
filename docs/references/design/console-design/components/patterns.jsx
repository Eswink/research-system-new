/* Interaction patterns — Drawer, Modal, CommandPalette, EmptyState,
   ContextMenu, TopToolbar, ViewSwitcher, Toast. */

// ─────────────────────────────────────────────────────────
// Drawer — right-side slide-in panel
// ─────────────────────────────────────────────────────────
const Drawer = ({ open, onClose, title, subtitle, width = 520, children, footer }) => {
  useEffect(() => {
    if (!open) return;
    const h = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  }, [open, onClose]);
  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 60,
      pointerEvents: open ? "auto" : "none",
    }}>
      <div onClick={onClose} style={{
        position: "absolute", inset: 0,
        background: "rgba(0,0,0,0.4)",
        opacity: open ? 1 : 0,
        transition: "opacity 220ms",
      }}/>
      <div style={{
        position: "absolute", top: 0, right: 0, bottom: 0,
        width, maxWidth: "94vw",
        background: "var(--bg-panel)",
        borderLeft: "1px solid var(--border)",
        boxShadow: "var(--shadow-3)",
        display: "flex", flexDirection: "column",
        transform: open ? "translateX(0)" : "translateX(100%)",
        transition: "transform 260ms cubic-bezier(0.2, 0, 0, 1)",
      }}>
        <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "flex-start", gap: 12 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            {subtitle && <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{subtitle}</div>}
            <div style={{ fontSize: 15, fontWeight: 500, letterSpacing: "-0.005em" }}>{title}</div>
          </div>
          <button className="btn sm ghost" onClick={onClose}><Icon name="x" size={11}/></button>
        </div>
        <div style={{ flex: 1, overflow: "auto", padding: 20 }}>{children}</div>
        {footer && (
          <div style={{ padding: "12px 20px", borderTop: "1px solid var(--border)", background: "var(--bg-raised)", display: "flex", alignItems: "center", gap: 8 }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// Modal — centered confirm / small dialog
// ─────────────────────────────────────────────────────────
const Modal = ({ open, onClose, title, children, footer, width = 440 }) => {
  useEffect(() => {
    if (!open) return;
    const h = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 70,
      display: "flex", alignItems: "center", justifyContent: "center",
      background: "rgba(0,0,0,0.5)",
      animation: "fadeIn 160ms ease-out",
    }} onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} style={{
        width, maxWidth: "94vw",
        background: "var(--bg-panel)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        boxShadow: "var(--shadow-3)",
      }}>
        <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center" }}>
          <div style={{ fontSize: 14, fontWeight: 500 }}>{title}</div>
          <button className="btn sm ghost" onClick={onClose} style={{ marginLeft: "auto" }}><Icon name="x" size={11}/></button>
        </div>
        <div style={{ padding: 18 }}>{children}</div>
        {footer && (
          <div style={{ padding: "12px 18px", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "flex-end", gap: 8, background: "var(--bg-raised)" }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// EmptyState — first-run / no-data placeholder
// ─────────────────────────────────────────────────────────
const EmptyState = ({ icon = "diamond", title, description, cta, secondaryCta, kicker }) => (
  <div style={{
    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
    padding: "48px 24px", textAlign: "center", gap: 8, minHeight: 240,
  }}>
    <div style={{
      width: 56, height: 56, borderRadius: 8,
      background: "var(--bg-raised)",
      border: "1px dashed var(--border-strong)",
      display: "flex", alignItems: "center", justifyContent: "center",
      color: "var(--fg-muted)", marginBottom: 12,
    }}>
      <Icon name={icon} size={22}/>
    </div>
    {kicker && <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--accent)", letterSpacing: "0.08em", textTransform: "uppercase" }}>{kicker}</div>}
    <div style={{ fontSize: 15, fontWeight: 500, letterSpacing: "-0.005em" }}>{title}</div>
    {description && <div style={{ fontSize: 12, color: "var(--fg-muted)", maxWidth: 380, lineHeight: 1.55 }}>{description}</div>}
    {(cta || secondaryCta) && (
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        {cta && <button className="btn primary" onClick={cta.onClick}>{cta.icon && <Icon name={cta.icon} size={11}/>} {cta.label}</button>}
        {secondaryCta && <button className="btn" onClick={secondaryCta.onClick}>{secondaryCta.icon && <Icon name={secondaryCta.icon} size={11}/>} {secondaryCta.label}</button>}
      </div>
    )}
  </div>
);

// ─────────────────────────────────────────────────────────
// CommandPalette — ⌘K global search / actions
// ─────────────────────────────────────────────────────────
const CommandPalette = ({ open, onClose, items = [] }) => {
  const { t } = (typeof useI18n === "function") ? useI18n() : { t: (k, f) => f ?? k };
  const [q, setQ] = useState("");
  const [hover, setHover] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setQ(""); setHover(0);
      setTimeout(() => inputRef.current?.focus(), 40);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const h = (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowDown") { e.preventDefault(); setHover(h => Math.min(filtered.length - 1, h + 1)); }
      if (e.key === "ArrowUp")   { e.preventDefault(); setHover(h => Math.max(0, h - 1)); }
      if (e.key === "Enter" && filtered[hover]) { filtered[hover].action?.(); onClose(); }
    };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  });

  const filtered = useMemo(() => {
    const s = q.toLowerCase().trim();
    if (!s) return items;
    return items.filter(it => (it.label + " " + (it.hint || "") + " " + (it.section || "")).toLowerCase().includes(s));
  }, [q, items]);

  if (!open) return null;
  const grouped = {};
  filtered.forEach(it => {
    const g = it.section || "Actions";
    if (!grouped[g]) grouped[g] = [];
    grouped[g].push(it);
  });

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 80,
      display: "flex", alignItems: "flex-start", justifyContent: "center",
      paddingTop: "12vh",
      background: "rgba(0,0,0,0.55)",
      animation: "fadeIn 140ms",
    }} onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} style={{
        width: 640, maxWidth: "94vw",
        background: "var(--bg-panel)",
        border: "1px solid var(--border)",
        borderRadius: 10,
        boxShadow: "var(--shadow-3)",
        overflow: "hidden",
        display: "flex", flexDirection: "column",
        maxHeight: "72vh",
      }}>
        <div style={{ padding: "10px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
          <Icon name="search" size={14} style={{ color: "var(--fg-faint)" }}/>
          <input ref={inputRef} value={q} onChange={e => { setQ(e.target.value); setHover(0); }}
            placeholder={t("pal.placeholder", "Type a command, search anything…")}
            style={{
              flex: 1, background: "transparent", border: "none", outline: "none",
              color: "var(--fg)", fontSize: 14,
            }}/>
          <kbd>ESC</kbd>
        </div>
        <div style={{ flex: 1, overflow: "auto", padding: 4 }}>
          {filtered.length === 0 && (
            <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--fg-faint)", fontSize: 12 }}>
              {t("pal.noMatches", "No matches. Try \"run\", \"budget\", \"approval\", or \"claim\".")}
            </div>
          )}
          {Object.entries(grouped).map(([g, its]) => (
            <div key={g}>
              <div style={{ padding: "8px 12px 4px", fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.1em", textTransform: "uppercase" }}>{g}</div>
              {its.map((it, i) => {
                const flatIdx = filtered.indexOf(it);
                const active = flatIdx === hover;
                return (
                  <div key={i} onMouseEnter={() => setHover(flatIdx)} onClick={() => { it.action?.(); onClose(); }} style={{
                    display: "flex", alignItems: "center", gap: 10,
                    padding: "8px 12px", borderRadius: 6, cursor: "pointer",
                    background: active ? "var(--bg-hover)" : "transparent",
                    borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
                    marginLeft: 4, marginRight: 4,
                  }}>
                    <Icon name={it.icon || "chevron-r"} size={12} style={{ color: active ? "var(--accent)" : "var(--fg-muted)" }}/>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, color: "var(--fg)" }}>{it.label}</div>
                      {it.hint && <div style={{ fontSize: 10, color: "var(--fg-faint)", fontFamily: "var(--font-mono)" }}>{it.hint}</div>}
                    </div>
                    {it.shortcut && <kbd>{it.shortcut}</kbd>}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
        <div style={{ padding: "8px 14px", borderTop: "1px solid var(--border)", background: "var(--bg-raised)", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", display: "flex", justifyContent: "space-between" }}>
          <span><kbd>↑</kbd> <kbd>↓</kbd> {t("pal.navigate", "navigate")} · <kbd>↵</kbd> {t("pal.select", "select")} · <kbd>esc</kbd> {t("pal.close", "close")}</span>
          <span>{filtered.length} {t("pal.results", "results")}</span>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// ContextMenu — right-click flyout
// ─────────────────────────────────────────────────────────
const ContextMenu = ({ x, y, items, onClose }) => {
  useEffect(() => {
    const h = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    document.addEventListener("click", onClose, { once: true });
    return () => document.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div style={{
      position: "fixed", left: x, top: y, zIndex: 90,
      background: "var(--bg-panel)", border: "1px solid var(--border)",
      borderRadius: 6, boxShadow: "var(--shadow-2)",
      padding: 4, minWidth: 200,
      animation: "fadeIn 120ms",
    }}>
      {items.map((it, i) => {
        if (it.divider) return <div key={i} style={{ height: 1, background: "var(--border)", margin: "4px 0" }}/>;
        return (
          <button key={i} onClick={() => { it.action?.(); onClose(); }} disabled={it.disabled}
            style={{
              display: "flex", alignItems: "center", gap: 8,
              width: "100%", padding: "6px 10px",
              background: "transparent", border: "none",
              color: it.danger ? "var(--danger)" : "var(--fg)",
              fontSize: 12, textAlign: "left", cursor: "pointer",
              opacity: it.disabled ? 0.4 : 1,
              borderRadius: 4,
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "var(--bg-hover)"}
            onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
            {it.icon && <Icon name={it.icon} size={11}/>}
            <span style={{ flex: 1 }}>{it.label}</span>
            {it.shortcut && <kbd>{it.shortcut}</kbd>}
          </button>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// ViewSwitcher — segmented control (List / Board / Timeline)
// ─────────────────────────────────────────────────────────
const ViewSwitcher = ({ views, value, onChange }) => (
  <div style={{ display: "flex", gap: 2, padding: 2, background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 6 }}>
    {views.map(v => {
      const active = v.value === value;
      return (
        <button key={v.value} onClick={() => onChange(v.value)} style={{
          display: "inline-flex", alignItems: "center", gap: 5,
          padding: "3px 10px", height: 22, borderRadius: 4,
          border: "none", cursor: "pointer",
          background: active ? "var(--bg-panel)" : "transparent",
          color: active ? "var(--fg)" : "var(--fg-muted)",
          fontFamily: "inherit", fontSize: 11, fontWeight: active ? 500 : 400,
          boxShadow: active ? "var(--shadow-1)" : "none",
        }}>
          {v.icon && <Icon name={v.icon} size={10}/>}
          {v.label}
        </button>
      );
    })}
  </div>
);

// ─────────────────────────────────────────────────────────
// NotificationBell — dropdown with unread notifications
// ─────────────────────────────────────────────────────────
const NotificationBell = ({ items = [], onOpenAll }) => {
  const { t } = (typeof useI18n === "function") ? useI18n() : { t: (k, f) => f ?? k };
  const [open, setOpen] = useState(false);
  const unread = items.filter(n => !n.read).length;
  return (
    <div style={{ position: "relative" }}>
      <button className="btn sm ghost" onClick={() => setOpen(!open)} title="Notifications">
        <Icon name="q" size={11}/>
        {unread > 0 && (
          <span style={{
            position: "absolute", top: 2, right: 2,
            width: 6, height: 6, borderRadius: "50%",
            background: "var(--danger)", boxShadow: "0 0 0 2px var(--bg-panel)",
          }}/>
        )}
      </button>
      {open && (
        <>
          <div style={{ position: "fixed", inset: 0, zIndex: 50 }} onClick={() => setOpen(false)}/>
          <div style={{
            position: "absolute", right: 0, top: 30, zIndex: 51,
            width: 380, background: "var(--bg-panel)",
            border: "1px solid var(--border)", borderRadius: 8,
            boxShadow: "var(--shadow-2)", overflow: "hidden",
            animation: "fadeIn 140ms",
          }}>
            <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: 12, fontWeight: 500 }}>{t("nt.title", "Notifications")}</span>
              <span className="chip">{unread} {t("nt.unread", "unread")}</span>
            </div>
            <div style={{ maxHeight: 380, overflow: "auto" }}>
              {items.map(n => (
                <div key={n.id} style={{
                  padding: "10px 14px",
                  borderBottom: "1px solid var(--border-subtle)",
                  background: n.read ? "transparent" : "var(--bg-raised)",
                  display: "flex", gap: 10,
                }}>
                  <div style={{
                    width: 6, height: 6, borderRadius: "50%",
                    marginTop: 6, flexShrink: 0,
                    background: n.severity === "high" ? "var(--danger)" : n.severity === "medium" ? "var(--warn)" : "var(--fg-faint)",
                  }}/>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 11, color: "var(--fg)", lineHeight: 1.45, marginBottom: 3 }}>{n.subject}</div>
                    <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                      {n.kind} · {new Date(n.at).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ padding: "8px 14px", borderTop: "1px solid var(--border)", background: "var(--bg-raised)", fontSize: 11 }}>
              <a onClick={() => onOpenAll?.()} style={{ color: "var(--accent)", cursor: "pointer" }}>{t("nt.openAll", "View all notifications →")}</a>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// WorkspaceSwitcher — dropdown for multi-tenant
// ─────────────────────────────────────────────────────────
const WorkspaceSwitcher = ({ workspaces }) => {
  const { t } = (typeof useI18n === "function") ? useI18n() : { t: (k, f) => f ?? k };
  const [open, setOpen] = useState(false);
  const cur = workspaces.find(w => w.current) || workspaces[0];
  return (
    <div style={{ position: "relative" }}>
      <button onClick={() => setOpen(!open)} style={{
        display: "flex", alignItems: "center", gap: 8,
        padding: "5px 10px", height: 26,
        background: "var(--bg-raised)", border: "1px solid var(--border)",
        borderRadius: 6, cursor: "pointer",
        fontSize: 11, color: "var(--fg)",
      }}>
        <div style={{ width: 14, height: 14, borderRadius: 3, background: "linear-gradient(135deg, var(--accent), #6BA1FF)" }}/>
        <span style={{ fontWeight: 500 }}>{cur.name}</span>
        <Icon name="chevron-d" size={9} style={{ color: "var(--fg-faint)" }}/>
      </button>
      {open && (
        <>
          <div style={{ position: "fixed", inset: 0, zIndex: 50 }} onClick={() => setOpen(false)}/>
          <div style={{
            position: "absolute", left: 0, right: 0, top: 32, zIndex: 51,
            background: "var(--bg-panel)",
            border: "1px solid var(--border)", borderRadius: 8,
            boxShadow: "var(--shadow-2)", overflow: "hidden",
            animation: "fadeIn 140ms",
          }}>
            <div style={{ padding: "8px 12px 4px", fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase" }}>{t("ws2.workspaces", "Workspaces")}</div>
            {workspaces.map(w => (
              <button key={w.id} onClick={() => setOpen(false)} style={{
                display: "flex", alignItems: "flex-start", gap: 10, width: "100%",
                padding: "8px 12px", background: "transparent", border: "none", cursor: "pointer",
                fontSize: 11, color: "var(--fg)", textAlign: "left",
              }}>
                <div style={{
                  width: 22, height: 22, borderRadius: 4, flexShrink: 0, marginTop: 1,
                  background: "linear-gradient(135deg, var(--accent), #6BA1FF)",
                }}/>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{w.name}</div>
                  <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", lineHeight: 1.5, wordBreak: "break-word" }}>{w.role} · {w.members} · {w.plan}</div>
                </div>
                {w.current && <Icon name="check" size={11} style={{ color: "var(--accent)", flexShrink: 0, marginTop: 4 }}/>}
              </button>
            ))}
            <div style={{ borderTop: "1px solid var(--border)", padding: 6 }}>
              <button className="btn sm ghost" style={{ width: "100%", justifyContent: "flex-start" }}><Icon name="plus" size={10}/> {t("ws2.new", "New workspace")}</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// QuickCreate — plus button dropdown
// ─────────────────────────────────────────────────────────
const QuickCreate = ({ onCreate }) => {
  const [open, setOpen] = useState(false);
  // useI18n falls back to identity when there's no provider — safe to call
  // unconditionally so this component works standalone (e.g. in Command Center).
  const { t } = (typeof useI18n === "function") ? useI18n() : { t: (k, f) => f ?? k };
  const opts = [
    { id: "project",    label: t("qc.newProject",    "New Project"),    icon: "hex",      shortcut: "P" },
    { id: "experiment", label: t("qc.newExperiment", "New Experiment"), icon: "flask",    shortcut: "E" },
    { id: "prompt",     label: t("qc.newPrompt",     "New Prompt"),     icon: "book",     shortcut: "R" },
    { id: "notebook",   label: t("qc.newNotebook",   "New Notebook"),   icon: "book",     shortcut: "N" },
    { id: "alert",      label: t("qc.newAlert",      "New Alert Rule"), icon: "warn-tri", shortcut: "A" },
    { id: "schedule",   label: t("qc.newSchedule",   "New Schedule"),   icon: "clock",    shortcut: "S" },
  ];
  return (
    <div style={{ position: "relative" }}>
      <button className="btn sm primary" onClick={() => setOpen(!open)}>
        <Icon name="plus" size={11}/> {t("act.create", "Create")}
      </button>
      {open && (
        <>
          <div style={{ position: "fixed", inset: 0, zIndex: 50 }} onClick={() => setOpen(false)}/>
          <div style={{
            position: "absolute", right: 0, top: 28, zIndex: 51,
            width: 240, background: "var(--bg-panel)",
            border: "1px solid var(--border)", borderRadius: 8,
            boxShadow: "var(--shadow-2)",
            padding: 4, animation: "fadeIn 140ms",
          }}>
            {opts.map(o => (
              <button key={o.id} onClick={() => { onCreate?.(o.id); setOpen(false); }} style={{
                display: "flex", alignItems: "center", gap: 10, width: "100%",
                padding: "7px 10px", background: "transparent", border: "none", cursor: "pointer",
                fontSize: 12, color: "var(--fg)", textAlign: "left", borderRadius: 4,
              }}
                onMouseEnter={(e) => e.currentTarget.style.background = "var(--bg-hover)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
                <Icon name={o.icon} size={11} style={{ color: "var(--accent)" }}/>
                <span style={{ flex: 1 }}>{o.label}</span>
                <kbd>{o.shortcut}</kbd>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// FormRow / FormField — for CRUD drawers
// ─────────────────────────────────────────────────────────
const FormRow = ({ label, hint, required, children }) => (
  <div style={{ marginBottom: 16 }}>
    <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 6 }}>
      <label style={{ fontSize: 11, color: "var(--fg-muted)", fontWeight: 500, letterSpacing: "0.02em" }}>
        {label} {required && <span style={{ color: "var(--danger)" }}>*</span>}
      </label>
      {hint && <span style={{ fontSize: 10, color: "var(--fg-faint)", fontFamily: "var(--font-mono)" }}>{hint}</span>}
    </div>
    {children}
  </div>
);

const TextInput = ({ value, onChange, placeholder, mono, ...rest }) => (
  <input value={value} onChange={e => onChange?.(e.target.value)} placeholder={placeholder}
    style={{
      width: "100%", height: 32,
      padding: "0 10px",
      background: "var(--bg-raised)",
      border: "1px solid var(--border)",
      borderRadius: 6,
      color: "var(--fg)",
      fontSize: 13,
      fontFamily: mono ? "var(--font-mono)" : "inherit",
      outline: "none",
    }}
    onFocus={(e) => e.currentTarget.style.borderColor = "var(--accent)"}
    onBlur={(e) => e.currentTarget.style.borderColor = "var(--border)"}
    {...rest}/>
);

const TextArea = ({ value, onChange, rows = 3, mono, placeholder }) => (
  <textarea value={value} onChange={e => onChange?.(e.target.value)} rows={rows} placeholder={placeholder}
    style={{
      width: "100%", padding: 10,
      background: "var(--bg-raised)",
      border: "1px solid var(--border)",
      borderRadius: 6,
      color: "var(--fg)",
      fontSize: 12,
      fontFamily: mono ? "var(--font-mono)" : "inherit",
      lineHeight: 1.5, resize: "vertical",
      outline: "none",
    }}
    onFocus={(e) => e.currentTarget.style.borderColor = "var(--accent)"}
    onBlur={(e) => e.currentTarget.style.borderColor = "var(--border)"}/>
);

const Select = ({ value, onChange, options }) => (
  <select value={value} onChange={e => onChange?.(e.target.value)}
    style={{
      width: "100%", height: 32,
      padding: "0 10px",
      background: "var(--bg-raised)",
      border: "1px solid var(--border)",
      borderRadius: 6,
      color: "var(--fg)",
      fontSize: 12, fontFamily: "inherit",
      outline: "none",
    }}>
    {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
  </select>
);

const TagInput = ({ tags = [], onChange }) => {
  const [input, setInput] = useState("");
  const add = () => {
    if (!input.trim()) return;
    onChange?.([...tags, input.trim()]);
    setInput("");
  };
  return (
    <div style={{
      minHeight: 32, padding: 4,
      background: "var(--bg-raised)",
      border: "1px solid var(--border)",
      borderRadius: 6,
      display: "flex", flexWrap: "wrap", alignItems: "center", gap: 4,
    }}>
      {tags.map((t, i) => (
        <span key={i} className="chip" style={{ background: "var(--accent-dim)", color: "var(--accent)", borderColor: "var(--accent-line)" }}>
          {t}
          <button onClick={() => onChange?.(tags.filter((_, j) => j !== i))} style={{ background: "transparent", border: "none", color: "inherit", cursor: "pointer", padding: 0, marginLeft: 2 }}><Icon name="x" size={8}/></button>
        </span>
      ))}
      <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && (e.preventDefault(), add())}
        placeholder={tags.length ? "" : "Add tag…"}
        style={{ flex: 1, minWidth: 60, background: "transparent", border: "none", outline: "none", color: "var(--fg)", fontSize: 12, padding: "0 4px", height: 22 }}/>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// Toolbar / SearchBar — reusable page header pattern
// ─────────────────────────────────────────────────────────
const PageToolbar = ({ title, subtitle, children, actions }) => (
  <div style={{ display: "flex", alignItems: "flex-end", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
    <div>
      {subtitle && <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--accent)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{subtitle}</div>}
      <div style={{ fontSize: 18, fontWeight: 500, letterSpacing: "-0.01em" }}>{title}</div>
    </div>
    <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
      {children}
    </div>
    {actions && <div style={{ display: "flex", gap: 6 }}>{actions}</div>}
  </div>
);

const SearchInput = ({ value, onChange, placeholder = "Filter…", width = 200 }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "0 10px", height: 26, background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 6, width }}>
    <Icon name="search" size={11} style={{ color: "var(--fg-faint)" }}/>
    <input value={value} onChange={e => onChange?.(e.target.value)} placeholder={placeholder}
      style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: "var(--fg)", fontSize: 11 }}/>
  </div>
);

// ─────────────────────────────────────────────────────────
// TrendBadge — inline percent delta w/ up/down triangle
// ─────────────────────────────────────────────────────────
const TrendBadge = ({ delta, inverted = false, format = (v) => `${v > 0 ? "+" : ""}${v.toFixed(1)}%` }) => {
  const good = inverted ? delta < 0 : delta > 0;
  const color = delta === 0 ? "var(--fg-muted)" : good ? "var(--success)" : "var(--danger)";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 3,
      color, fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 500,
    }}>
      {delta > 0 ? "▲" : delta < 0 ? "▼" : "→"} {format(Math.abs(delta))}
    </span>
  );
};

// ─────────────────────────────────────────────────────────
// FilterChips — dismissable filter pills
// ─────────────────────────────────────────────────────────
const FilterChips = ({ filters, onRemove }) => filters.length === 0 ? null : (
  <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
    {filters.map(f => (
      <span key={f.key} className="chip" style={{ background: "var(--accent-dim)", color: "var(--accent)", borderColor: "var(--accent-line)" }}>
        <span style={{ color: "var(--fg-faint)" }}>{f.field}:</span> {f.value}
        <button onClick={() => onRemove?.(f.key)} style={{ background: "transparent", border: "none", color: "inherit", cursor: "pointer", padding: 0, marginLeft: 2 }}><Icon name="x" size={8}/></button>
      </span>
    ))}
  </div>
);

Object.assign(window, {
  Drawer, Modal, EmptyState, CommandPalette, ContextMenu,
  ViewSwitcher, NotificationBell, WorkspaceSwitcher, QuickCreate,
  FormRow, TextInput, TextArea, Select, TagInput,
  PageToolbar, SearchInput, TrendBadge, FilterChips,
});
