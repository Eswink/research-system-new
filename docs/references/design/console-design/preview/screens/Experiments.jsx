/* Experiments — queue + variable matrix + scheduler
   Views: queue (list) / matrix (variable grid) / calendar */

const ExperimentsScreen = () => {
  const { t } = useI18n();
  const [view, setView] = useState("queue");
  const [selectedId, setSelectedId] = useState(FIX_EXPERIMENT_QUEUE[0].id);
  const [drawer, setDrawer] = useState(null);
  const [q, setQ] = useState("");
  const selected = FIX_EXPERIMENT_QUEUE.find(e => e.id === selectedId);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("exp.title")} subtitle={t("exp.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("exp.search")} width={220}/>
        <ViewSwitcher value={view} onChange={setView} views={[
          { value: "queue", label: t("exp.viewQueue"), icon: "menu" },
          { value: "matrix", label: t("exp.viewMatrix"), icon: "square" },
          { value: "calendar", label: t("exp.viewCalendar"), icon: "clock" },
        ]}/>
        <button className="btn primary sm" onClick={() => setDrawer({ mode: "create" })}>
          <Icon name="plus" size={11}/> {t("exp.new")}
        </button>
      </PageToolbar>

      {view === "queue" && (
        <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 12, flex: 1, minHeight: 0 }}>
          <ExperimentQueue queue={FIX_EXPERIMENT_QUEUE} selectedId={selectedId} onSelect={setSelectedId}/>
          <ExperimentDetail experiment={selected}/>
        </div>
      )}
      {view === "matrix" && <ExperimentMatrix experiments={FIX_EXPERIMENT_QUEUE}/>}
      {view === "calendar" && <ExperimentCalendar experiments={FIX_EXPERIMENT_QUEUE}/>}

      <Drawer open={!!drawer} onClose={() => setDrawer(null)}
        title={t("exp.new")}
        subtitle={t("exp.newSub")}
        width={560}
        footer={
          <>
            <button className="btn ghost" onClick={() => setDrawer(null)}>{t("act.cancel")}</button>
            <div style={{ marginLeft: "auto", fontSize: 11, color: "var(--fg-muted)", marginRight: 12 }}>
              <span className="mono">{t("exp.totalRuns")}</span> <strong style={{ color: "var(--accent)" }}>96</strong>
            </div>
            <button className="btn primary" onClick={() => setDrawer(null)}><Icon name="play" size={11}/> {t("exp.queueRun")}</button>
          </>
        }>
        <ExperimentForm/>
      </Drawer>
    </div>
  );
};

const ExpStatusBadge = ({ status }) => {
  const map = {
    QUEUED:    { tone: "neutral", icon: "circle-dash", label: "QUEUED",   dashed: true },
    RUNNING:   { tone: "info",    icon: "spin",        label: "RUNNING" },
    PAUSED:    { tone: "warn",    icon: "pause",       label: "PAUSED",  filled: true },
    SUCCEEDED: { tone: "success", icon: "check",       label: "DONE",    filled: true },
    FAILED:    { tone: "danger",  icon: "x",           label: "FAILED",  filled: true },
  };
  const cfg = map[status];
  if (cfg.tone === "info") return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "1px 7px", height: 18, borderRadius: 4, fontSize: 11, fontFamily: "var(--font-mono)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", border: "1px solid var(--accent-line)", background: "var(--accent-dim)", color: "var(--accent)" }}>
      <Icon name={cfg.icon} size={10}/> {cfg.label}
    </span>
  );
  return <StatusBadge {...cfg}/>;
};

const PriorityChip = ({ priority }) => {
  const color = priority === "high" ? "var(--danger)" : priority === "medium" ? "var(--warn)" : "var(--fg-muted)";
  return (
    <span className="chip" style={{ color, borderColor: `${color}44` }}>
      P{priority === "high" ? "0" : priority === "medium" ? "1" : "2"} · {priority}
    </span>
  );
};

