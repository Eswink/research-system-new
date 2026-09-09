/* Atomic components: badges, chips, digests, icons.
   All support the four-channel state encoding: shape + icon + text + color. */

const { useState, useRef, useEffect, useMemo, useCallback } = React;

// ─────────────────────────────────────────────────────────
// Icons — minimal inline SVG, 12px default, currentColor.
// Each state has its own SHAPE (P colorblind req).
// ─────────────────────────────────────────────────────────
const Icon = ({ name, size = 12, style }) => {
  const s = size;
  const props = { width: s, height: s, viewBox: "0 0 12 12", fill: "none", stroke: "currentColor", strokeWidth: 1.4, strokeLinecap: "round", strokeLinejoin: "round", style, "aria-hidden": true };
  switch (name) {
    // Status shapes
    case "check": return <svg {...props}><path d="M2.5 6.5 L5 9 L9.5 3.5"/></svg>;
    case "x": return <svg {...props}><path d="M3 3 L9 9 M9 3 L3 9"/></svg>;
    case "warn-tri": return <svg {...props}><path d="M6 1.5 L11 10.5 L1 10.5 Z"/><path d="M6 5 V7.5" strokeWidth="1.6"/><circle cx="6" cy="9" r="0.4" fill="currentColor" stroke="none"/></svg>;
    case "hex": return <svg {...props}><path d="M6 1.2 L10.2 3.6 V8.4 L6 10.8 L1.8 8.4 V3.6 Z"/></svg>;
    case "diamond": return <svg {...props}><path d="M6 1.5 L10.5 6 L6 10.5 L1.5 6 Z"/></svg>;
    case "circle-o": return <svg {...props}><circle cx="6" cy="6" r="4"/></svg>;
    case "circle": return <svg {...props}><circle cx="6" cy="6" r="4" fill="currentColor" stroke="none"/></svg>;
    case "circle-dash": return <svg {...props}><circle cx="6" cy="6" r="4" strokeDasharray="1.5 1.5"/></svg>;
    case "square": return <svg {...props}><rect x="2" y="2" width="8" height="8" rx="1"/></svg>;
    case "q": return <svg {...props}><circle cx="6" cy="6" r="4"/><path d="M4.6 5 A1.4 1.4 0 1 1 6 6.6 V7.4"/><circle cx="6" cy="9.2" r="0.35" fill="currentColor" stroke="none"/></svg>;

    case "play": return <svg {...props}><path d="M3.5 2.5 L9.5 6 L3.5 9.5 Z" fill="currentColor" stroke="none"/></svg>;
    case "pause": return <svg {...props}><rect x="3.2" y="2.8" width="1.8" height="6.4" fill="currentColor" stroke="none"/><rect x="7" y="2.8" width="1.8" height="6.4" fill="currentColor" stroke="none"/></svg>;
    case "stop": return <svg {...props}><rect x="3" y="3" width="6" height="6" fill="currentColor" stroke="none"/></svg>;
    case "fork": return <svg {...props}><circle cx="3" cy="2.5" r="1"/><circle cx="9" cy="2.5" r="1"/><circle cx="6" cy="10" r="1"/><path d="M3 3.5 V6.5 A1.5 1.5 0 0 0 4.5 8 H7.5 A1.5 1.5 0 0 0 9 6.5 V3.5"/><path d="M6 8 V9"/></svg>;
    case "copy": return <svg {...props}><rect x="4" y="4" width="6" height="6" rx="1"/><path d="M2 8 V3 A1 1 0 0 1 3 2 H8"/></svg>;
    case "external": return <svg {...props}><path d="M7 2 H10 V5"/><path d="M10 2 L5.5 6.5"/><path d="M9 7.5 V9.5 A0.5 0.5 0 0 1 8.5 10 H2.5 A0.5 0.5 0 0 1 2 9.5 V3.5 A0.5 0.5 0 0 1 2.5 3 H4.5"/></svg>;
    case "chevron-r": return <svg {...props}><path d="M4.5 2.5 L8 6 L4.5 9.5"/></svg>;
    case "chevron-d": return <svg {...props}><path d="M2.5 4.5 L6 8 L9.5 4.5"/></svg>;
    case "search": return <svg {...props}><circle cx="5" cy="5" r="3"/><path d="M7.2 7.2 L10 10"/></svg>;
    case "plus": return <svg {...props}><path d="M6 2.5 V9.5 M2.5 6 H9.5"/></svg>;
    case "lock": return <svg {...props}><rect x="2.5" y="5.5" width="7" height="5" rx="0.6"/><path d="M4 5.5 V4 A2 2 0 0 1 8 4 V5.5"/></svg>;
    case "dot": return <svg {...props}><circle cx="6" cy="6" r="2" fill="currentColor" stroke="none"/></svg>;
    case "ban": return <svg {...props}><circle cx="6" cy="6" r="4"/><path d="M3.2 3.2 L8.8 8.8"/></svg>;
    case "clock": return <svg {...props}><circle cx="6" cy="6" r="4"/><path d="M6 3.5 V6 L7.6 7.6"/></svg>;
    case "spin": return <svg {...props} style={{ ...style, animation: "spin 1s linear infinite" }}><path d="M6 2 A4 4 0 1 1 2 6" /></svg>;
    case "wifi": return <svg {...props}><path d="M1.5 4.5 A6 6 0 0 1 10.5 4.5"/><path d="M3 6.3 A4 4 0 0 1 9 6.3"/><path d="M4.5 8 A2 2 0 0 1 7.5 8"/><circle cx="6" cy="9.5" r="0.5" fill="currentColor" stroke="none"/></svg>;
    case "wifi-off": return <svg {...props}><path d="M1.5 4.5 A6 6 0 0 1 3.5 3.2"/><path d="M8.5 3.2 A6 6 0 0 1 10.5 4.5"/><path d="M4.5 8 A2 2 0 0 1 7.5 8"/><path d="M1.5 1.5 L10.5 10.5"/></svg>;
    case "shield": return <svg {...props}><path d="M6 1.5 L10 3 V6.5 C10 8.5 8 10 6 10.5 C4 10 2 8.5 2 6.5 V3 Z"/></svg>;
    case "eye-off": return <svg {...props}><path d="M2 2 L10 10"/><path d="M2.5 6.5 C4 4.5 4 4.5 6 4.5 C7 4.5 8 5 9.5 6.5"/><circle cx="6" cy="6.5" r="1.2"/></svg>;
    case "flask": return <svg {...props}><path d="M4.5 2 V4.5 L2.5 9 A1 1 0 0 0 3.5 10.5 H8.5 A1 1 0 0 0 9.5 9 L7.5 4.5 V2"/><path d="M4 2 H8"/><path d="M3.5 7 H8.5"/></svg>;
    case "book": return <svg {...props}><path d="M2 2.5 H5.5 A1 1 0 0 1 6 3 V9.5 A0.5 0.5 0 0 1 5.5 10 H2 Z"/><path d="M6 3 A1 1 0 0 1 6.5 2.5 H10 V9.5 A0.5 0.5 0 0 1 9.5 10 H6"/></svg>;
    case "graph": return <svg {...props}><circle cx="3" cy="3" r="1.2"/><circle cx="9" cy="4" r="1.2"/><circle cx="6" cy="9" r="1.2"/><path d="M4 3.4 L8 3.8"/><path d="M3.4 4 L5.4 8"/><path d="M8.4 5 L6.6 8"/></svg>;
    case "menu": return <svg {...props}><path d="M2 3.5 H10 M2 6 H10 M2 8.5 H10"/></svg>;
    default: return <svg {...props}><circle cx="6" cy="6" r="4"/></svg>;
  }
};

