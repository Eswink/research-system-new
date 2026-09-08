/* Protocol Editor — the 7 section forms.
   Each Section is a pure component receiving (value, setP, errors, ...).
*/

// helper — find error attached to a specific path
const findErr = (errors, path) => errors.find(e => e.path === path);

// ─── 01. Manifest ─────────────────────────────────────
const ManifestSection = ({ value, setP, errors, adminMode }) => {
  const { t } = useI18n();
  const { manifest, protocol_version } = value;
  const eName = findErr(errors, "manifest.name");
  const levels = [
    { value: "MANUAL", label: t("pe.man.manual"), desc: t("pe.man.manualDesc") },
    { value: "GUARDED_AUTONOMOUS", label: t("pe.man.guarded"), desc: t("pe.man.guardedDesc") },
    { value: "AUTONOMOUS", label: t("pe.man.autonomous"), desc: t("pe.man.autonomousDesc") },
  ];
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.manifest")}
        subtitle={t("pe.sec.manifestDesc")}
        extra={<span className="chip mono" style={{ background: "var(--accent-dim)", borderColor: "var(--accent-line)", color: "var(--accent)" }}>protocol_version 1.4</span>}
      />

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 90px) minmax(0, 1fr)", gap: 14 }}>
        <Field
          label="protocol_version"
          tooltip={t("pe.man.tip.version")}
          locked
        >
          <input value={protocol_version} readOnly disabled style={{ ...INPUT_MONO, opacity: 0.6, cursor: "not-allowed", textAlign: "center" }}/>
        </Field>
        <Field
          label="manifest.id"
          tooltip={t("pe.man.tip.id")}
          locked
        >
          <div style={{ display: "flex", gap: 6, alignItems: "center", minWidth: 0 }}>
            <input value={manifest.id} readOnly disabled style={{ ...INPUT_MONO, opacity: 0.6, cursor: "not-allowed", minWidth: 0 }}/>
            <button className="btn sm ghost" title="Copy" style={{ height: 28, flexShrink: 0 }}>
              <Icon name="copy" size={10}/>
            </button>
          </div>
        </Field>
      </div>

      <Field
        label="manifest.name"
        tooltip={t("pe.man.tip.name")}
        error={eName}
        hint={t("pe.man.hint.name")}
      >
        <input
          value={manifest.name}
          onChange={e => setP(p => { p.manifest.name = e.target.value; })}
          style={eName ? { ...INPUT_ERR, fontFamily: "var(--font-mono)" } : INPUT_MONO}
          placeholder="lowercase-with-hyphens"
        />
      </Field>

      <Field
        label="manifest.autonomy_level"
        tooltip={t("pe.man.tip.autonomy")}
      >
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6 }}>
          {levels.map(l => {
            const active = manifest.autonomy_level === l.value;
            const tone = l.value === "AUTONOMOUS" ? "danger" : l.value === "GUARDED_AUTONOMOUS" ? "warn" : "success";
            return (
              <button
                key={l.value}
                onClick={() => setP(p => { p.manifest.autonomy_level = l.value; })}
                style={{
                  padding: "10px 12px",
                  background: active ? `var(--${tone}-dim)` : "var(--bg-sunken)",
                  border: `1px solid ${active ? `var(--${tone}-line)` : "var(--border)"}`,
                  borderRadius: 6,
                  cursor: "pointer", textAlign: "left",
                  color: "var(--fg)", fontFamily: "inherit",
                }}
              >
                <div style={{
                  fontSize: 11, fontFamily: "var(--font-mono)", fontWeight: 500,
                  color: active ? `var(--${tone})` : "var(--fg-muted)",
                  marginBottom: 4, letterSpacing: "0.04em",
                }}>{l.value}</div>
                <div style={{ fontSize: 10, color: "var(--fg-faint)", lineHeight: 1.4 }}>{l.desc}</div>
              </button>
            );
          })}
        </div>
      </Field>
    </div>
  );
};

