/* Screen 1: Setup Wizard — 5-step onboarding, Relay → Test → Models → Probe → Defaults */

const SetupScreen = () => {
  const { t } = useI18n();
  const [step, setStep] = useState(3); // Show probe step to demo the interesting state
  const steps = [
    { id: "relay", label: t("st.step.relay"), icon: "wifi" },
    { id: "test", label: t("st.step.test"), icon: "circle-o" },
    { id: "models", label: t("st.step.models"), icon: "hex" },
    { id: "probe", label: t("st.step.probe"), icon: "flask" },
    { id: "defaults", label: t("st.step.defaults"), icon: "check" },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 24, flex: 1, minHeight: 0, alignItems: "flex-start", padding: "24px 8px" }}>
      {/* Left info card */}
      <div className="panel" style={{ padding: 20, position: "sticky", top: 0 }}>
        <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--accent)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>
          <Icon name="shield" size={10}/> {t("st.kicker")}
        </div>
        <div style={{ fontSize: 18, fontWeight: 500, marginBottom: 4, letterSpacing: "-0.005em" }}>{t("st.title")}</div>
        <div style={{ fontSize: 12, color: "var(--fg-muted)", lineHeight: 1.55, marginBottom: 20 }}>
          {t("st.desc")}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.5 }}>
          <div style={{ display: "flex", gap: 8 }}>
            <Icon name="check" size={11} style={{ color: "var(--success)", flexShrink: 0, marginTop: 2 }}/>
            <div><strong style={{ color: "var(--fg)" }}>{t("st.pt1")}</strong> {t("st.pt1b")} <span className="mono">configured / missing</span>.</div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <Icon name="check" size={11} style={{ color: "var(--success)", flexShrink: 0, marginTop: 2 }}/>
            <div><strong style={{ color: "var(--fg)" }}>{t("st.pt2")}</strong> {t("st.pt2b")}</div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <Icon name="check" size={11} style={{ color: "var(--success)", flexShrink: 0, marginTop: 2 }}/>
            <div><strong style={{ color: "var(--fg)" }}>{t("st.pt3")}</strong> {t("st.pt3b")}</div>
          </div>
          <div style={{ height: 1, background: "var(--border)", margin: "6px 0" }}/>
          <div style={{ display: "flex", gap: 8 }}>
            <Icon name="ban" size={11} style={{ color: "var(--fg-faint)", flexShrink: 0, marginTop: 2 }}/>
            <div>{t("st.no1")} <em>{t("st.no1b")}</em> {t("st.no1c")}</div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <Icon name="ban" size={11} style={{ color: "var(--fg-faint)", flexShrink: 0, marginTop: 2 }}/>
            <div>{t("st.no2")} <em>{t("st.no2b")}</em> {t("st.no2c")}</div>
          </div>
        </div>
      </div>

      {/* Wizard */}
      <div style={{ maxWidth: 640, display: "flex", flexDirection: "column", gap: 20 }}>
        {/* Step indicator */}
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          {steps.map((s, i) => (
            <React.Fragment key={s.id}>
              <div style={{
                display: "flex", alignItems: "center", gap: 6, padding: "5px 10px",
                borderRadius: 4, fontSize: 11, fontFamily: "var(--font-mono)",
                letterSpacing: "0.04em", textTransform: "uppercase",
                background: i === step ? "var(--accent-dim)" : "transparent",
                color: i === step ? "var(--accent)" : i < step ? "var(--success)" : "var(--fg-faint)",
                border: `1px solid ${i === step ? "var(--accent-line)" : "transparent"}`,
                cursor: i < step ? "pointer" : "default",
              }} onClick={() => i <= step && setStep(i)}>
                <Icon name={i < step ? "check" : s.icon} size={10}/>
                <span>{String(i+1).padStart(2,"0")} · {s.label}</span>
              </div>
              {i < steps.length - 1 && <div style={{ width: 12, height: 1, background: i < step ? "var(--success)" : "var(--border)" }}/>}
            </React.Fragment>
          ))}
        </div>

        {/* Current step body */}
        {step === 0 && <StepRelay/>}
        {step === 1 && <StepTest/>}
        {step === 2 && <StepModels/>}
        {step === 3 && <StepProbe/>}
        {step === 4 && <StepDefaults/>}

        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
          <button className="btn" disabled={step === 0} onClick={() => setStep(step - 1)}>{t("st.back")}</button>
          <div style={{ fontSize: 11, color: "var(--fg-faint)", alignSelf: "center" }}>{t("st.stepN")} {step+1} {t("st.stepOf")} {steps.length}</div>
          <button className="btn primary" disabled={step === steps.length - 1} onClick={() => setStep(step + 1)}>{t("st.continue")}</button>
        </div>
      </div>
    </div>
  );
};

