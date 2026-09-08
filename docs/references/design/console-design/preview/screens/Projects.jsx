/* Projects — portfolio management with list + CRUD drawer.
   Views: list / board (by status) / grid.
   Row actions: open · edit · duplicate · archive · delete (soft). */

const ProjectsScreen = () => {
  const { t } = useI18n();
  const [view, setView] = useState("list");
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [drawer, setDrawer] = useState(null); // { mode: 'view'|'create'|'edit', project? }
  const [ctx, setCtx] = useState(null); // { x, y, project }
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [projectsLocal, setProjectsLocal] = useState(FIX_PROJECTS);

  const filtered = useMemo(() => {
    let list = projectsLocal;
    if (statusFilter !== "all") list = list.filter(p => p.status === statusFilter);
    if (q.trim()) {
      const s = q.toLowerCase();
      list = list.filter(p => p.name.toLowerCase().includes(s) || p.slug.toLowerCase().includes(s) || p.tags.some(t => t.toLowerCase().includes(s)));
    }
    return list;
  }, [projectsLocal, statusFilter, q]);

  const counts = useMemo(() => {
    const c = { all: projectsLocal.length };
    projectsLocal.forEach(p => c[p.status] = (c[p.status] || 0) + 1);
    return c;
  }, [projectsLocal]);

  const openMenu = (e, project) => {
    e.preventDefault();
    setCtx({ x: e.clientX, y: e.clientY, project });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      {/* Header */}
      <PageToolbar title={t("proj.title")} subtitle={t("proj.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("proj.search")} width={240}/>
        <ViewSwitcher value={view} onChange={setView} views={[
          { value: "list", label: t("proj.viewList"), icon: "menu" },
          { value: "board", label: t("proj.viewBoard"), icon: "hex" },
          { value: "grid", label: t("proj.viewGrid"), icon: "square" },
        ]}/>
        <button className="btn primary sm" onClick={() => setDrawer({ mode: "create" })}>
          <Icon name="plus" size={11}/> {t("proj.new")}
        </button>
      </PageToolbar>

      {/* Status filter tabs */}
      <div style={{ display: "flex", gap: 4, borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
        {[
          ["all", t("lbl.all")],
          ["RUNNING", t("proj.filterRunning")],
          ["PAUSED", t("proj.filterPaused")],
          ["DRAFT", t("proj.filterDraft")],
          ["SUCCEEDED", t("proj.filterSucceeded")],
          ["FAILED", t("proj.filterFailed")],
          ["ARCHIVED", t("proj.filterArchived")],
        ].map(([s, l]) => (
          <button key={s} onClick={() => setStatusFilter(s)} className="btn sm ghost" style={{
            background: statusFilter === s ? "var(--bg-hover)" : "transparent",
            color: statusFilter === s ? "var(--fg)" : "var(--fg-muted)",
            fontWeight: statusFilter === s ? 500 : 400,
            borderColor: "transparent",
          }}>
            {l} <span style={{ marginLeft: 4, color: "var(--fg-faint)", fontFamily: "var(--font-mono)", fontSize: 10 }}>{counts[s] || 0}</span>
          </button>
        ))}
      </div>

      {/* Views */}
      <div style={{ flex: 1, minHeight: 0, overflow: "auto" }}>
        {filtered.length === 0 && (
          <EmptyState
            icon="hex"
            kicker={t("proj.emptyKicker")}
            title={q ? t("proj.emptyMatchTitle").replace("{q}", q) : t("proj.emptyFilterTitle")}
            description={q ? t("proj.emptyMatchDesc") : t("proj.emptyFilterDesc")}
            cta={{ label: t("proj.new"), icon: "plus", onClick: () => setDrawer({ mode: "create" }) }}
          />
        )}
        {filtered.length > 0 && view === "list" && (
          <ProjectsListView projects={filtered} onOpen={p => setDrawer({ mode: "view", project: p })} onContextMenu={openMenu}/>
        )}
        {filtered.length > 0 && view === "board" && (
          <ProjectsBoardView projects={filtered} onOpen={p => setDrawer({ mode: "view", project: p })} onContextMenu={openMenu}/>
        )}
        {filtered.length > 0 && view === "grid" && (
          <ProjectsGridView projects={filtered} onOpen={p => setDrawer({ mode: "view", project: p })} onContextMenu={openMenu}/>
        )}
      </div>

      {/* Drawer */}
      <Drawer open={!!drawer} onClose={() => setDrawer(null)}
        title={drawer?.mode === "create" ? t("proj.createTitle") : drawer?.mode === "edit" ? t("proj.editTitle") : drawer?.project?.name || ""}
        subtitle={drawer?.mode === "create" ? t("proj.createSubtitle") : drawer?.mode === "edit" ? t("proj.editSubtitle") : t("proj.detailSubtitle")}
        width={drawer?.mode === "view" ? 560 : 480}
        footer={drawer?.mode === "view" ? (
          <>
            <button className="btn" onClick={() => setDrawer({ mode: "edit", project: drawer.project })}><Icon name="copy" size={11}/> {t("act.edit")}</button>
            <button className="btn ghost" onClick={() => {
              setProjectsLocal(prev => [{ ...drawer.project, id: "proj_dup_" + Date.now(), name: drawer.project.name + " (copy)", status: "DRAFT", created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, ...prev]);
              setDrawer(null);
            }}><Icon name="fork" size={11}/> {t("act.duplicate")}</button>
            <button className="btn ghost" style={{ color: "var(--danger)", marginLeft: "auto" }} onClick={() => { setConfirmDelete(drawer.project); setDrawer(null); }}>
              <Icon name="x" size={11}/> {t("act.delete")}
            </button>
          </>
        ) : (
          <>
            <button className="btn ghost" onClick={() => setDrawer(null)}>{t("act.cancel")}</button>
            <button className="btn primary" style={{ marginLeft: "auto" }} onClick={() => setDrawer(null)}>
              <Icon name="check" size={11}/> {drawer?.mode === "create" ? t("proj.createCta") : t("act.saveChanges")}
            </button>
          </>
        )}>
        {drawer?.mode === "view" && <ProjectDetail project={drawer.project}/>}
        {(drawer?.mode === "create" || drawer?.mode === "edit") && <ProjectForm project={drawer.project}/>}
      </Drawer>

      {/* Context menu */}
      {ctx && (
        <ContextMenu x={ctx.x} y={ctx.y} onClose={() => setCtx(null)}
          items={[
            { icon: "external", label: t("act.open"), shortcut: "O", action: () => setDrawer({ mode: "view", project: ctx.project }) },
            { icon: "copy", label: t("act.edit"), shortcut: "E", action: () => setDrawer({ mode: "edit", project: ctx.project }) },
            { icon: "fork", label: t("act.duplicate"), action: () => {
              setProjectsLocal(prev => [{ ...ctx.project, id: "proj_dup_" + Date.now(), name: ctx.project.name + " (copy)", status: "DRAFT", created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, ...prev]);
            }},
            { divider: true },
            { icon: "lock", label: t("act.archive"), action: () => setProjectsLocal(prev => prev.map(p => p.id === ctx.project.id ? { ...p, status: "ARCHIVED", archived_at: new Date().toISOString() } : p)) },
            { icon: "x", label: t("act.delete"), danger: true, action: () => setConfirmDelete(ctx.project) },
          ]}/>
      )}

      {/* Confirm delete modal */}
      <Modal open={!!confirmDelete} onClose={() => setConfirmDelete(null)}
        title={t("proj.deleteConfirm")}
        footer={
          <>
            <button className="btn ghost" onClick={() => setConfirmDelete(null)}>{t("act.cancel")}</button>
            <button className="btn danger" onClick={() => {
              setProjectsLocal(prev => prev.filter(p => p.id !== confirmDelete.id));
              setConfirmDelete(null);
            }}><Icon name="x" size={11}/> {t("act.deletePerm")}</button>
          </>
        }>
        <div style={{ fontSize: 12, color: "var(--fg-muted)", lineHeight: 1.6 }}>
          {t("proj.deleteMsg")} <strong style={{ color: "var(--fg)" }}>{confirmDelete?.name}</strong>. {t("proj.deleteMsg2").replace("{n}", confirmDelete?.runs || 0)}
        </div>
        <div style={{ marginTop: 12, padding: 10, background: "var(--warn-dim)", border: "1px solid var(--warn-line)", borderRadius: 6, fontSize: 11, color: "var(--warn)", display: "flex", gap: 8 }}>
          <Icon name="warn-tri" size={12}/> <div>{t("proj.archiveHint")} <strong>{t("act.archive").toLowerCase()}</strong> {t("proj.archiveHint2")}</div>
        </div>
      </Modal>
    </div>
  );
};

// ─── Views ───────────────────────────────────────────────

const ProjectStatusBadge = ({ status }) => {
  const map = {
    RUNNING:   { tone: "info",    icon: "spin",       label: "RUNNING" },
    PAUSED:    { tone: "warn",    icon: "pause",      label: "PAUSED", filled: true },
    DRAFT:     { tone: "neutral", icon: "circle-o",   label: "DRAFT",  dashed: true },
    SUCCEEDED: { tone: "success", icon: "check",      label: "DONE",   filled: true },
    FAILED:    { tone: "danger",  icon: "x",          label: "FAILED", filled: true },
    ARCHIVED:  { tone: "neutral", icon: "lock",       label: "ARCHIVED" },
  };
  const cfg = map[status] || map.DRAFT;
  if (cfg.tone === "info") return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "1px 7px", height: 18, borderRadius: 4, fontSize: 11, fontFamily: "var(--font-mono)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", border: "1px solid var(--accent-line)", background: "var(--accent-dim)", color: "var(--accent)" }}>
      <Icon name={cfg.icon} size={10}/> {cfg.label}
    </span>
  );
  return <StatusBadge {...cfg}/>;
};

const ProjectsListView = ({ projects, onOpen, onContextMenu }) => { const { t } = useI18n(); return (
  <div className="panel" style={{ overflow: "hidden" }}>
    <div className="row head" style={{ gridTemplateColumns: "24px minmax(220px, 1.8fr) 110px 130px 130px 70px 110px 90px" }}>
      <span></span>
      <span>{t("proj.colProject")}</span>
      <span>{t("lbl.status")}</span>
      <span>{t("proj.colHealth")}</span>
      <span>{t("proj.colBudget")}</span>
      <span>{t("proj.colRuns")}</span>
      <span>{t("lbl.updated")}</span>
      <span>{t("lbl.owner")}</span>
    </div>
    {projects.map(p => (
      <div key={p.id} className="row" onContextMenu={e => onContextMenu(e, p)} onClick={() => onOpen(p)}
        style={{ gridTemplateColumns: "24px minmax(220px, 1.8fr) 110px 130px 130px 70px 110px 90px", cursor: "pointer" }}>
        <span style={{ color: p.favorited ? "var(--warn)" : "var(--fg-faint)" }}>
          <Icon name={p.favorited ? "diamond" : "circle-o"} size={11}/>
        </span>
        <div className="row-cell-wrap" style={{ minWidth: 0, overflow: "hidden" }}>
          <div style={{ fontSize: 13, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginBottom: 2 }}>{p.name}</div>
          <div style={{ display: "flex", gap: 4, alignItems: "center", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", overflow: "hidden", whiteSpace: "nowrap" }}>
            <span style={{ flexShrink: 0 }}>{p.slug}</span>
            {p.tags.slice(0, 2).map(tg => <span key={tg} className="chip" style={{ height: 15, fontSize: 9, flexShrink: 0 }}>{tg}</span>)}
            {p.tags.length > 2 && <span style={{ fontSize: 10, flexShrink: 0 }}>+{p.tags.length - 2}</span>}
          </div>
        </div>
        <span><ProjectStatusBadge status={p.status}/></span>
        <span>
          {p.health == null ? <span className="empty-mark">—</span> :
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ flex: 1, height: 3, background: "var(--bg-sunken)", borderRadius: 2, minWidth: 40 }}>
                <div style={{ width: `${p.health}%`, height: "100%", background: p.health >= 80 ? "var(--success)" : p.health >= 50 ? "var(--warn)" : "var(--danger)", borderRadius: 2 }}/>
              </div>
              <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: p.health >= 80 ? "var(--success)" : p.health >= 50 ? "var(--warn)" : "var(--danger)" }}>{p.health}</span>
            </div>
          }
        </span>
        <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
          ${(p.spent_minor/100000).toFixed(0)} / ${(p.budget_minor/100000).toFixed(0)}
        </span>
        <span style={{ fontSize: 12, fontFamily: "var(--font-mono)" }}>{p.runs}</span>
        <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
          {new Date(p.updated_at).toLocaleDateString("en-CA")}
        </span>
        <span style={{ fontSize: 11, color: "var(--fg-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {p.owner.split("@")[0]}
        </span>
      </div>
    ))}
  </div>
)};

const ProjectsBoardView = ({ projects, onOpen, onContextMenu }) => {
  const cols = ["DRAFT", "RUNNING", "PAUSED", "SUCCEEDED", "FAILED", "ARCHIVED"];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 10, minWidth: 1200 }}>
      {cols.map(col => {
        const items = projects.filter(p => p.status === col);
        return (
          <div key={col} className="panel" style={{ padding: 8, display: "flex", flexDirection: "column", gap: 6, minHeight: 400 }}>
            <div style={{ padding: "4px 8px", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", letterSpacing: "0.06em", textTransform: "uppercase", display: "flex", alignItems: "center" }}>
              {col.toLowerCase()} <span style={{ marginLeft: "auto", color: "var(--fg-faint)" }}>{items.length}</span>
            </div>
            {items.map(p => (
              <div key={p.id} onClick={() => onOpen(p)} onContextMenu={e => onContextMenu(e, p)}
                style={{ padding: 10, background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 6, cursor: "pointer" }}>
                <div style={{ fontSize: 11, fontWeight: 500, marginBottom: 4, lineHeight: 1.4 }}>{p.name}</div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                  <span>{p.runs} runs</span>
                  <span style={{ color: p.health >= 80 ? "var(--success)" : p.health >= 50 ? "var(--warn)" : p.health != null ? "var(--danger)" : "var(--fg-faint)" }}>
                    {p.health != null ? `${p.health}` : "—"}
                  </span>
                </div>
              </div>
            ))}
            {items.length === 0 && <div style={{ fontSize: 10, color: "var(--fg-faint)", textAlign: "center", padding: 20, fontStyle: "italic" }}>{typeof useI18n === "function" ? useI18n().t("proj.boardEmpty") : "empty"}</div>}
          </div>
        );
      })}
    </div>
  );
};

const ProjectsGridView = ({ projects, onOpen, onContextMenu }) => { const { t } = useI18n(); return (
  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
    {projects.map(p => (
      <div key={p.id} onClick={() => onOpen(p)} onContextMenu={e => onContextMenu(e, p)}
        className="panel" style={{ padding: 14, cursor: "pointer", display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 4 }}>{p.name}</div>
            <div className="mono" style={{ fontSize: 10, color: "var(--fg-faint)" }}>{p.slug}</div>
          </div>
          <ProjectStatusBadge status={p.status}/>
        </div>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {p.tags.slice(0, 4).map(t => <span key={t} className="chip" style={{ height: 16, fontSize: 9 }}>{t}</span>)}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginTop: 4, paddingTop: 10, borderTop: "1px solid var(--border-subtle)" }}>
          <div>
            <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{t("proj.card.runs")}</div>
            <div style={{ fontSize: 14, fontFamily: "var(--font-mono)", fontWeight: 500 }}>{p.runs}</div>
          </div>
          <div>
            <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{t("proj.card.health")}</div>
            <div style={{ fontSize: 14, fontFamily: "var(--font-mono)", fontWeight: 500, color: p.health == null ? "var(--fg-faint)" : p.health >= 80 ? "var(--success)" : p.health >= 50 ? "var(--warn)" : "var(--danger)" }}>{p.health ?? "—"}</div>
          </div>
          <div>
            <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{t("proj.card.burn")}</div>
            <div style={{ fontSize: 14, fontFamily: "var(--font-mono)", fontWeight: 500 }}>{Math.round(p.spent_minor/p.budget_minor*100)}%</div>
          </div>
        </div>
      </div>
    ))}
  </div>
)};