// ─── 02. Objectives ───────────────────────────────────
const ObjectivesSection = ({ value, setP, errors }) => {
  const { t } = useI18n();
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.objectives")}
        subtitle={t("pe.sec.objectivesDesc")}
        extra={<span className="chip">{value.objectives.length} · {t("pe.obj.total")}</span>}
      />

      {value.objectives.map((o, i) => {
        const eId = findErr(errors, `objectives[${i}].id`);
        const eSt = findErr(errors, `objectives[${i}].statement`);
        return (
          <div key={i} style={{
            marginBottom: 12,
            border: "1px solid var(--border)", borderRadius: 8,
            background: "var(--bg-raised)",
          }}>
            <div style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "7px 12px", borderBottom: "1px solid var(--border-subtle)",
              background: "var(--bg-panel)", borderRadius: "8px 8px 0 0",
            }}>
              <Icon name="flask" size={10} style={{ color: "var(--fg-muted)" }}/>
              <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>
                OBJECTIVE {String(i+1).padStart(2, "0")}
              </span>
              <button className="btn sm ghost" style={{ marginLeft: "auto", height: 20, padding: "0 6px", color: "var(--danger)" }}
                onClick={() => setP(p => { p.objectives.splice(i, 1); })}>
                <Icon name="x" size={9}/> {t("pe.obj.remove")}
              </button>
            </div>
            <div style={{ padding: 12 }}>
              <Field label="id" error={eId}>
                <input
                  value={o.id}
                  onChange={e => setP(p => { p.objectives[i].id = e.target.value; })}
                  style={eId ? { ...INPUT_ERR, fontFamily: "var(--font-mono)" } : INPUT_MONO}
                  placeholder="obj_short_snake_case"
                />
              </Field>
              <Field label="statement" error={eSt} tooltip={t("pe.obj.tip.statement")}>
                <textarea
                  value={o.statement}
                  onChange={e => setP(p => { p.objectives[i].statement = e.target.value; })}
                  style={{ ...INPUT, height: "auto", minHeight: 60, padding: 8, resize: "vertical", lineHeight: 1.55, ...(eSt ? { borderColor: "var(--warn-line)" } : {}) }}
                  placeholder="Quantify …"
                />
              </Field>
            </div>
          </div>
        );
      })}

      <button className="btn"
        onClick={() => setP(p => { p.objectives.push({ id: `obj_${Math.random().toString(36).slice(2,7)}`, statement: "" }); })}
        style={{ width: "100%", justifyContent: "center", borderStyle: "dashed" }}>
        <Icon name="plus" size={11}/> {t("pe.obj.add")}
      </button>
    </div>
  );
};

// ─── 03. Team ─────────────────────────────────────────
const TeamSection = ({ value, setP, errors }) => {
  const { t } = useI18n();
  const templates = [
    { id: "LEAN", label: "LEAN", desc: t("pe.tm.leanDesc"), roles: 3 },
    { id: "STANDARD", label: "STANDARD", desc: t("pe.tm.stdDesc"), roles: 8 },
    { id: "RIGOROUS", label: "RIGOROUS", desc: t("pe.tm.rigDesc"), roles: 12 },
  ];
  const roleOptions = ["role_planner","role_experimenter","role_reviewer","role_stats","role_writer","role_ethics","role_qa","role_ops"];
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.team")}
        subtitle={t("pe.sec.teamDesc")}
      />

      <Field label="team.template" tooltip={t("pe.tm.tip.template")}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6 }}>
          {templates.map(tm => {
            const active = value.team.template === tm.id;
            return (
              <button key={tm.id}
                onClick={() => setP(p => { p.team.template = tm.id; })}
                style={{
                  padding: "10px 12px",
                  background: active ? "var(--accent-dim)" : "var(--bg-sunken)",
                  border: `1px solid ${active ? "var(--accent-line)" : "var(--border)"}`,
                  borderRadius: 6,
                  cursor: "pointer", textAlign: "left",
                  color: "var(--fg)", fontFamily: "inherit",
                }}>
                <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", fontWeight: 500, color: active ? "var(--accent)" : "var(--fg-muted)", marginBottom: 4 }}>
                  {tm.label}
                </div>
                <div style={{ fontSize: 10, color: "var(--fg-faint)", lineHeight: 1.4, marginBottom: 4 }}>{tm.desc}</div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{tm.roles} {t("pe.tm.roles")}</div>
              </button>
            );
          })}
        </div>
      </Field>

      <div style={{ marginTop: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
          <label style={{ fontSize: 11, color: "var(--fg-muted)" }}>team.overrides</label>
          <TooltipIcon text={t("pe.tm.tip.overrides")}/>
          <span className="chip">{value.team.overrides.length}</span>
        </div>

        {/* Table header */}
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 0.6fr 1.6fr 24px", gap: 8, padding: "0 2px 6px", fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          <span>role</span>
          <span>instances</span>
          <span>collapse_when</span>
          <span/>
        </div>
        <div style={{ background: "var(--bg-sunken)", border: "1px solid var(--border)", borderRadius: 6 }}>
          {value.team.overrides.map((ov, i) => (
            <div key={i} style={{
              display: "grid", gridTemplateColumns: "1.4fr 0.6fr 1.6fr 24px", gap: 8,
              padding: "6px 8px", alignItems: "center",
              borderBottom: i < value.team.overrides.length - 1 ? "1px solid var(--border-subtle)" : "none",
            }}>
              <select value={ov.role}
                onChange={e => setP(p => { p.team.overrides[i].role = e.target.value; })}
                style={INPUT_MONO}>
                {roleOptions.map(r => <option key={r}>{r}</option>)}
              </select>
              <input type="number"
                value={ov.instances ?? ""}
                onChange={e => setP(p => { p.team.overrides[i].instances = e.target.value === "" ? null : Number(e.target.value); })}
                placeholder="—"
                style={INPUT_MONO}/>
              <input value={ov.collapse_when}
                onChange={e => setP(p => { p.team.overrides[i].collapse_when = e.target.value; })}
                placeholder="condition expression …"
                style={INPUT_MONO}/>
              <button className="btn sm ghost" style={{ height: 22, padding: 0, width: 22, justifyContent: "center", color: "var(--danger)" }}
                onClick={() => setP(p => { p.team.overrides.splice(i, 1); })}>
                <Icon name="x" size={9}/>
              </button>
            </div>
          ))}
        </div>
        <button className="btn sm"
          style={{ width: "100%", justifyContent: "center", marginTop: 6, borderStyle: "dashed" }}
          onClick={() => setP(p => { p.team.overrides.push({ role: "role_reviewer", instances: 1, collapse_when: "" }); })}>
          <Icon name="plus" size={10}/> {t("pe.tm.addOverride")}
        </button>
      </div>
    </div>
  );
};

// ─── 04. Evaluation ───────────────────────────────────
const EvaluationSection = ({ value, setP, errors, warnings }) => {
  const { t } = useI18n();
  const ev = value.evaluation;
  const eN = findErr(errors, "evaluation.n_per_lang");
  const wN = findErr(warnings, "evaluation.n_per_lang");
  const wT = findErr(warnings, "evaluation.temperature_grid");
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.evaluation")}
        subtitle={t("pe.sec.evaluationDesc")}
        extra={<span className="chip mono">n = {ev.languages.length * ev.n_per_lang * ev.temperature_grid.length}</span>}
      />

      {/* Benchmarks */}
      <Field label="evaluation.benchmarks" tooltip={t("pe.ev.tip.benchmarks")}>
        <ChipMultiSelect
          items={ev.benchmarks}
          available={AVAILABLE_BENCHMARKS}
          onAdd={v => setP(p => { if (!p.evaluation.benchmarks.includes(v)) p.evaluation.benchmarks.push(v); })}
          onRemove={v => setP(p => { p.evaluation.benchmarks = p.evaluation.benchmarks.filter(x => x !== v); })}
          onFreeAdd={v => setP(p => { if (v && !p.evaluation.benchmarks.includes(v)) p.evaluation.benchmarks.push(v); })}
        />
      </Field>

      {/* Languages */}
      <Field label="evaluation.languages" tooltip={t("pe.ev.tip.languages")}
        hint={`${ev.languages.length} ${t("pe.ev.langsSelected")} · ${AVAILABLE_LANGUAGES.length - ev.languages.length} ${t("pe.ev.langsMore")}`}>
        <div>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 6 }}>
            {ev.languages.map(code => {
              const meta = AVAILABLE_LANGUAGES.find(l => l.code === code);
              return (
                <span key={code} style={{
                  display: "inline-flex", alignItems: "center", gap: 5,
                  padding: "3px 6px 3px 8px", height: 24,
                  background: "var(--accent-dim)", border: "1px solid var(--accent-line)",
                  borderRadius: 4, fontSize: 11,
                }}>
                  <span className="mono" style={{ color: "var(--accent)", fontWeight: 500 }}>{code}</span>
                  {meta && <span style={{ color: "var(--fg-muted)", fontSize: 10 }}>{meta.label}</span>}
                  <button
                    onClick={() => setP(p => { p.evaluation.languages = p.evaluation.languages.filter(x => x !== code); })}
                    style={{ background: "transparent", border: "none", color: "var(--fg-faint)", cursor: "pointer", padding: 0, marginLeft: 2, display: "flex" }}>
                    <Icon name="x" size={9}/>
                  </button>
                </span>
              );
            })}
          </div>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {AVAILABLE_LANGUAGES.filter(l => !ev.languages.includes(l.code)).map(l => (
              <button key={l.code}
                onClick={() => setP(p => { p.evaluation.languages.push(l.code); })}
                style={{
                  display: "inline-flex", alignItems: "center", gap: 4,
                  padding: "2px 7px", height: 22,
                  background: "transparent", border: "1px dashed var(--border-strong)",
                  borderRadius: 4, fontSize: 11, color: "var(--fg-muted)",
                  cursor: "pointer", fontFamily: "inherit",
                }}>
                <Icon name="plus" size={9}/>
                <span className="mono">{l.code}</span>
                <span style={{ fontSize: 10, color: "var(--fg-faint)" }}>{l.label}</span>
              </button>
            ))}
          </div>
        </div>
      </Field>

      {/* n_per_lang */}
      <Field label="evaluation.n_per_lang" tooltip={t("pe.ev.tip.n")} error={eN} hint={wN ? wN.message : t("pe.ev.hint.n")}>
        <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
          <button className="btn sm" onClick={() => setP(p => { p.evaluation.n_per_lang = Math.max(0, p.evaluation.n_per_lang - 50); })}>
            <Icon name="dot" size={9}/> −50
          </button>
          <input type="number" value={ev.n_per_lang}
            onChange={e => setP(p => { p.evaluation.n_per_lang = Number(e.target.value); })}
            style={{ ...(eN ? INPUT_ERR : wN ? { ...INPUT, borderColor: "var(--warn-line)" } : INPUT), fontFamily: "var(--font-mono)", width: 96, textAlign: "center" }}/>
          <button className="btn sm" onClick={() => setP(p => { p.evaluation.n_per_lang += 50; })}>
            <Icon name="plus" size={9}/> +50
          </button>
          <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", marginLeft: 4 }}>
            × {ev.languages.length} = {(ev.n_per_lang * ev.languages.length).toLocaleString()} samples
          </span>
        </div>
      </Field>

      {/* Temperature grid */}
      <Field label="evaluation.temperature_grid" tooltip={t("pe.ev.tip.temp")} hint={wT ? wT.message : t("pe.ev.hint.temp")}>
        <TemperatureGrid
          values={ev.temperature_grid}
          onChange={arr => setP(p => { p.evaluation.temperature_grid = arr; })}
        />
      </Field>
    </div>
  );
};