// ─────────────────────────────────────────────────────────
// StatusBadge — the workhorse. Four-channel encoding.
// tone: success | warn | danger | unknown | neutral | info
// shape via distinct icon; text always present.
// ─────────────────────────────────────────────────────────
const StatusBadge = ({ tone = "neutral", label, icon, dashed = false, filled = false, size = "md" }) => {
  const styles = {
    display: "inline-flex", alignItems: "center", gap: 5,
    padding: size === "sm" ? "0 5px" : "1px 7px",
    height: size === "sm" ? 16 : 18,
    borderRadius: 4,
    fontSize: size === "sm" ? 10 : 11,
    fontFamily: "var(--font-mono)",
    fontWeight: 500,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    whiteSpace: "nowrap",
    border: `1px ${dashed ? "dashed" : "solid"} var(--${tone === "neutral" ? "border" : tone}-line)`,
    background: filled ? `var(--${tone === "neutral" ? "bg-raised" : tone}-dim)` : "transparent",
    color: tone === "neutral" ? "var(--fg-muted)" : `var(--${tone})`,
  };
  return (
    <span style={styles} role="status">
      {icon && <Icon name={icon} size={10} />}
      <span>{label}</span>
    </span>
  );
};

// Semantic wrappers — CANONICAL usage
const ClaimStatusBadge = ({ status }) => {
  const map = {
    PROPOSED: { tone: "neutral", icon: "circle-dash", label: "PROPOSED", dashed: true },
    VERIFIED: { tone: "success", icon: "check", label: "VERIFIED", filled: true },
    DISPUTED: { tone: "warn", icon: "warn-tri", label: "DISPUTED", filled: true },
    REFUTED:  { tone: "danger", icon: "x", label: "REFUTED", filled: true },
  };
  return <StatusBadge {...map[status]} />;
};

