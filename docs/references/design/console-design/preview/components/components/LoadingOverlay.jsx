/* LoadingOverlay — cinematic boot / locale-switch curtain.
   Aesthetic: research-console, not marketing.
   Composition:
     · full-viewport dim scrim
     · centered "instrument panel" card
     · animated hex/diamond logo (spins slowly, pulses)
     · scanning line sweep over a mono-lattice grid backdrop
     · four-line boot log that types character-by-character
     · progress bar wired to those steps
   Two modes:
     · mode="boot"   → 1200ms full ceremony on first paint
     · mode="switch" → 700ms lighter version during locale swap
   Auto-dismisses; parent doesn't need to control lifecycle beyond mount.
*/

const LoadingOverlay = ({ mode = "boot", onDone }) => {
  const { t } = (typeof useI18n === "function") ? useI18n() : { t: (k) => k };
  const isSwitch = mode === "switch";

  const steps = isSwitch
    ? [t("load.step.locale"), t("load.step.ready")]
    : [
        t("load.step.tokens"),
        t("load.step.fixtures"),
        t("load.step.streams"),
        t("load.step.ready"),
      ];

  const totalDuration = isSwitch ? 700 : 1200;
  const perStep = totalDuration / steps.length;

  const [phase, setPhase] = useState(0);       // step index driving progress
  const [typed, setTyped] = useState("");      // current step's typewriter text
  const [exiting, setExiting] = useState(false);

  // Step scheduler
  useEffect(() => {
    const timers = [];
    steps.forEach((_, i) => {
      timers.push(setTimeout(() => setPhase(i), i * perStep));
    });
    timers.push(setTimeout(() => setExiting(true), totalDuration - 120));
    timers.push(setTimeout(() => { onDone && onDone(); }, totalDuration));
    return () => timers.forEach(clearTimeout);
    // eslint-disable-next-line
  }, []);

  // Typewriter for the currently-active step label
  useEffect(() => {
    const target = steps[phase] || "";
    setTyped("");
    const chars = Array.from(target);
    const step = Math.max(14, Math.floor((perStep * 0.7) / Math.max(chars.length, 1)));
    const timers = [];
    chars.forEach((_, i) => {
      timers.push(setTimeout(() => setTyped(target.slice(0, i + 1)), i * step));
    });
    return () => timers.forEach(clearTimeout);
    // eslint-disable-next-line
  }, [phase]);

  const progress = ((phase + 1) / steps.length) * 100;
  const label = isSwitch ? t("load.switch") : t("load.boot");

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          "radial-gradient(ellipse at center, rgba(11,13,16,0.86) 0%, rgba(11,13,16,0.98) 60%)",
        backdropFilter: "blur(6px)",
        WebkitBackdropFilter: "blur(6px)",
        opacity: exiting ? 0 : 1,
        transition: "opacity 220ms cubic-bezier(0.2,0,0,1)",
        pointerEvents: exiting ? "none" : "auto",
      }}
    >
      {/* Mono-lattice grid backdrop */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(76,141,255,0.06) 1px, transparent 1px)," +
            "linear-gradient(90deg, rgba(76,141,255,0.06) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
          maskImage:
            "radial-gradient(ellipse at center, rgba(0,0,0,0.9), transparent 70%)",
          WebkitMaskImage:
            "radial-gradient(ellipse at center, rgba(0,0,0,0.9), transparent 70%)",
        }}
      />
      {/* Scanning sweep */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          height: 140,
          top: "50%",
          transform: "translateY(-50%)",
          background:
            "linear-gradient(180deg, transparent, rgba(76,141,255,0.10) 45%, rgba(76,141,255,0.22) 50%, rgba(76,141,255,0.10) 55%, transparent)",
          animation: "ros-scan 2.4s linear infinite",
          pointerEvents: "none",
        }}
      />

      {/* Instrument card */}
      <div
        style={{
          position: "relative",
          width: 420,
          padding: "28px 30px 24px",
          background: "linear-gradient(180deg, rgba(23,27,33,0.92), rgba(18,21,26,0.92))",
          border: "1px solid rgba(76,141,255,0.28)",
          borderRadius: 12,
          boxShadow:
            "0 24px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.02) inset",
          fontFamily: "var(--font-sans)",
          animation: exiting ? "ros-card-out 220ms forwards" : "ros-card-in 340ms cubic-bezier(0.2,0,0,1)",
        }}
      >
        {/* Top row: logo + kicker */}
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 20 }}>
          <div style={{ position: "relative", width: 40, height: 40 }}>
            {/* Outer rotating ring */}
            <svg
              width="40"
              height="40"
              viewBox="0 0 40 40"
              style={{ position: "absolute", inset: 0, animation: "ros-spin 3.6s linear infinite" }}
              aria-hidden
            >
              <circle
                cx="20"
                cy="20"
                r="17"
                fill="none"
                stroke="rgba(76,141,255,0.24)"
                strokeWidth="1"
                strokeDasharray="4 6"
              />
              <circle
                cx="20"
                cy="20"
                r="17"
                fill="none"
                stroke="#4C8DFF"
                strokeWidth="1.4"
                strokeDasharray="18 90"
                strokeLinecap="round"
              />
            </svg>
            {/* Inner logo diamond */}
            <div
              style={{
                position: "absolute",
                inset: 8,
                borderRadius: 6,
                background: "linear-gradient(135deg, #4C8DFF, #6BA1FF)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontFamily: "var(--font-mono)",
                fontSize: 14,
                fontWeight: 600,
                boxShadow:
                  "0 0 24px rgba(76,141,255,0.55), 0 0 0 1px rgba(255,255,255,0.08) inset",
                animation: "ros-pulse 1.8s ease-in-out infinite",
              }}
            >
              ◇
            </div>
          </div>
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                fontSize: 10,
                fontFamily: "var(--font-mono)",
                letterSpacing: "0.16em",
                color: "#4C8DFF",
                textTransform: "uppercase",
                marginBottom: 3,
              }}
            >
              Research OS · v0.1
            </div>
            <div style={{ fontSize: 16, fontWeight: 500, color: "#E6EAF0", letterSpacing: "-0.005em" }}>
              {label}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div
          style={{
            position: "relative",
            height: 3,
            background: "rgba(35,42,51,0.9)",
            borderRadius: 2,
            overflow: "hidden",
            marginBottom: 14,
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              width: progress + "%",
              background: "linear-gradient(90deg, #4C8DFF, #6BA1FF)",
              boxShadow: "0 0 12px rgba(76,141,255,0.6)",
              transition: "width 260ms cubic-bezier(0.2,0,0,1)",
            }}
          />
          <div
            aria-hidden
            style={{
              position: "absolute",
              top: 0,
              bottom: 0,
              width: 40,
              left: `calc(${progress}% - 40px)`,
              background:
                "linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)",
              transition: "left 260ms cubic-bezier(0.2,0,0,1)",
            }}
          />
        </div>

        {/* Log lines */}
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {steps.map((s, i) => {
            const done = i < phase;
            const active = i === phase;
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  color: done ? "#35A56F" : active ? "#E6EAF0" : "#6B7684",
                  opacity: done || active ? 1 : 0.55,
                  transition: "color 200ms, opacity 200ms",
                }}
              >
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    width: 12,
                    height: 12,
                    borderRadius: 3,
                    background: done
                      ? "rgba(53,165,111,0.18)"
                      : active
                      ? "rgba(76,141,255,0.18)"
                      : "transparent",
                    border:
                      "1px solid " +
                      (done
                        ? "rgba(53,165,111,0.4)"
                        : active
                        ? "rgba(76,141,255,0.4)"
                        : "rgba(107,118,132,0.35)"),
                    fontSize: 9,
                    color: done ? "#35A56F" : active ? "#4C8DFF" : "#6B7684",
                  }}
                >
                  {done ? "✓" : active ? "▸" : "·"}
                </span>
                <span style={{ letterSpacing: "0.02em" }}>
                  {done ? s : active ? typed : s}
                  {active && (
                    <span
                      style={{
                        display: "inline-block",
                        width: 6,
                        height: 10,
                        marginLeft: 2,
                        background: "#4C8DFF",
                        verticalAlign: "middle",
                        animation: "ros-caret 0.9s steps(2) infinite",
                      }}
                    />
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <style>{`
        @keyframes ros-spin { to { transform: rotate(360deg); } }
        @keyframes ros-pulse {
          0%, 100% { box-shadow: 0 0 18px rgba(76,141,255,0.45), 0 0 0 1px rgba(255,255,255,0.08) inset; }
          50%      { box-shadow: 0 0 32px rgba(76,141,255,0.75), 0 0 0 1px rgba(255,255,255,0.12) inset; }
        }
        @keyframes ros-scan {
          0%   { transform: translateY(-260px); }
          100% { transform: translateY(260px); }
        }
        @keyframes ros-caret {
          0%, 50%  { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        @keyframes ros-card-in {
          from { opacity: 0; transform: translateY(6px) scale(0.985); }
          to   { opacity: 1; transform: none; }
        }
        @keyframes ros-card-out {
          from { opacity: 1; transform: none; }
          to   { opacity: 0; transform: translateY(-4px) scale(0.99); }
        }
      `}</style>
    </div>
  );
};

// Wrapper that listens for locale-change events and mounts a switch-mode
// overlay automatically. Also exposes a boot overlay on first mount.
const LoadingCoordinator = ({ children }) => {
  const [showBoot, setShowBoot] = useState(true);
  const [showSwitch, setShowSwitch] = useState(false);

  useEffect(() => {
    const onChange = () => setShowSwitch(true);
    window.addEventListener("ros:lang-changing", onChange);
    return () => window.removeEventListener("ros:lang-changing", onChange);
  }, []);

  return (
    <>
      {children}
      {showBoot && <LoadingOverlay mode="boot" onDone={() => setShowBoot(false)} />}
      {showSwitch && <LoadingOverlay mode="switch" onDone={() => setShowSwitch(false)} />}
    </>
  );
};

Object.assign(window, { LoadingOverlay, LoadingCoordinator });
