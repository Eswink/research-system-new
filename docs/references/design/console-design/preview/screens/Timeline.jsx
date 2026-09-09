/* Screen 5: Run Timeline — the signature view.
   Status bar / phase swimlanes + event stream / detail drawer. */

const TimelineScreen = () => {
  const { t } = useI18n();
  const [selectedEvent, setSelectedEvent] = useState(FIX_EVENTS[3]); // tool.called (has model + cost + latency)
  const [filter, setFilter] = useState("all");
  const [liveState, setLiveState] = useState("live"); // live | reconnecting | behind
  const [autoScroll, setAutoScroll] = useState(true);

  const filteredEvents = filter === "all" ? FIX_EVENTS : FIX_EVENTS.filter(e => e.type.startsWith(filter));
  const totalDuration = 72; // phase units

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      {/* ── Top status bar ─────────────────────────────── */}
      <div className="panel" style={{ padding: "12px 16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RunStateBadge state="RUNNING"/>
            <span style={{ fontSize: 13, fontWeight: 500 }}>{FIX_RUN.id}</span>
          </div>
          <div className="vr" style={{ height: 20 }}/>
          <DigestText value={FIX_RUN.manifest_digest} label="manifest:" length={12}/>
          <DigestText value={FIX_RUN.protocol_digest} label="protocol:" length={10}/>
          <div className="vr" style={{ height: 20 }}/>
          <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
            <span><span style={{ color: "var(--fg-faint)" }}>{t("lbl.started").toLowerCase()}</span> 2026-08-27T14:03:22Z</span>
            <span><span style={{ color: "var(--fg-faint)" }}>{t("dr.elapsed")}</span> 00:38:12</span>
            <span><span style={{ color: "var(--fg-faint)" }}>{t("lbl.tasks").toLowerCase()}</span> {FIX_RUN.progress.tasks_done}/{FIX_RUN.progress.tasks_total} · <span style={{ color: "var(--accent)" }}>{FIX_RUN.progress.tasks_running} {t("exp.running")}</span> · <span style={{ color: "var(--danger)" }}>{FIX_RUN.progress.tasks_failed} {t("rh.failed")}</span></span>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            <LiveIndicator state={liveState}/>
            <div className="vr" style={{ height: 20 }}/>
            <button className="btn sm"><Icon name="pause" size={10}/> {t("act.pause")}</button>
            <button className="btn sm"><Icon name="fork" size={10}/> {t("act.fork")}</button>
            <button className="btn sm" style={{ color: "var(--danger)" }}><Icon name="stop" size={10}/> {t("tl.cancel")}</button>
          </div>
        </div>
      </div>

      {/* ── Middle: Swimlanes + Event stream ──────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.3fr) minmax(0, 1fr)", gap: 12, flex: 1, minHeight: 0 }}>
        {/* Swimlanes */}
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="hex" size={12} style={{ color: "var(--fg-muted)" }}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("tl.phasesTasks")}</span>
            <span className="chip">{FIX_PHASES.reduce((a,p) => a + p.tasks.length, 0)}</span>
            <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
              {["SUCCEEDED","RUNNING","FAILED","PENDING"].map(s => {
                const count = FIX_PHASES.flatMap(p => p.tasks).filter(t => t.status === s).length;
                return (
                  <span key={s} className="chip" style={{
                    color: s === "SUCCEEDED" ? "var(--success)" : s === "RUNNING" ? "var(--accent)" : s === "FAILED" ? "var(--danger)" : "var(--fg-faint)",
                    borderColor: s === "SUCCEEDED" ? "var(--success-line)" : s === "RUNNING" ? "var(--accent-line)" : s === "FAILED" ? "var(--danger-line)" : "var(--border)",
                  }}>{s.toLowerCase()} {count}</span>
                );
              })}
            </div>
          </div>
          <div style={{ flex: 1, overflow: "auto", padding: "8px 4px" }}>
            {/* Time ruler */}
            <div style={{ position: "sticky", top: 0, background: "var(--bg-panel)", zIndex: 2, padding: "4px 12px 4px 152px", borderBottom: "1px solid var(--border-subtle)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                {[0,10,20,30,40,50,60,70].map(t => <span key={t}>+{String(t).padStart(2,"0")}m</span>)}
              </div>
              <div style={{ position: "relative", height: 4 }}>
                {/* Now indicator at 68m */}
                <div style={{ position: "absolute", left: `${68/totalDuration*100}%`, top: 0, bottom: -800, width: 1, background: "var(--accent)", opacity: 0.4 }}/>
                <div style={{ position: "absolute", left: `${68/totalDuration*100}%`, top: -2, transform: "translateX(-50%)", fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--accent)", background: "var(--bg-panel)", padding: "0 4px" }}>NOW</div>
              </div>
            </div>

            {FIX_PHASES.map(phase => (
              <div key={phase.id} style={{ marginTop: 8 }}>
                <div style={{ padding: "4px 12px", fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", letterSpacing: "0.06em", textTransform: "uppercase", background: "var(--bg-raised)" }}>
                  {phase.name} <span style={{ color: "var(--fg-faint)", marginLeft: 6 }}>+{phase.start}m → +{phase.end}m</span>
                </div>
                {phase.tasks.map(task => {
                  const agent = FIX_AGENTS.find(a => a.id === task.agent_id);
                  const statusColor = {
                    SUCCEEDED: "var(--success)", RUNNING: "var(--accent)",
                    FAILED: "var(--danger)", PENDING: "var(--fg-faint)",
                  }[task.status];
                  return (
                    <div key={task.id} style={{
                      display: "grid", gridTemplateColumns: "144px 1fr", gap: 8,
                      padding: "3px 12px",
                      alignItems: "center",
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 5, minWidth: 0 }}>
                        <div style={{ width: 5, height: 5, borderRadius: "50%", background: statusColor, flexShrink: 0 }}/>
                        <span style={{ fontSize: 11, color: "var(--fg-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{task.name}</span>
                        {task.attempt > 1 && <span title={`attempt ${task.attempt}`} style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--warn)", background: "var(--warn-dim)", padding: "0 3px", borderRadius: 2, flexShrink: 0 }}>×{task.attempt}</span>}
                      </div>
                      <div style={{ position: "relative", height: 16 }}>
                        <div style={{
                          position: "absolute",
                          left: `${task.start/totalDuration*100}%`,
                          width: `${(task.end-task.start)/totalDuration*100}%`,
                          top: 3, height: 10,
                          background: task.status === "PENDING" ? "transparent" :
                                      task.status === "RUNNING" ? `linear-gradient(90deg, ${statusColor}, ${statusColor}66)` : statusColor,
                          border: task.status === "PENDING" ? `1px dashed ${statusColor}` : "none",
                          borderRadius: 2,
                          boxShadow: task.status === "RUNNING" ? `0 0 12px ${statusColor}44` : "none",
                        }}/>
                        {task.status === "RUNNING" && (
                          <div style={{
                            position: "absolute",
                            left: `${task.start/totalDuration*100}%`,
                            width: `${(task.end-task.start)/totalDuration*100}%`,
                            top: 3, height: 10,
                            background: "repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(255,255,255,0.08) 3px, rgba(255,255,255,0.08) 6px)",
                            borderRadius: 2,
                          }}/>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Event stream */}
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="menu" size={12} style={{ color: "var(--fg-muted)" }}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("tl.eventStream")}</span>
            <span className="chip">{filteredEvents.length}</span>
            <div style={{ marginLeft: "auto", display: "flex", gap: 4 }}>
              {[["all",t("tl.filterAll")],["task","task"],["tool","tool"],["policy","policy"],["evidence","evidence"]].map(([v,l]) => (
                <button key={v} onClick={() => setFilter(v)} className="btn sm ghost" style={{
                  color: filter === v ? "var(--accent)" : "var(--fg-muted)",
                  background: filter === v ? "var(--accent-dim)" : "transparent",
                }}>{l}</button>
              ))}
            </div>
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {filteredEvents.map((ev, i) => (
              <EventRow key={ev.event_id} ev={ev} selected={selectedEvent && selectedEvent.event_id === ev.event_id}
                onClick={() => setSelectedEvent(ev)}
                isLatest={i === filteredEvents.length - 1} />
            ))}
          </div>
          <div style={{ padding: "6px 12px", borderTop: "1px solid var(--border)", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", display: "flex", justifyContent: "space-between" }}>
            <span>{t("tl.cursor")} evt_01K5FZ8H015 · {t("tl.resumable")}</span>
            <label style={{ display: "flex", alignItems: "center", gap: 4, cursor: "pointer" }}>
              <input type="checkbox" checked={autoScroll} onChange={e => setAutoScroll(e.target.checked)} style={{ accentColor: "var(--accent)" }}/>
              {t("tl.autoScroll")}
            </label>
          </div>
        </div>
      </div>

      {/* ── Bottom drawer: event detail ─────────────────── */}
      {selectedEvent && <EventDrawer ev={selectedEvent} onClose={() => setSelectedEvent(null)}/>}
    </div>
  );
};

// ─── Event row ──────────────────────────────────────────
const EventRow = ({ ev, selected, onClick, isLatest }) => {
  const typeStyle = getEventTypeStyle(ev.type);
  const actorLabel = ev.actor.kind === "agent" ? FIX_AGENTS.find(a => a.id === ev.actor.id)?.name || ev.actor.id
                   : ev.actor.kind === "tool" ? ev.actor.id
                   : ev.actor.kind === "policy" ? "policy"
                   : ev.actor.kind === "user" ? ev.actor.id
                   : "system";
  return (
    <div onClick={onClick} style={{
      display: "grid", gridTemplateColumns: "80px 18px 1fr auto",
      gap: 8, padding: "5px 12px",
      borderBottom: "1px solid var(--border-subtle)",
      background: selected ? "var(--bg-hover)" : "transparent",
      cursor: "pointer",
      alignItems: "center",
      animation: isLatest ? "stream-in 400ms ease-out" : undefined,
    }}>
      <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{ev.occurred_at.slice(11,19)}</span>
      <Icon name={typeStyle.icon} size={11} style={{ color: typeStyle.color }}/>
      <div style={{ minWidth: 0, display: "flex", alignItems: "center", gap: 6 }}>
        <span className="mono" style={{ fontSize: 11, color: typeStyle.color, fontWeight: 500 }}>{ev.type}</span>
        <span style={{ fontSize: 11, color: "var(--fg-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {getEventSummary(ev)}
        </span>
      </div>
      <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{actorLabel}</span>
    </div>
  );
};

const getEventTypeStyle = (type) => {
  if (type.startsWith("task.failed")) return { icon: "x", color: "var(--danger)" };
  if (type.startsWith("task.attempt")) return { icon: "clock", color: "var(--warn)" };
  if (type.startsWith("task")) return { icon: "hex", color: "var(--fg-muted)" };
  if (type.startsWith("agent")) return { icon: "circle", color: "var(--accent)" };
  if (type.startsWith("tool")) return { icon: "square", color: "var(--fg-muted)" };
  if (type.startsWith("policy")) return { icon: "shield", color: "var(--accent)" };
  if (type.startsWith("evidence")) return { icon: "diamond", color: "var(--success)" };
  if (type.startsWith("budget")) return { icon: "diamond", color: "var(--warn)" };
  if (type.startsWith("claim")) return { icon: "check", color: "var(--success)" };
  if (type.startsWith("gate")) return { icon: "shield", color: "var(--unknown)" };
  if (type.startsWith("experiment")) return { icon: "flask", color: "var(--accent)" };
  return { icon: "circle-o", color: "var(--fg-muted)" };
};

const getEventSummary = (ev) => {
  const p = ev.payload || {};
  if (ev.type === "task.started") return `${p.phase || ""} ${p.subtasks ? `(${p.subtasks} subtasks)` : ""}`;
  if (ev.type === "agent.spawned") return `${p.agent_id} using ${p.model_id}`;
  if (ev.type === "tool.called") return `${p.tool} · model=${p.model_id}`;
  if (ev.type === "tool.returned") return `${p.results} results → artifact ${p.artifact_id}`;
  if (ev.type === "evidence.proposed") return `${p.relation} ${p.claim_id} @ strength ${p.strength}`;
  if (ev.type === "policy.decision") return `${p.decision} · ${p.policy_id}`;
  if (ev.type === "budget.reserved") return `${p.resource} · $${(p.amount_minor/100000).toFixed(2)}`;
  if (ev.type === "experiment.started") return `${p.experiment_run_id.slice(0,24)}…`;
  if (ev.type === "task.attempt") return `attempt ${p.attempt} · ${p.previous_error_class} · backoff ${p.backoff_ms}ms`;
  if (ev.type === "claim.upgraded") return `${p.claim_id} · ${p.from_status} → ${p.to_status}`;
  if (ev.type === "gate.opened") return `${p.gate_type} · ${p.reason}`;
  if (ev.type === "task.failed") return `${p.error_class} · ${p.error_message_redacted}`;
  return "";
};

// ─── Event drawer ───────────────────────────────────────
const EventDrawer = ({ ev, onClose }) => { const { t } = useI18n();
  const typeStyle = getEventTypeStyle(ev.type);
  const agent = ev.actor.kind === "agent" ? FIX_AGENTS.find(a => a.id === ev.actor.id) : null;
  const modelId = ev.payload?.model_id || agent?.model_binding?.model_id || agent?.resolved_model_id;
  const model = modelId ? FIX_MODELS.find(m => m.id === modelId) : null;

  return (
    <div className="panel" style={{ padding: 0, maxHeight: 280, overflow: "auto", animation: "fadeIn 200ms ease-out" }}>
      <div style={{ padding: "10px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
        <Icon name={typeStyle.icon} size={13} style={{ color: typeStyle.color }}/>
        <span className="mono" style={{ fontSize: 12, color: typeStyle.color, fontWeight: 500 }}>{ev.type}</span>
        <DigestText value={ev.event_id} label="event:" length={16}/>
        <DigestText value={ev.trace_id} label="trace:" length={10}/>
        <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{ev.occurred_at}</span>
        <button className="btn sm ghost" style={{ marginLeft: "auto" }} onClick={onClose}><Icon name="x" size={10}/></button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 0 }}>
        <DrawerSection title={t("tl.evActor")}>
          <KV k="kind" v={ev.actor.kind}/>
          {ev.actor.id && <KV k="id" v={ev.actor.id}/>}
          {agent && <KV k="name" v={agent.name}/>}
          {agent && <KV k="role" v={FIX_ROLES.find(r=>r.id===agent.role_id)?.name || "-"}/>}
        </DrawerSection>
        <DrawerSection title={t("tl.evTaskScope")}>
          <KV k="scope" v={ev.scope}/>
          {ev.task_id && <KV k="task_id" v={ev.task_id}/>}
          <KV k="run_id" v={FIX_RUN.id.slice(0, 22)}/>
        </DrawerSection>
        <DrawerSection title={model ? t("tl.evModel") : t("tl.evMetrics")}>
          {model ? (
            <>
              <KV k="model_id" v={model.model_id}/>
              <KV k="returned" v={model.returned_model_name} warn={model.drift_alert}/>
              <KV k="fingerprint" v={model.system_fingerprint || "not provided"} unknown={!model.system_fingerprint}/>
            </>
          ) : (
            <>
              {ev.cost_minor != null && <KV k="cost" v={`$${(ev.cost_minor/100000).toFixed(4)}`}/>}
              {ev.latency_ms != null && <KV k="latency" v={`${ev.latency_ms}ms`}/>}
              {ev.payload?.artifact_id && <KV k="artifact" v={ev.payload.artifact_id}/>}
            </>
          )}
        </DrawerSection>
      </div>
      <div style={{ borderTop: "1px solid var(--border)" }}>
        <div style={{ padding: "6px 16px", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="eye-off" size={10}/> {t("tl.evPayload")}
          <span style={{ marginLeft: "auto", color: "var(--warn)" }}>{t("tl.evRedacted")}</span>
        </div>
        <pre style={{
          margin: 0, padding: "8px 16px 14px",
          fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.55,
          color: "var(--fg-muted)", background: "var(--bg-sunken)",
          overflow: "auto", maxHeight: 140,
        }}>{JSON.stringify(ev.payload, null, 2)}</pre>
      </div>
    </div>
  );
};

const DrawerSection = ({ title, children }) => (
  <div style={{ padding: "10px 16px", borderRight: "1px solid var(--border)" }}>
    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>{title}</div>
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>{children}</div>
  </div>
);

const KV = ({ k, v, unknown, warn }) => (
  <div style={{ display: "grid", gridTemplateColumns: "88px 1fr", gap: 8, fontSize: 11, lineHeight: 1.4 }}>
    <span style={{ color: "var(--fg-faint)", fontFamily: "var(--font-mono)" }}>{k}</span>
    <span className="mono" style={{ color: unknown ? "var(--unknown)" : warn ? "var(--warn)" : "var(--fg)" }} title={typeof v === "string" ? v : ""}>{v}</span>
  </div>
);

Object.assign(window, { TimelineScreen });