const RunStateBadge = ({ state }) => {
  const map = {
    PENDING:   { tone: "neutral", icon: "circle-o", label: "PENDING" },
    RUNNING:   { tone: "info", icon: "spin", label: "RUNNING", filled: true },
    PAUSED:    { tone: "warn", icon: "pause", label: "PAUSED", filled: true },
    SUCCEEDED: { tone: "success", icon: "check", label: "SUCCEEDED", filled: true },
    FAILED:    { tone: "danger", icon: "x", label: "FAILED", filled: true },
    CANCELED:  { tone: "neutral", icon: "ban", label: "CANCELED" },
  };
  const cfg = map[state] || map.PENDING;
  // info tone → use accent
  if (cfg.tone === "info") {
    return (
      <span style={{
        display: "inline-flex", alignItems: "center", gap: 5,
        padding: "1px 7px", height: 18, borderRadius: 4,
        fontSize: 11, fontFamily: "var(--font-mono)", fontWeight: 500,
        letterSpacing: "0.04em", textTransform: "uppercase",
        border: "1px solid var(--accent-line)", background: "var(--accent-dim)", color: "var(--accent)",
      }}>
        <Icon name={cfg.icon} size={10} /> {cfg.label}
      </span>
    );
  }
  return <StatusBadge tone={cfg.tone} icon={cfg.icon} label={cfg.label} filled={cfg.filled} dashed={cfg.dashed} />;
};

const PreflightBadge = ({ status }) => {
  const map = {
    PASS: { tone: "success", icon: "check", label: "PASS", filled: true },
    WARN: { tone: "warn", icon: "warn-tri", label: "WARN", filled: true },
    FAIL: { tone: "danger", icon: "x", label: "FAIL", filled: true },
  };
  return <StatusBadge {...map[status]} />;
};

// ─────────────────────────────────────────────────────────
// ReproducibilityChip — enforces P3 hard rule.
// If system_fingerprint is null → MUST render "Configuration reproducible".
// ─────────────────────────────────────────────────────────
const ReproducibilityChip = ({ fingerprint, providerAvailable, compact = false }) => {
  // Hard rule from DTO: provider_fingerprint_available=false → unknown
  if (providerAvailable === false || !fingerprint) {
    return (
      <span title="Configuration reproducible / provider fingerprint unavailable"
            style={{
              display: "inline-flex", alignItems: "center", gap: 5,
              padding: "1px 7px", height: 18, borderRadius: 4,
              fontSize: 11, fontFamily: "var(--font-mono)",
              border: "1px dashed var(--unknown-line)",
              background: "var(--unknown-dim)",
              color: "var(--unknown)",
              whiteSpace: "nowrap",
            }}>
        <Icon name="q" size={10} />
        {compact ? "CFG-ONLY" : "Configuration reproducible"}
      </span>
    );
  }
  return (
    <span title={`Fully reproducible · fingerprint ${fingerprint}`}
          style={{
            display: "inline-flex", alignItems: "center", gap: 5,
            padding: "1px 7px", height: 18, borderRadius: 4,
            fontSize: 11, fontFamily: "var(--font-mono)",
            border: "1px solid var(--success-line)",
            background: "var(--success-dim)",
            color: "var(--success)",
            whiteSpace: "nowrap",
          }}>
      <Icon name="check" size={10} />
      {compact ? "REPRODUCIBLE" : "Fully reproducible"}
    </span>
  );
};