// ─── Detail + Form ───────────────────────────────────────

const ProjectDetail = ({ project }) => { const { t } = useI18n(); return (
  <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
      <ProjectStatusBadge status={project.status}/>
      <DigestText value={project.id} length={16} prefix={false}/>
      <span className="chip">{project.team_template}</span>
      {project.favorited && <span className="chip" style={{ color: "var(--warn)", borderColor: "var(--warn-line)" }}><Icon name="diamond" size={9}/> {t("proj.card.pinned")}</span>}
    </div>

    <div>
      <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>{t("proj.overview").toUpperCase()}</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        <MetricCard label={t("proj.card.runs")} value={project.runs} sub={<span>{project.active_agents} {t("proj.card.activeAgents")}</span>}/>
        <MetricCard label={t("proj.card.health")} value={project.health ?? "—"}
          sub={<span>{t("proj.card.score")}</span>}
          bar={project.health != null ? project.health / 100 : 0}
          barColor={project.health == null ? "var(--fg-faint)" : project.health >= 80 ? "var(--success)" : project.health >= 50 ? "var(--warn)" : "var(--danger)"}/>
        <MetricCard label={t("bg.totalSpent")} value={`$${(project.spent_minor/100000).toFixed(2)}`}
          sub={<span>{t("proj.card.spentOf")} <span className="mono">${(project.budget_minor/100000).toFixed(2)}</span> · {Math.round(project.spent_minor/project.budget_minor*100)}%</span>}
          bar={project.spent_minor/project.budget_minor} barColor="var(--accent)"/>
        <MetricCard label={t("gv.claims").toUpperCase()} value={project.claims.verified + project.claims.disputed + project.claims.proposed + project.claims.refuted}
          sub={<span>
            <span style={{ color: "var(--success)" }}>{project.claims.verified} {t("proj.status.verified")}</span> · <span style={{ color: "var(--warn)" }}>{project.claims.disputed} {t("proj.status.disputed")}</span> · <span style={{ color: "var(--danger)" }}>{project.claims.refuted} {t("proj.status.refuted")}</span>
          </span>}/>
      </div>
    </div>

    <div>
      <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>{t("lbl.tags")}</div>
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
        {project.tags.map(t => <span key={t} className="chip" style={{ background: "var(--accent-dim)", color: "var(--accent)", borderColor: "var(--accent-line)" }}>{t}</span>)}
      </div>
    </div>

    {(project.paused_reason || project.failure_reason) && (
      <div style={{ padding: 10, background: "var(--warn-dim)", border: "1px solid var(--warn-line)", borderRadius: 6, fontSize: 11, color: "var(--warn)", display: "flex", gap: 8 }}>
        <Icon name="warn-tri" size={12}/> <div>{project.paused_reason || project.failure_reason}</div>
      </div>
    )}

    <div>
      <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>{t("exp.meta").toUpperCase()}</div>
      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 12px", fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
        <span style={{ color: "var(--fg-faint)" }}>owner</span><span>{project.owner}</span>
        <span style={{ color: "var(--fg-faint)" }}>{t("lbl.created")}</span><span>{new Date(project.created_at).toISOString().replace("T"," ").slice(0,16)}</span>
        <span style={{ color: "var(--fg-faint)" }}>{t("lbl.updated").toLowerCase()}</span><span>{new Date(project.updated_at).toISOString().replace("T"," ").slice(0,16)}</span>
        <span style={{ color: "var(--fg-faint)" }}>{t("lbl.template")}</span><span>{project.team_template}</span>
      </div>
    </div>
  </div>
)};