const StepRelay = () => { const { t } = useI18n(); return (
  <div className="panel" style={{ padding: 20 }}>
    <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 4 }}>{t("st.addEndpoint")}</div>
    <div style={{ fontSize: 12, color: "var(--fg-muted)", marginBottom: 16 }}>{t("st.addDesc")}</div>

    <FormField label={t("st.f.name")}>
      <input className="input" defaultValue="Anthropic Direct" style={INPUT}/>
    </FormField>
    <FormField label={t("st.f.baseUrl")}>
      <input className="input" defaultValue="https://api.anthropic.com" style={{ ...INPUT, fontFamily: "var(--font-mono)" }}/>
    </FormField>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      <FormField label={t("st.f.protocol")}>
        <select style={INPUT}><option>OPENAI_COMPATIBLE</option></select>
      </FormField>
      <FormField label={t("st.f.apiStyle")}>
        <select style={INPUT}><option>chat_completions</option><option>responses</option></select>
      </FormField>
    </div>
    <FormField label={<>{t("st.f.apiKey")} <span style={{ color: "var(--fg-faint)", fontWeight: 400 }}>· {t("st.f.apiKeyHint")}</span></>}>
      <div style={{ position: "relative" }}>
        <input type="password" defaultValue="sk-ant-••••••••••••••••••••••••••••••••••••" style={{ ...INPUT, paddingLeft: 32, fontFamily: "var(--font-mono)" }}/>
        <Icon name="lock" size={12} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--fg-faint)" }}/>
      </div>
    </FormField>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
      <FormField label={t("st.f.timeout")}><input style={INPUT} defaultValue="60"/></FormField>
      <FormField label={t("st.f.retries")}><input style={INPUT} defaultValue="3"/></FormField>
      <FormField label={t("st.f.concurrency")}><input style={INPUT} defaultValue="16"/></FormField>
    </div>
  </div>
)};

const StepTest = () => { const { t } = useI18n(); return (
  <div className="panel" style={{ padding: 20 }}>
    <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 12 }}>{t("st.test.title")}</div>
    <div style={{ background: "var(--bg-sunken)", padding: 14, borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 12, lineHeight: 1.7 }}>
      <div><span style={{ color: "var(--fg-faint)" }}>POST</span> <span style={{ color: "var(--accent)" }}>/llm-endpoints/ep_anthropic_direct/test</span></div>
      <div style={{ marginTop: 8 }}>
        <span style={{ color: "var(--fg-faint)" }}>ok</span> · <span style={{ color: "var(--success)" }}>true</span>
      </div>
      <div><span style={{ color: "var(--fg-faint)" }}>returned_model_name</span> · claude-sonnet-4-20250514</div>
      <div><span style={{ color: "var(--fg-faint)" }}>system_fingerprint</span> · <span style={{ color: "var(--unknown)" }}>{t("st.test.notProvided")}</span> <span style={{ fontSize: 10 }}>({"provider_fingerprint_available"}: false)</span></div>
      <div><span style={{ color: "var(--fg-faint)" }}>latency_ms</span> · 302</div>
    </div>
    <div style={{ marginTop: 12, padding: 10, background: "var(--unknown-dim)", border: "1px dashed var(--unknown-line)", borderRadius: 4, fontSize: 11, color: "var(--unknown)", display: "flex", gap: 8 }}>
      <Icon name="q" size={12} style={{ flexShrink: 0, marginTop: 2 }}/>
      <span><strong>{t("st.test.reprodTitle")}</strong> {t("st.test.reprodMsg")} <span className="mono">system_fingerprint</span>{t("st.test.reprodMsg2")}</span>
    </div>
  </div>
)};

const StepModels = () => { const { t } = useI18n(); return (
  <div className="panel" style={{ padding: 20 }}>
    <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 4 }}>{t("st.models.title")}</div>
    <div style={{ fontSize: 12, color: "var(--fg-muted)", marginBottom: 12 }}>{t("st.models.desc")}</div>
    <div style={{ border: "1px solid var(--border)", borderRadius: 6, overflow: "hidden" }}>
      {[
        ["claude-opus-4-1-20250805", true, "Frontier · 200k ctx"],
        ["claude-sonnet-4-20250514", true, "Balanced · 200k ctx"],
        ["claude-3-5-haiku-20241022", true, "Fast · 200k ctx"],
        ["claude-3-opus-20240229", false, "Legacy · 200k ctx"],
        ["claude-3-sonnet-20240229", false, "Legacy · 200k ctx"],
      ].map(([id, checked, hint], i) => (
        <label key={id} style={{
          display: "grid", gridTemplateColumns: "auto 1fr auto",
          gap: 12, padding: "8px 12px", alignItems: "center",
          borderBottom: i < 4 ? "1px solid var(--border-subtle)" : "none",
          cursor: "pointer",
        }}>
          <input type="checkbox" defaultChecked={checked} style={{ accentColor: "var(--accent)" }}/>
          <span className="mono" style={{ fontSize: 12 }}>{id}</span>
          <span style={{ fontSize: 11, color: "var(--fg-faint)" }}>{hint}</span>
        </label>
      ))}
    </div>
  </div>
)};