// ─────────────────────────────────────────────────────────
// DigestText — mono, truncated, copyable, full on hover
// ─────────────────────────────────────────────────────────
const DigestText = ({ value, prefix = true, length = 8, label, onCopy }) => {
  const [copied, setCopied] = useState(false);
  const doCopy = (e) => {
    e.stopPropagation();
    try { navigator.clipboard.writeText(value); } catch(_){}
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
    onCopy && onCopy(value);
  };
  const short = prefix && value.includes(":")
    ? value.slice(0, value.indexOf(":") + 1) + value.slice(value.indexOf(":") + 1, value.indexOf(":") + 1 + length)
    : value.slice(0, length);
  return (
    <span title={value} onClick={doCopy}
      style={{
        display: "inline-flex", alignItems: "center", gap: 4,
        fontFamily: "var(--font-mono)", fontSize: 11,
        color: "var(--fg-muted)",
        cursor: "pointer",
        padding: "1px 5px",
        borderRadius: 3,
        transition: "background 120ms",
      }}
      onMouseEnter={(e) => e.currentTarget.style.background = "var(--bg-hover)"}
      onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
    >
      {label && <span style={{ color: "var(--fg-faint)" }}>{label}</span>}
      <span>{short}{value.length > short.length && "…"}</span>
      <Icon name={copied ? "check" : "copy"} size={10} style={{ color: copied ? "var(--success)" : "var(--fg-faint)" }} />
    </span>
  );
};

// ─────────────────────────────────────────────────────────
// LiveIndicator — SSE status. Four states.
// ─────────────────────────────────────────────────────────
const LiveIndicator = ({ state = "live", behind = 0 }) => {
  const cfg = {
    live:      { color: "var(--success)", icon: "dot", label: "LIVE", pulse: true },
    reconnecting: { color: "var(--warn)", icon: "spin", label: "RECONNECTING" },
    behind:    { color: "var(--warn)", icon: "clock", label: `BEHIND ${behind}` },
    offline:   { color: "var(--fg-faint)", icon: "wifi-off", label: "OFFLINE" },
  }[state] || {};
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      fontFamily: "var(--font-mono)", fontSize: 10,
      letterSpacing: "0.08em", color: cfg.color,
    }}>
      <span style={{ position: "relative", display: "inline-flex" }}>
        <Icon name={cfg.icon} size={10} />
        {cfg.pulse && (
          <span style={{
            position: "absolute", inset: -2,
            borderRadius: "50%",
            background: cfg.color, opacity: 0.35,
            animation: "pulse 1.6s ease-out infinite",
          }} />
        )}
      </span>
      <span>{cfg.label}</span>
    </span>
  );
};

// ─────────────────────────────────────────────────────────
// GateChip — approval gate types
// ─────────────────────────────────────────────────────────
const GateChip = ({ type }) => {
  const map = {
    POLICY_GATE:   { color: "var(--accent)", label: "POLICY" },
    BUDGET_GATE:   { color: "var(--warn)", label: "BUDGET" },
    QUALITY_GATE:  { color: "var(--success)", label: "QUALITY" },
    HUMAN_GATE:    { color: "var(--fg-muted)", label: "HUMAN" },
    SECURITY_GATE: { color: "var(--danger)", label: "SECURITY" },
    PUBLISH_GATE:  { color: "var(--unknown)", label: "PUBLISH" },
  };
  const cfg = map[type] || map.POLICY_GATE;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "1px 6px", height: 18, borderRadius: 4,
      fontSize: 10, fontFamily: "var(--font-mono)",
      letterSpacing: "0.06em",
      border: `1px solid ${cfg.color}44`,
      color: cfg.color,
      background: "transparent",
    }}>
      <Icon name="shield" size={9}/> {cfg.label}
    </span>
  );
};

// ─────────────────────────────────────────────────────────
// UnknownValue — enforces P4. Never displays as 0 or —.
// ─────────────────────────────────────────────────────────
const UnknownValue = ({ hint = "estimated_cost_minor=null" }) => (
  <span title={hint} style={{
    display: "inline-flex", alignItems: "center", gap: 4,
    fontFamily: "var(--font-mono)", fontSize: 11,
    color: "var(--unknown)",
    padding: "0 4px",
  }}>
    <Icon name="q" size={10} /> UNKNOWN
  </span>
);

// ─────────────────────────────────────────────────────────
// Global keyframes helper
// ─────────────────────────────────────────────────────────
const GlobalKeyframes = () => (
  <style>{`
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes pulse {
      0%   { transform: scale(0.6); opacity: 0.6; }
      100% { transform: scale(1.8); opacity: 0; }
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(2px); } to { opacity: 1; transform: none; } }
    @keyframes stream-in {
      from { opacity: 0; transform: translateX(-4px); background: var(--accent-dim); }
      to { opacity: 1; transform: none; }
    }
  `}</style>
);

Object.assign(window, {
  Icon, StatusBadge, ClaimStatusBadge, RunStateBadge, PreflightBadge,
  ReproducibilityChip, DigestText, LiveIndicator, GateChip, UnknownValue,
  GlobalKeyframes,
});