const ProjectForm = ({ project }) => { const { t } = useI18n();
  const [name, setName] = useState(project?.name || "");
  const [slug, setSlug] = useState(project?.slug || "");
  const [tmpl, setTmpl] = useState(project?.team_template || "STANDARD");
  const [tags, setTags] = useState(project?.tags || []);
  const [budget, setBudget] = useState(project?.budget_minor ? project.budget_minor/100000 : 5);
  const [autonomy, setAutonomy] = useState("GUARDED_AUTONOMOUS");
  const [notes, setNotes] = useState("");

  return (
    <div>
      <FormRow label={t("lbl.name")} required hint={t("proj.form.nameHint")}>
        <TextInput value={name} onChange={setName} placeholder={t("proj.form.namePh")}/>
      </FormRow>
      <FormRow label={t("proj.form.slug")} hint={t("proj.form.slugHint")} required>
        <TextInput value={slug} onChange={setSlug} placeholder="med-qa-hallucination" mono/>
      </FormRow>
      <FormRow label={t("proj.form.teamTmpl")} hint={t("proj.form.teamTmplHint")}>
        <Select value={tmpl} onChange={setTmpl} options={[
          { value: "LEAN", label: "LEAN · 5-7 agents · fast iteration" },
          { value: "STANDARD", label: "STANDARD · 10-14 agents · heterogeneous review" },
          { value: "RIGOROUS", label: "RIGOROUS · 16-24 agents · adversarial + ethics" },
        ]}/>
      </FormRow>
      <FormRow label={t("lbl.autonomy")} hint={t("proj.form.autonomyHint")}>
        <Select value={autonomy} onChange={setAutonomy} options={[
          { value: "SUPERVISED", label: "SUPERVISED · every action requires human confirm" },
          { value: "GUARDED_AUTONOMOUS", label: "GUARDED_AUTONOMOUS · pause on gates" },
          { value: "AUTONOMOUS", label: "AUTONOMOUS · pause only on hard failures" },
        ]}/>
      </FormRow>
      <FormRow label={t("proj.form.budget")} hint={t("proj.form.budgetHint")}>
        <TextInput value={budget} onChange={v => setBudget(parseFloat(v) || 0)} mono/>
      </FormRow>
      <FormRow label={t("lbl.tags")}>
        <TagInput tags={tags} onChange={setTags}/>
      </FormRow>
      <FormRow label={t("lbl.notes")} hint={t("proj.form.notesHint")}>
        <TextArea value={notes} onChange={setNotes} rows={4} placeholder={t("proj.form.notesPh")}/>
      </FormRow>
      <div style={{ padding: 10, background: "var(--bg-raised)", border: "1px dashed var(--border)", borderRadius: 6, fontSize: 10, color: "var(--fg-muted)", display: "flex", gap: 8 }}>
        <Icon name="q" size={11} style={{ color: "var(--fg-faint)", marginTop: 2 }}/>
        <div style={{ lineHeight: 1.5 }}>
          {t("proj.form.starts")} <span className="mono">DRAFT</span>{t("proj.form.starts2")}
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { ProjectsScreen });