const ExperimentQueue = ({ queue, selectedId, onSelect }) => { const { t } = useI18n(); return (
  <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
    <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
      <Icon name="flask" size={12} style={{ color: "var(--fg-muted)" }}/>
      <span style={{ fontSize: 12, fontWeight: 500 }}>{t("exp.queue")}</span>
      <span className="chip">{queue.length}</span>
      <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
        {queue.filter(e => e.status === "RUNNING").length} {t("exp.running")} · {queue.filter(e => e.status === "QUEUED").length} {t("exp.queued")}
      </span>
    </div>
    <div style={{ flex: 1, overflow: "auto" }}>
      {queue.map(e => {
        const selected = e.id === selectedId;
        return (
          <div key={e.id} onClick={() => onSelect(e.id)} style={{
            padding: "12px 14px", cursor: "pointer",
            background: selected ? "var(--bg-hover)" : "transparent",
            borderLeft: `2px solid ${selected ? "var(--accent)" : "transparent"}`,
            borderBottom: "1px solid var(--border-subtle)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <ExpStatusBadge status={e.status}/>
              <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", fontWeight: 500 }}>{e.label}</span>
              <PriorityChip priority={e.priority}/>
              <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                {e.status === "RUNNING" ? `ETA ${e.eta_min}m` :
                 e.status === "QUEUED" ? `~${e.eta_min}m` :
                 e.status === "PAUSED" ? "paused" :
                 e.duration_s ? `${Math.round(e.duration_s/60)}m` : "—"}
              </span>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 6 }}>
              {Object.entries(e.variables).slice(0, 4).map(([k, v]) => (
                <span key={k} className="chip" style={{ fontSize: 9, height: 15 }}>
                  <span style={{ color: "var(--fg-faint)" }}>{k}:</span> {Array.isArray(v) ? `[${v.length}]` : v}
                </span>
              ))}
            </div>
            {(e.status === "RUNNING" || e.progress > 0) && (
              <div style={{ height: 3, background: "var(--bg-sunken)", borderRadius: 2 }}>
                <div style={{ width: `${e.progress * 100}%`, height: "100%", background: e.status === "FAILED" ? "var(--danger)" : "var(--accent)", borderRadius: 2 }}/>
              </div>
            )}
          </div>
        );
      })}
    </div>
  </div>
)};