// ─── Sub: Chip multi-select ─────────────────────────
const ChipMultiSelect = ({ items, available, onAdd, onRemove, onFreeAdd }) => {
  const [input, setInput] = useState("");
  const [pickerOpen, setPickerOpen] = useState(false);
  const unpicked = available.filter(x => !items.includes(x));
  return (
    <div>
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 6 }}>
        {items.map(x => (
          <span key={x} style={{
            display: "inline-flex", alignItems: "center", gap: 5,
            padding: "3px 6px 3px 8px", height: 22,
            background: "var(--bg-raised)", border: "1px solid var(--border-strong)",
            borderRadius: 4, fontSize: 11, fontFamily: "var(--font-mono)",
          }}>
            {x}
            <button onClick={() => onRemove(x)}
              style={{ background: "transparent", border: "none", color: "var(--fg-faint)", cursor: "pointer", padding: 0, display: "flex" }}>
              <Icon name="x" size={9}/>
            </button>
          </span>
        ))}
      </div>
      <div style={{ display: "flex", gap: 6, alignItems: "center", minWidth: 0 }}>
        <input value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && input.trim()) { onFreeAdd(input.trim()); setInput(""); } }}
          placeholder="+ custom · Enter"
          style={{ ...INPUT_MONO, flex: 1, height: 26, minWidth: 0 }}/>
        {unpicked.length > 0 && (
          <div style={{ position: "relative", flexShrink: 0 }}>
            <button className="btn sm" onClick={() => setPickerOpen(v => !v)}>
              <Icon name="menu" size={10}/> +{unpicked.length}
              <Icon name="chevron-d" size={9}/>
            </button>
            {pickerOpen && (
              <div style={{
                position: "absolute", top: "calc(100% + 4px)", right: 0,
                background: "var(--bg-panel)", border: "1px solid var(--border-strong)",
                borderRadius: 6, padding: 4, minWidth: 200,
                boxShadow: "var(--shadow-2)", zIndex: 50,
              }}>
                {unpicked.map(x => (
                  <button key={x} onClick={() => { onAdd(x); setPickerOpen(false); }}
                    style={{
                      display: "block", width: "100%", padding: "5px 8px",
                      background: "transparent", border: "none", cursor: "pointer",
                      color: "var(--fg)", fontSize: 11, fontFamily: "var(--font-mono)",
                      textAlign: "left", borderRadius: 3,
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                    <Icon name="plus" size={9} style={{ marginRight: 6, color: "var(--fg-faint)" }}/>
                    {x}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Sub: Temperature grid (slider + chips) ─────────
const TemperatureGrid = ({ values, onChange }) => {
  const [newVal, setNewVal] = useState(0.4);
  const sorted = [...values].sort((a,b) => a-b);
  return (
    <div>
      {/* Sample point track */}
      <div style={{
        position: "relative", height: 44,
        background: "var(--bg-sunken)", border: "1px solid var(--border)",
        borderRadius: 6, padding: "16px 12px 12px",
      }}>
        {/* Ticks */}
        {[0, 0.25, 0.5, 0.75, 1.0].map(t => (
          <div key={t} style={{
            position: "absolute", top: 8, bottom: 4, width: 1,
            left: `calc(12px + ${t * 100}% - ${t * 24}px)`,
            background: "var(--border-subtle)",
          }}/>
        ))}
        {/* Baseline */}
        <div style={{
          position: "absolute", left: 12, right: 12, top: "50%",
          height: 1, background: "var(--border-subtle)",
        }}/>
        {/* Dots */}
        {sorted.map((v, i) => (
          <div key={i} title={`temperature = ${v.toFixed(2)}`}
            style={{
              position: "absolute", top: "50%", transform: "translate(-50%, -50%)",
              left: `calc(12px + ${v * 100}% - ${v * 24}px)`,
              width: 14, height: 14, borderRadius: "50%",
              background: "var(--accent)", border: "2px solid var(--bg-panel)",
              boxShadow: "0 0 0 1px var(--accent-line)",
            }}/>
        ))}
        {/* labels */}
        {[0, 0.25, 0.5, 0.75, 1.0].map(t => (
          <div key={t} style={{
            position: "absolute", bottom: -12, fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)",
            left: `calc(12px + ${t * 100}% - ${t * 24}px)`, transform: "translateX(-50%)",
          }}>{t.toFixed(2)}</div>
        ))}
      </div>

      {/* Chips */}
      <div style={{ marginTop: 20, display: "flex", gap: 4, flexWrap: "wrap" }}>
        {sorted.map((v, i) => (
          <span key={i} style={{
            display: "inline-flex", alignItems: "center", gap: 5,
            padding: "3px 6px 3px 8px", height: 22,
            background: "var(--accent-dim)", border: "1px solid var(--accent-line)",
            borderRadius: 4, fontSize: 11, fontFamily: "var(--font-mono)",
            color: "var(--accent)",
          }}>
            {v.toFixed(2)}
            <button onClick={() => onChange(values.filter(x => x !== v))}
              style={{ background: "transparent", border: "none", color: "var(--fg-faint)", cursor: "pointer", padding: 0, display: "flex" }}>
              <Icon name="x" size={9}/>
            </button>
          </span>
        ))}
        <div style={{ display: "inline-flex", alignItems: "center", gap: 4, marginLeft: 4 }}>
          <input type="number" step="0.05" min="0" max="1"
            value={newVal}
            onChange={e => setNewVal(Number(e.target.value))}
            style={{ ...INPUT_MONO, height: 22, width: 60, fontSize: 11, padding: "0 6px" }}/>
          <button className="btn sm"
            onClick={() => { if (!values.includes(newVal) && newVal >= 0 && newVal <= 1) onChange([...values, newVal]); }}
            style={{ height: 22 }}>
            <Icon name="plus" size={9}/> add
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── 05. Budget ───────────────────────────────────────
const BudgetSection = ({ value, setP, errors, warnings }) => {
  const { t } = useI18n();
  const b = value.budget;
  const eRes = findErr(errors, "budget.reservations");
  const wRes = findErr(warnings, "budget.reservations");
  const wHs = findErr(warnings, "budget.hard_stop_on_breach");
  const [capConfirm, setCapConfirm] = useState(false);
  const [capDraft, setCapDraft] = useState(b.cap_minor);

  const sum = b.reservations.reduce((s, r) => s + (r.minor || 0), 0);
  const pct = Math.min(100, (sum / b.cap_minor) * 100);
  const palette = ["var(--accent)", "#8B7BD8", "#D9962A", "#35A56F", "#E0524C", "#4CB8C4"];

  return (
    <div>
      <SectionHeader
        title={t("pe.sec.budget")}
        subtitle={t("pe.sec.budgetDesc")}
      />

      {/* cap_minor */}
      <Field label="budget.cap_minor" tooltip={t("pe.bd.tip.cap")}
        hint={`≈ $${(b.cap_minor / 100000).toFixed(2)} USD ${t("pe.bd.capHint")}`}>
        <div style={{ display: "flex", gap: 6, alignItems: "center", minWidth: 0 }}>
          <input type="number" value={capDraft}
            onChange={e => setCapDraft(Number(e.target.value))}
            style={{ ...INPUT_MONO, flex: 1, minWidth: 0 }}/>
          <span style={{ fontSize: 11, color: "var(--fg-faint)", fontFamily: "var(--font-mono)", flexShrink: 0 }}>
            = ${(capDraft / 100000).toFixed(2)}
          </span>
          {capDraft > b.cap_minor && !capConfirm ? (
            <button className="btn sm" style={{ borderColor: "var(--warn-line)", color: "var(--warn)" }}
              onClick={() => setCapConfirm(true)}>
              <Icon name="warn-tri" size={9}/> {t("pe.bd.capConfirm")}
            </button>
          ) : capConfirm && capDraft > b.cap_minor ? (
            <button className="btn sm primary"
              onClick={() => { setP(p => { p.budget.cap_minor = capDraft; }); setCapConfirm(false); }}>
              <Icon name="check" size={9}/> {t("pe.bd.capApply")}
            </button>
          ) : capDraft !== b.cap_minor ? (
            <button className="btn sm primary"
              onClick={() => setP(p => { p.budget.cap_minor = capDraft; })}>
              <Icon name="check" size={9}/> apply
            </button>
          ) : (
            <span className="chip" style={{ color: "var(--success)", borderColor: "var(--success-line)" }}>
              <Icon name="check" size={9}/> saved
            </span>
          )}
        </div>
      </Field>

      {/* hard_stop_on_breach */}
      <Field label="budget.hard_stop_on_breach" tooltip={t("pe.bd.tip.hardstop")}
        hint={wHs ? wHs.message : null}>
        <div style={{ display: "flex", gap: 6 }}>
          {[true, false].map(v => (
            <button key={String(v)}
              onClick={() => setP(p => { p.budget.hard_stop_on_breach = v; })}
              style={{
                padding: "6px 12px",
                background: b.hard_stop_on_breach === v ? (v ? "var(--success-dim)" : "var(--danger-dim)") : "var(--bg-sunken)",
                border: `1px solid ${b.hard_stop_on_breach === v ? (v ? "var(--success-line)" : "var(--danger-line)") : "var(--border)"}`,
                borderRadius: 6, cursor: "pointer",
                fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.04em",
                color: b.hard_stop_on_breach === v ? (v ? "var(--success)" : "var(--danger)") : "var(--fg-muted)",
              }}>
              <Icon name={v ? "check" : "ban"} size={10}/> {v ? "HARD_STOP" : "SOFT_WARN"}
            </button>
          ))}
        </div>
      </Field>

      {/* Reservations table */}
      <div style={{ marginTop: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
          <label style={{ fontSize: 11, color: "var(--fg-muted)" }}>budget.reservations</label>
          <TooltipIcon text={t("pe.bd.tip.reservations")}/>
          <span className="chip" style={{
            color: eRes ? "var(--danger)" : sum === b.cap_minor ? "var(--success)" : "var(--fg-muted)",
            borderColor: eRes ? "var(--danger-line)" : sum === b.cap_minor ? "var(--success-line)" : "var(--border)",
          }}>
            Σ ${(sum / 100000).toFixed(2)} / ${(b.cap_minor / 100000).toFixed(2)}
          </span>
          {eRes && <span style={{ fontSize: 10, color: "var(--danger)", fontFamily: "var(--font-mono)" }}>· overflow</span>}
          {!eRes && wRes && <span style={{ fontSize: 10, color: "var(--warn)", fontFamily: "var(--font-mono)" }}>· underplanned</span>}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 130px", gap: 12 }}>
          {/* Table */}
          <div style={{ background: "var(--bg-sunken)", border: `1px solid ${eRes ? "var(--danger-line)" : "var(--border)"}`, borderRadius: 6 }}>
            {b.reservations.map((r, i) => {
              const rowPct = (r.minor / b.cap_minor) * 100;
              return (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "6px minmax(0, 1fr) 90px 32px 20px",
                  gap: 6, padding: "6px 8px 6px 0", alignItems: "center",
                  borderBottom: i < b.reservations.length - 1 ? "1px solid var(--border-subtle)" : "none",
                }}>
                  <div style={{ width: 3, height: 20, background: palette[i % palette.length], borderRadius: 2, marginLeft: 6 }}/>
                  <select value={r.resource}
                    onChange={e => setP(p => { p.budget.reservations[i].resource = e.target.value; })}
                    style={{ ...INPUT_MONO, fontSize: 11, padding: "0 6px", minWidth: 0, width: "100%" }}>
                    {RESOURCE_TYPES.map(rt => <option key={rt.id} value={rt.id}>{rt.id}</option>)}
                  </select>
                  <input type="number" step="10000" value={r.minor}
                    onChange={e => setP(p => { p.budget.reservations[i].minor = Number(e.target.value); })}
                    style={{ ...INPUT_MONO, textAlign: "right", fontSize: 11, padding: "0 6px" }}/>
                  <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", textAlign: "right" }}>
                    {rowPct.toFixed(0)}%
                  </span>
                  <button className="btn sm ghost" style={{ height: 20, padding: 0, width: 20, justifyContent: "center", color: "var(--danger)" }}
                    onClick={() => setP(p => { p.budget.reservations.splice(i, 1); })}>
                    <Icon name="x" size={9}/>
                  </button>
                </div>
              );
            })}
            <button className="btn sm ghost"
              style={{ width: "100%", justifyContent: "center", height: 28, borderTop: "1px solid var(--border-subtle)", borderRadius: 0 }}
              onClick={() => setP(p => { p.budget.reservations.push({ resource: "external_tools", minor: 100000 }); })}>
              <Icon name="plus" size={10}/> {t("pe.bd.addResv")}
            </button>
          </div>

          {/* Donut / pie */}
          <div style={{
            background: "var(--bg-sunken)", border: "1px solid var(--border)",
            borderRadius: 6, padding: 12,
            display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
          }}>
            <BudgetDonut reservations={b.reservations} cap={b.cap_minor} palette={palette}/>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", textAlign: "center" }}>
              <div style={{ fontSize: 14, fontWeight: 500, color: eRes ? "var(--danger)" : "var(--fg)" }}>
                {pct.toFixed(0)}%
              </div>
              <div>{t("pe.bd.ofCap")}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const BudgetDonut = ({ reservations, cap, palette }) => {
  const total = cap;
  const r = 32, cx = 44, cy = 44, strokeW = 10;
  const circ = 2 * Math.PI * r;
  let acc = 0;
  return (
    <svg width="88" height="88" viewBox="0 0 88 88">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--bg-panel)" strokeWidth={strokeW}/>
      {reservations.map((res, i) => {
        const frac = (res.minor || 0) / total;
        const dash = frac * circ;
        const offset = -acc * circ;
        acc += frac;
        return (
          <circle key={i} cx={cx} cy={cy} r={r} fill="none"
            stroke={palette[i % palette.length]} strokeWidth={strokeW}
            strokeDasharray={`${dash} ${circ}`}
            strokeDashoffset={offset}
            transform={`rotate(-90 ${cx} ${cy})`}
            strokeLinecap="butt"/>
        );
      })}
    </svg>
  );
};

// ─── 06. Gates ────────────────────────────────────────
const GatesSection = ({ value, setP, errors }) => {
  const { t } = useI18n();
  const kindHints = {
    BUDGET_GATE: t("pe.gt.bd"),
    QUALITY_GATE: t("pe.gt.qa"),
    PUBLISH_GATE: t("pe.gt.pub"),
    SECURITY_GATE: t("pe.gt.sec"),
    ETHICS_GATE: t("pe.gt.eth"),
  };
  const kindTones = {
    BUDGET_GATE: "warn", QUALITY_GATE: "accent", PUBLISH_GATE: "unknown",
    SECURITY_GATE: "danger", ETHICS_GATE: "danger",
  };
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.gates")}
        subtitle={t("pe.sec.gatesDesc")}
        extra={<span className="chip">{value.gates.length} · {t("pe.gt.total")}</span>}
      />

      {value.gates.map((g, i) => {
        const tone = kindTones[g.kind] || "neutral";
        return (
          <div key={i} style={{
            padding: "10px 12px", marginBottom: 6,
            background: "var(--bg-raised)",
            border: "1px solid var(--border)", borderRadius: 6,
          }}>
            <div style={{
              display: "grid", gridTemplateColumns: "minmax(0, 160px) minmax(0, 1fr) 20px",
              gap: 8, alignItems: "center",
            }}>
              <select value={g.kind}
                onChange={e => setP(p => { p.gates[i].kind = e.target.value; })}
                style={{
                  ...INPUT_MONO, width: "100%", minWidth: 0, fontSize: 11,
                  background: `var(--${tone}-dim)`,
                  borderColor: `var(--${tone}-line)`,
                  color: `var(--${tone})`,
                  fontWeight: 500,
                  letterSpacing: "0.04em",
                }}>
                {GATE_KINDS.map(k => <option key={k} value={k}>{k}</option>)}
              </select>
              <input value={g.at}
                onChange={e => setP(p => { p.gates[i].at = e.target.value; })}
                placeholder="trigger condition …"
                style={{ ...INPUT_MONO, minWidth: 0 }}/>
              <button className="btn sm ghost" style={{ height: 20, padding: 0, width: 20, justifyContent: "center", color: "var(--danger)" }}
                onClick={() => setP(p => { p.gates.splice(i, 1); })}>
                <Icon name="x" size={9}/>
              </button>
            </div>
            <div style={{ fontSize: 10, color: "var(--fg-faint)", marginTop: 6, lineHeight: 1.4, paddingLeft: 2 }}>
              {kindHints[g.kind]}
            </div>
          </div>
        );
      })}
      <button className="btn"
        onClick={() => setP(p => { p.gates.push({ kind: "QUALITY_GATE", at: "" }); })}
        style={{ width: "100%", justifyContent: "center", borderStyle: "dashed" }}>
        <Icon name="plus" size={11}/> {t("pe.gt.add")}
      </button>
    </div>
  );
};

// ─── 07. Policy ───────────────────────────────────────
const PolicySection = ({ value, setP, adminMode }) => {
  const { t } = useI18n();
  const p = value.policy;
  const disabled = !adminMode;
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.policy")}
        subtitle={t("pe.sec.policyDesc")}
        extra={
          <span className="chip mono" style={{
            color: adminMode ? "var(--success)" : "var(--warn)",
            borderColor: adminMode ? "var(--success-line)" : "var(--warn-line)",
            background: adminMode ? "var(--success-dim)" : "var(--warn-dim)",
          }}>
            <Icon name="shield" size={9}/> {adminMode ? "ADMIN" : "READ-ONLY"}
          </span>
        }
      />

      {!adminMode && (
        <div style={{
          padding: "10px 12px", marginBottom: 14,
          background: "var(--warn-dim)", border: "1px solid var(--warn-line)",
          borderRadius: 6, fontSize: 11, color: "var(--warn)",
          display: "flex", gap: 8, alignItems: "flex-start", lineHeight: 1.5,
        }}>
          <Icon name="lock" size={11} style={{ marginTop: 2, flexShrink: 0 }}/>
          <span><strong style={{ fontWeight: 500 }}>{t("pe.pol.adminReq")}</strong> {t("pe.pol.adminMsg")}</span>
        </div>
      )}

      <Field label="policy.heterogeneous_review" tooltip={t("pe.pol.tip.het")} locked={disabled}>
        <SegmentedField
          value={p.heterogeneous_review}
          onChange={v => setP(pp => { pp.policy.heterogeneous_review = v; })}
          options={[
            { value: "relaxed", label: "relaxed" },
            { value: "standard", label: "standard" },
            { value: "strict", label: "strict" },
          ]}
          disabled={disabled}
        />
      </Field>

      <Field label="policy.memory_write" tooltip={t("pe.pol.tip.mem")} locked={disabled}>
        <SegmentedField
          value={p.memory_write}
          onChange={v => setP(pp => { pp.policy.memory_write = v; })}
          options={[
            { value: "open", label: "open" },
            { value: "gated_by_provenance", label: "gated_by_provenance" },
            { value: "disabled", label: "disabled" },
          ]}
          disabled={disabled}
        />
      </Field>

      <Field label="policy.redact_prompts" tooltip={t("pe.pol.tip.redact")} locked={disabled}>
        <div style={{ display: "flex", gap: 6 }}>
          {[true, false].map(v => (
            <button key={String(v)} disabled={disabled}
              onClick={() => setP(pp => { pp.policy.redact_prompts = v; })}
              style={{
                padding: "6px 12px",
                background: p.redact_prompts === v ? "var(--accent-dim)" : "var(--bg-sunken)",
                border: `1px solid ${p.redact_prompts === v ? "var(--accent-line)" : "var(--border)"}`,
                borderRadius: 6, cursor: disabled ? "not-allowed" : "pointer",
                opacity: disabled ? 0.55 : 1,
                fontFamily: "var(--font-mono)", fontSize: 11,
                color: p.redact_prompts === v ? "var(--accent)" : "var(--fg-muted)",
              }}>
              <Icon name={v ? "check" : "ban"} size={10}/> {v ? "true" : "false"}
            </button>
          ))}
        </div>
      </Field>
    </div>
  );
};

const SegmentedField = ({ value, onChange, options, disabled }) => (
  <div style={{
    display: "inline-flex", padding: 2, gap: 2,
    background: "var(--bg-sunken)",
    border: "1px solid var(--border)",
    borderRadius: 6,
    opacity: disabled ? 0.55 : 1,
    pointerEvents: disabled ? "none" : "auto",
  }}>
    {options.map(opt => {
      const active = opt.value === value;
      return (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          style={{
            height: 24, padding: "0 12px",
            background: active ? "var(--bg-panel)" : "transparent",
            border: active ? "1px solid var(--border-strong)" : "1px solid transparent",
            color: active ? "var(--fg)" : "var(--fg-muted)",
            fontFamily: "var(--font-mono)",
            fontSize: 11, borderRadius: 4, cursor: "pointer",
            fontWeight: active ? 500 : 400,
          }}
        >
          {opt.label}
        </button>
      );
    })}
  </div>
);

Object.assign(window, {
  ManifestSection, ObjectivesSection, TeamSection, EvaluationSection,
  BudgetSection, GatesSection, PolicySection,
  ChipMultiSelect, TemperatureGrid, BudgetDonut, SegmentedField,
});