const StepProbe = () => { const { t } = useI18n();
  const rows = [
    { model: "claude-opus-4-1-20250805", status: "ok", caps: [["chat","ok"],["tool_calls","ok"],["extended_thinking","ok"]], fpAvail: false },
    { model: "claude-sonnet-4-20250514", status: "ok", caps: [["chat","ok"],["tool_calls","ok"],["json_mode","degraded"],["vision","ok"]], fpAvail: false },
    { model: "claude-3-5-haiku-20241022", status: "probing", caps: [], fpAvail: null },
  ];
  return (
    <div className="panel" style={{ padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 500 }}>{t("st.probe.title")}</div>
          <div style={{ fontSize: 12, color: "var(--fg-muted)" }}>{t("st.probe.desc")}</div>
        </div>
        <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>2/3 {t("st.probe.done")}</div>
      </div>
      <div style={{ border: "1px solid var(--border)", borderRadius: 6, overflow: "hidden" }}>
        {rows.map((r, i) => (
          <div key={r.model} style={{
            padding: "10px 12px",
            borderBottom: i < rows.length - 1 ? "1px solid var(--border-subtle)" : "none",
            background: r.status === "probing" ? "var(--bg-raised)" : "transparent",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
              {r.status === "probing"
                ? <Icon name="spin" size={12} style={{ color: "var(--accent)" }}/>
                : <Icon name="check" size={12} style={{ color: "var(--success)" }}/>}
              <span className="mono" style={{ fontSize: 12 }}>{r.model}</span>
              {r.status === "probing" && <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--accent)", letterSpacing: "0.08em" }}>{t("st.probe.probing")}</span>}
              {r.status !== "probing" && r.fpAvail === false && (
                <ReproducibilityChip fingerprint={null} providerAvailable={false} compact={true}/>
              )}
            </div>
            {r.caps.length > 0 && (
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                {r.caps.map(([cap, st]) => (
                  <span key={cap} style={{
                    display: "inline-flex", alignItems: "center", gap: 4,
                    padding: "1px 6px", height: 18, borderRadius: 3,
                    fontSize: 10, fontFamily: "var(--font-mono)",
                    background: st === "degraded" ? "var(--warn-dim)" : "var(--success-dim)",
                    border: `1px solid ${st === "degraded" ? "var(--warn-line)" : "var(--success-line)"}`,
                    color: st === "degraded" ? "var(--warn)" : "var(--success)",
                  }}>
                    <Icon name={st === "degraded" ? "warn-tri" : "check"} size={9}/> {cap}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const StepDefaults = () => { const { t } = useI18n(); return (
  <div className="panel" style={{ padding: 20 }}>
    <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 12 }}>{t("st.def.title")}</div>
    <div style={{ fontSize: 12, color: "var(--fg-muted)", marginBottom: 16 }}>{t("st.def.desc")}</div>
    {[
      ["fast_retrieval", "claude-3-5-haiku-20241022"],
      ["balanced_reasoning", "claude-sonnet-4-20250514"],
      ["frontier_reasoning", "claude-opus-4-1-20250805"],
      ["long_context", "gemini-2.5-pro"],
    ].map(([profile, model]) => (
      <div key={profile} style={{ display: "grid", gridTemplateColumns: "180px 1fr", gap: 12, padding: "6px 0", alignItems: "center" }}>
        <span className="mono" style={{ fontSize: 12, color: "var(--fg-muted)" }}>{profile}</span>
        <select style={INPUT} defaultValue={model}><option>{model}</option></select>
      </div>
    ))}
  </div>
)};

const INPUT = {
  width: "100%", height: 30, padding: "0 10px",
  background: "var(--bg-sunken)", color: "var(--fg)",
  border: "1px solid var(--border)", borderRadius: 6,
  fontSize: 12,
};

const FormField = ({ label, children }) => (
  <div style={{ marginBottom: 12 }}>
    <div style={{ fontSize: 11, color: "var(--fg-muted)", marginBottom: 4, letterSpacing: "0.02em" }}>{label}</div>
    {children}
  </div>
);

Object.assign(window, { SetupScreen });