const ExperimentDetail = ({ experiment: e }) => { const { t } = useI18n();
  const totalRuns = useMemo(() => {
    return Object.values(e.variables).reduce((acc, v) => acc * (Array.isArray(v) ? v.length : 1), 1);
  }, [e]);

  return (
    <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{t("exp.headExperiment")}</div>
        <div style={{ fontSize: 14, fontWeight: 500, fontFamily: "var(--font-mono)" }}>{e.label}</div>
        <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
          <ExpStatusBadge status={e.status}/>
          <PriorityChip priority={e.priority}/>
          <DigestText value={e.id} length={12} prefix={false}/>
        </div>
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
        {/* Variable matrix */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase" }}>{t("exp.variables")}</div>
            <span className="chip">{totalRuns} {t("exp.cartesian")}</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {Object.entries(e.variables).map(([k, v]) => (
              <div key={k} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 6 }}>
                <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", minWidth: 100 }}>{k}</span>
                <div style={{ flex: 1, display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {(Array.isArray(v) ? v : [v]).map((val, i) => (
                    <span key={i} style={{
                      display: "inline-flex", padding: "1px 6px", height: 18,
                      background: "var(--accent-dim)", color: "var(--accent)",
                      borderRadius: 3, fontSize: 10, fontFamily: "var(--font-mono)",
                    }}>{String(val)}</span>
                  ))}
                </div>
                <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>× {Array.isArray(v) ? v.length : 1}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Progress */}
        {e.status === "RUNNING" && (
          <div>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>{t("exp.progress")}</div>
            <div style={{ height: 6, background: "var(--bg-sunken)", borderRadius: 3, overflow: "hidden" }}>
              <div style={{ width: `${e.progress * 100}%`, height: "100%", background: "var(--accent)" }}/>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
              <span>{Math.round(e.progress * 100)}% · {Math.round(e.progress * totalRuns)} / {totalRuns}</span>
              <span>ETA {e.eta_min}m</span>
            </div>
          </div>
        )}

        {(e.failure_reason || e.paused_reason) && (
          <div style={{ padding: 10, background: "var(--warn-dim)", border: "1px solid var(--warn-line)", borderRadius: 6, fontSize: 11, color: "var(--warn)", display: "flex", gap: 8 }}>
            <Icon name="warn-tri" size={12}/> <div>{e.failure_reason || e.paused_reason}</div>
          </div>
        )}

        <div>
          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>{t("exp.meta").toUpperCase()}</div>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 12px", fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
            <span style={{ color: "var(--fg-faint)" }}>{t("lbl.project").toLowerCase()}</span><span>{e.project_id}</span>
            <span style={{ color: "var(--fg-faint)" }}>{t("exp.submitted")}</span><span>{new Date(e.submitted_at).toISOString().replace("T"," ").slice(0,16)}</span>
            <span style={{ color: "var(--fg-faint)" }}>{t("exp.submittedBy")}</span><span>{e.submitted_by}</span>
          </div>
        </div>

        <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
          {e.status === "QUEUED" && <button className="btn primary sm"><Icon name="play" size={10}/> {t("act.runNow")}</button>}
          {e.status === "RUNNING" && <button className="btn sm"><Icon name="pause" size={10}/> {t("act.pause")}</button>}
          {(e.status === "PAUSED" || e.status === "QUEUED") && <button className="btn sm"><Icon name="fork" size={10}/> {t("act.fork")}</button>}
          {e.status === "FAILED" && <button className="btn sm"><Icon name="spin" size={10}/> {t("act.retry")}</button>}
          <button className="btn sm ghost"><Icon name="copy" size={10}/> {t("act.edit")}</button>
          <button className="btn sm ghost" style={{ color: "var(--danger)", marginLeft: "auto" }}><Icon name="x" size={10}/> {t("tl.cancel")}</button>
        </div>
      </div>
    </div>
  );
};

// Full variable-matrix visualization: grid of runs (temp × model, colored by status)
const ExperimentMatrix = ({ experiments }) => { const { t } = useI18n();
  // Focus on the RUNNING sweep as an example
  const exp = experiments.find(e => e.status === "RUNNING") || experiments[0];
  const temps = exp.variables.temperature || [0.2];
  const models = exp.variables.model || ["gpt-4o"];
  const langs = exp.variables.language || ["en"];

  // deterministic cell status
  const status = (i, j, k) => {
    const rn = (Math.sin(i * 3 + j * 7 + k * 13) + 1) / 2;
    const done = Math.min(1, exp.progress + 0.1);
    if (rn < done * 0.7) return "SUCCEEDED";
    if (rn < done * 0.85) return "RUNNING";
    if (rn < done * 0.92) return "FAILED";
    return "PENDING";
  };
  const color = s => s === "SUCCEEDED" ? "var(--success)" : s === "RUNNING" ? "var(--accent)" : s === "FAILED" ? "var(--danger)" : "var(--bg-sunken)";

  return (
    <div className="panel" style={{ padding: 16, flex: 1, overflow: "auto" }}>
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{t("exp.matrixTitle")}</div>
        <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 4 }}>{exp.label}</div>
        <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>
          {t("exp.matrixDesc")}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        {langs.map((lang, li) => (
          <div key={lang}>
            <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--accent)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.08em" }}>
              language · {lang}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: `100px repeat(${temps.length}, 1fr)`, gap: 4, alignItems: "center" }}>
              <div/>
              {temps.map(t => <div key={t} style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", textAlign: "center" }}>temp={t}</div>)}
              {models.map((m, mi) => (
                <React.Fragment key={m}>
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>{m}</div>
                  {temps.map((t, ti) => {
                    const s = status(li, mi, ti);
                    return (
                      <div key={ti} title={`${lang} × ${m} × temp=${t} · ${s}`} style={{
                        height: 32, borderRadius: 4,
                        background: color(s),
                        opacity: s === "PENDING" ? 0.5 : 1,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontFamily: "var(--font-mono)", fontSize: 9,
                        color: s === "PENDING" ? "var(--fg-faint)" : "#fff",
                        border: s === "PENDING" ? "1px dashed var(--border-strong)" : "none",
                      }}>
                        {s === "SUCCEEDED" && "✓"}
                        {s === "RUNNING" && "…"}
                        {s === "FAILED" && "✕"}
                        {s === "PENDING" && "○"}
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div style={{ marginTop: 24, padding: 12, background: "var(--bg-raised)", borderRadius: 6, display: "flex", gap: 16, fontSize: 11, fontFamily: "var(--font-mono)" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}><div style={{ width: 14, height: 14, background: "var(--success)", borderRadius: 3 }}/> {t("exp.cellSucceeded")}</span>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}><div style={{ width: 14, height: 14, background: "var(--accent)", borderRadius: 3 }}/> {t("exp.cellRunning")}</span>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}><div style={{ width: 14, height: 14, background: "var(--danger)", borderRadius: 3 }}/> {t("exp.cellFailed")}</span>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}><div style={{ width: 14, height: 14, background: "var(--bg-sunken)", border: "1px dashed var(--border-strong)", borderRadius: 3 }}/> {t("exp.cellPending")}</span>
      </div>
    </div>
  );
};

const ExperimentCalendar = ({ experiments }) => { const { t } = useI18n();
  const days = 7;
  const hours = [8, 10, 12, 14, 16, 18, 20, 22];
  return (
    <div className="panel" style={{ padding: 16, flex: 1, overflow: "auto" }}>
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>{t("exp.calTitle")}</div>
        <div style={{ fontSize: 15, fontWeight: 500 }}>{t("exp.calRange")}</div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: `56px repeat(${days}, 1fr)`, gap: 2 }}>
        <div/>
        {Array.from({length: days}).map((_, d) => {
          const date = new Date(2026, 7, 26 + d);
          return <div key={d} style={{ padding: "4px 6px", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", textAlign: "center", background: "var(--bg-raised)", borderRadius: 4 }}>
            <div>{["MON","TUE","WED","THU","FRI","SAT","SUN"][date.getDay() === 0 ? 6 : date.getDay()-1]}</div>
            <div style={{ fontSize: 11, color: "var(--fg)" }}>{date.getDate()}</div>
          </div>;
        })}
        {hours.map(h => (
          <React.Fragment key={h}>
            <div style={{ padding: "6px", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", textAlign: "right" }}>{String(h).padStart(2,"0")}:00</div>
            {Array.from({length: days}).map((_, d) => {
              // Sprinkle experiments deterministically
              const has = (d * 7 + h) % 5 < 2;
              const exp = experiments[(d + h) % experiments.length];
              return (
                <div key={d} style={{
                  minHeight: 44, padding: 6,
                  background: has ? "var(--accent-dim)" : "var(--bg-sunken)",
                  border: `1px solid ${has ? "var(--accent-line)" : "var(--border-subtle)"}`,
                  borderRadius: 4,
                }}>
                  {has && (
                    <>
                      <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--accent)", marginBottom: 2 }}>{exp.label.slice(0, 22)}</div>
                      <div style={{ fontSize: 8, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>~{exp.eta_min || Math.round((exp.duration_s || 1200) / 60)}m</div>
                    </>
                  )}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

const ExperimentForm = () => { const { t } = useI18n();
  const [label, setLabel] = useState("");
  const [priority, setPriority] = useState("medium");
  const [langs, setLangs] = useState(["en", "es", "zh"]);
  const [temps, setTemps] = useState(["0.2", "0.4"]);
  const [models, setModels] = useState(["gpt-4o", "sonnet-4"]);
  const [samples, setSamples] = useState(200);

  const total = langs.length * temps.length * models.length;

  return (
    <div>
      <FormRow label={t("lbl.label")} required hint={t("exp.form.labelHint")}>
        <TextInput value={label} onChange={setLabel} mono placeholder="my-experiment-name"/>
      </FormRow>
      <FormRow label={t("lbl.project")}>
        <Select value="proj_01K5FZ8G3X2QN4M" onChange={() => {}} options={FIX_PROJECTS.map(p => ({ value: p.id, label: p.name }))}/>
      </FormRow>
      <FormRow label={t("lbl.priority")}>
        <Select value={priority} onChange={setPriority} options={[
          { value: "high", label: t("exp.form.priorityHigh") },
          { value: "medium", label: t("exp.form.priorityMid") },
          { value: "low", label: t("exp.form.priorityLow") },
        ]}/>
      </FormRow>

      <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginTop: 20, marginBottom: 8 }}>
        {t("exp.form.sweep")}
      </div>

      <FormRow label={t("lbl.languages")} hint={`${langs.length} ${t("exp.form.langHint")}`}>
        <TagInput tags={langs} onChange={setLangs}/>
      </FormRow>
      <FormRow label={t("lbl.temperatures")} hint={`${temps.length} ${t("exp.form.langHint")}`}>
        <TagInput tags={temps} onChange={setTemps}/>
      </FormRow>
      <FormRow label={t("lbl.models")} hint={`${models.length} ${t("exp.form.langHint")}`}>
        <TagInput tags={models} onChange={setModels}/>
      </FormRow>
      <FormRow label={t("lbl.samples")} hint={t("exp.form.samplesHint")}>
        <TextInput value={samples} onChange={v => setSamples(parseInt(v) || 0)} mono/>
      </FormRow>

      <div style={{ padding: 12, background: "var(--accent-dim)", border: "1px solid var(--accent-line)", borderRadius: 6, marginTop: 12 }}>
        <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--accent)", letterSpacing: "0.08em", marginBottom: 4 }}>{t("exp.projection")}</div>
        <div style={{ display: "flex", gap: 20, alignItems: "baseline" }}>
          <div>
            <div style={{ fontSize: 22, fontFamily: "var(--font-mono)", color: "var(--accent)" }}>{total}</div>
            <div style={{ fontSize: 10, color: "var(--fg-muted)" }}>{t("exp.cells")}</div>
          </div>
          <div>
            <div style={{ fontSize: 22, fontFamily: "var(--font-mono)" }}>{(total * samples).toLocaleString()}</div>
            <div style={{ fontSize: 10, color: "var(--fg-muted)" }}>{t("exp.samples")}</div>
          </div>
          <div>
            <div style={{ fontSize: 22, fontFamily: "var(--font-mono)" }}>~${(total * samples * 0.008).toFixed(0)}</div>
            <div style={{ fontSize: 10, color: "var(--fg-muted)" }}>{t("exp.estCost")}</div>
          </div>
          <div>
            <div style={{ fontSize: 22, fontFamily: "var(--font-mono)" }}>~{Math.round(total * samples * 0.4 / 60)}m</div>
            <div style={{ fontSize: 10, color: "var(--fg-muted)" }}>{t("exp.estDuration")}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { ExperimentsScreen });
