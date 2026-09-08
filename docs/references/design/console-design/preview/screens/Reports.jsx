/* Reports — research report authoring & publishing.
   List left · authored preview right (with cited claims). */

const ReportsScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState(FIX_REPORTS[0].id);
  const [drawer, setDrawer] = useState(null);
  const selected = FIX_REPORTS.find(r => r.id === selectedId);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("rp.title")} subtitle={t("rp.subtitle")}>
        <ViewSwitcher value="list" onChange={() => {}} views={[
          { value: "list", label: t("rp.viewList"), icon: "menu" },
          { value: "shelf", label: t("rp.viewShelf"), icon: "book" },
        ]}/>
        <button className="btn primary sm" onClick={() => setDrawer({ mode: "create" })}>
          <Icon name="plus" size={11}/> {t("rp.new")}
        </button>
      </PageToolbar>

      <div style={{ display: "grid", gridTemplateColumns: "380px 1fr", gap: 12, flex: 1, minHeight: 0 }}>
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="book" size={12} style={{ color: "var(--fg-muted)" }}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("rp.title")}</span>
            <span className="chip">{FIX_REPORTS.length}</span>
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {FIX_REPORTS.map(r => {
              const active = r.id === selectedId;
              return (
                <div key={r.id} onClick={() => setSelectedId(r.id)} style={{
                  padding: "12px 14px", cursor: "pointer",
                  background: active ? "var(--bg-hover)" : "transparent",
                  borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
                  borderBottom: "1px solid var(--border-subtle)",
                }}>
                  <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 4 }}>
                    <ReportStatusBadge status={r.status}/>
                    <span className="chip" style={{ fontSize: 9 }}>{r.format}</span>
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 500, lineHeight: 1.4, marginBottom: 4 }}>{r.title}</div>
                  <div style={{ display: "flex", gap: 10, fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
                    <span>{r.sections} sect</span>
                    <span>{r.cited_claims} claims</span>
                    <span>{r.figures} figs</span>
                    <span>{r.pdf_pages}pp</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {selected && <ReportPreview report={selected} onEdit={() => setDrawer({ mode: "edit", report: selected })}/>}
      </div>

      <Drawer open={!!drawer} onClose={() => setDrawer(null)}
        title={drawer?.mode === "create" ? t("rp.new") : t("rp.edit")}
        subtitle={drawer?.mode === "create" ? t("rp.newSub") : t("rp.editSub")}
        width={520}
        footer={
          <>
            <button className="btn ghost" onClick={() => setDrawer(null)}>{t("act.cancel")}</button>
            <button className="btn primary" style={{ marginLeft: "auto" }} onClick={() => setDrawer(null)}>
              <Icon name="check" size={11}/> {drawer?.mode === "create" ? t("rp.createDraft") : t("act.save")}
            </button>
          </>
        }>
        <ReportForm report={drawer?.report}/>
      </Drawer>
    </div>
  );
};

const ReportStatusBadge = ({ status }) => {
  const map = {
    DRAFT:     { tone: "neutral", icon: "circle-o", label: "DRAFT",     dashed: true },
    IN_REVIEW: { tone: "warn",    icon: "eye-off",  label: "IN REVIEW", filled: true },
    PUBLISHED: { tone: "success", icon: "check",    label: "PUBLISHED", filled: true },
  };
  return <StatusBadge {...(map[status] || map.DRAFT)}/>;
};

const ReportPreview = ({ report, onEdit }) => { const { t } = useI18n();
  const draft = FIX_REPORT_DRAFT;
  const showDraft = report.id === draft.id;

  return (
    <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "flex-start", gap: 12 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 4 }}>
            {report.format} · {report.pdf_pages}{t("rp.pages")} · {report.word_count.toLocaleString()} {t("rp.words")}
          </div>
          <div style={{ fontSize: 17, fontWeight: 500, letterSpacing: "-0.005em", marginBottom: 6 }}>{report.title}</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", fontSize: 11, color: "var(--fg-muted)" }}>
            <ReportStatusBadge status={report.status}/>
            <DigestText value={report.digest} label="digest:" length={10}/>
            {report.doi && <span className="mono">DOI: {report.doi}</span>}
            {report.venue && <span className="chip">{report.venue}</span>}
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button className="btn sm" onClick={onEdit}><Icon name="copy" size={10}/> {t("act.edit")}</button>
          <button className="btn sm"><Icon name="external" size={10}/> {t("act.preview")}</button>
          <button className="btn primary sm"><Icon name="external" size={10}/> {t("act.export")}</button>
        </div>
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: 24, background: "var(--bg-sunken)" }}>
        {/* Paper-styled document */}
        <div style={{
          maxWidth: 760, margin: "0 auto",
          background: "var(--bg-panel)",
          border: "1px solid var(--border)",
          borderRadius: 4, padding: "36px 48px",
          boxShadow: "var(--shadow-2)",
          minHeight: 600,
        }}>
          <div style={{ textAlign: "center", marginBottom: 32 }}>
            <div style={{ fontSize: 20, fontWeight: 500, letterSpacing: "-0.005em", lineHeight: 1.3, marginBottom: 14, color: "var(--fg)" }}>
              {report.title}
            </div>
            <div style={{ fontSize: 11, color: "var(--fg-muted)", fontFamily: "var(--font-mono)" }}>
              {report.authors.join(" · ")}
            </div>
            <div style={{ fontSize: 10, color: "var(--fg-faint)", fontFamily: "var(--font-mono)", marginTop: 4 }}>
              {report.published_at ? `${t("rp.published")} ${new Date(report.published_at).toISOString().slice(0,10)}` : `${t("rp.draft")} ${new Date(report.updated_at).toISOString().slice(0,10)}`}
            </div>
          </div>

          {showDraft ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
              {draft.sections.map(s => (
                <div key={s.id}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                    <span style={{ fontSize: 14, fontWeight: 500 }}>{s.title}</span>
                    <SectionStatusChip status={s.status}/>
                    {s.claims.length > 0 && <span className="chip" style={{ fontSize: 9 }}>{t("rp.cites")} {s.claims.length}</span>}
                  </div>
                  {s.status === "todo" ? (
                    <div style={{ padding: 14, border: "1px dashed var(--border-strong)", borderRadius: 6, fontSize: 11, color: "var(--fg-faint)", fontStyle: "italic" }}>
                      {t("rp.sectTodo")}
                    </div>
                  ) : (
                    <>
                      <p style={{ fontSize: 12, lineHeight: 1.7, color: "var(--fg-muted)", margin: "0 0 8px" }}>
                        {sectionText(s.id)}
                      </p>
                      {s.claims.length > 0 && (
                        <div style={{ marginTop: 8, padding: 10, background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 4 }}>
                          <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6 }}>{t("rp.cited")}</div>
                          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                            {s.claims.map(cid => {
                              const c = FIX_CLAIMS.find(x => x.id === cid);
                              if (!c) return null;
                              return (
                                <div key={cid} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                                  <ClaimStatusBadge status={c.status}/>
                                  <div style={{ flex: 1, fontSize: 11, color: "var(--fg)", lineHeight: 1.5 }}>
                                    <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg-faint)", fontSize: 10 }}>[{cid.slice(4, 14)}]</span> {c.statement}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <p style={{ fontSize: 12, lineHeight: 1.75, color: "var(--fg-muted)" }}>
                <strong style={{ color: "var(--fg)" }}>{t("rp.abstract")}</strong> {sectionText("abstract")}
              </p>
              <p style={{ fontSize: 12, lineHeight: 1.75, color: "var(--fg-muted)" }}>{sectionText("intro")}</p>
              <p style={{ fontSize: 12, lineHeight: 1.75, color: "var(--fg-muted)" }}>{sectionText("methods")}</p>
              <p style={{ fontSize: 12, lineHeight: 1.75, color: "var(--fg-muted)" }}>{sectionText("results")}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const SectionStatusChip = ({ status }) => {
  const map = {
    complete:      { color: "var(--success)", label: "complete" },
    "in-progress": { color: "var(--accent)",  label: "in-progress" },
    draft:         { color: "var(--warn)",    label: "draft" },
    todo:          { color: "var(--fg-faint)", label: "todo" },
  };
  const c = map[status] || map.todo;
  return <span className="chip" style={{ color: c.color, borderColor: `${c.color}44`, fontSize: 9, height: 15 }}>{c.label}</span>;
};

const sectionText = (id) => {
  const T = {
    abstract: "We evaluated hallucination rates of five frontier LLMs on multilingual medical dosage question-answering across seven languages (n=8,400). Across our benchmark, Spanish and Chinese elicited substantially higher hallucination rates than English (12.3% and 8.7% vs 4.1% respectively, χ²=27.4, p<0.001). Claude Opus 4.1 showed the lowest cross-lingual variance (σ=0.031); however, the Arabic subset (n=48) is underpowered and this finding is currently disputed. Chain-of-thought prompting, contrary to expectations, did not reduce hallucination — instead it inflated model confidence without accuracy gains.",
    intro: "1. Introduction. Large language models are increasingly deployed as clinical decision support, yet their reliability under multilingual medical queries remains poorly characterized. Prior work has focused predominantly on English benchmarks (MedQA, MedMCQA). We ask whether the frontier hallucination behavior observed on English generalizes across the seven WHO-priority languages …",
    methods: "2. Methods. We assembled a corpus of 8,420 dosage-QA pairs from the WHO Dosage Guidelines (2024) and PubMed abstracts (2023). Each query was translated by native-speaker clinicians and cross-verified. Five models (GPT-4o, Claude Sonnet 4, Claude Opus 4.1, Gemini 2.5 Pro, Qwen3-235B) were queried under a fixed protocol …",
    results: "3. Results. Table 1 reports hallucination rates by (model × language). Across the pooled sample (n=8,400), Spanish showed the highest hallucination rate (12.3%, 95% CI [11.1, 13.6]). Chinese generic-name substitution errors occurred at 2.8× the English baseline. Model-wise, Claude Opus 4.1 was most stable across languages (σ=0.031) but the Arabic subset was too small (n=48) for statistical conclusions and this claim is currently under review …",
  };
  return T[id] || "";
};

const ReportForm = ({ report }) => { const { t } = useI18n();
  const [title, setTitle] = useState(report?.title || "");
  const [format, setFormat] = useState(report?.format || "preprint");
  const [project, setProject] = useState(report?.project_id || "proj_01K5FZ8G3X2QN4M");
  const [claims, setClaims] = useState(report ? FIX_CLAIMS.filter(c => c.status === "VERIFIED").slice(0, 3).map(c => c.id) : []);

  return (
    <div>
      <FormRow label={t("lbl.title")} required>
        <TextInput value={title} onChange={setTitle} placeholder={t("rp.form.titlePh")}/>
      </FormRow>
      <FormRow label={t("lbl.project")}>
        <Select value={project} onChange={setProject} options={FIX_PROJECTS.map(p => ({ value: p.id, label: p.name }))}/>
      </FormRow>
      <FormRow label={t("rp.form.fmt")}>
        <Select value={format} onChange={setFormat} options={[
          { value: "abstract", label: t("rp.form.fmtAbstract") },
          { value: "preprint", label: t("rp.form.fmtPreprint") },
          { value: "workshop", label: t("rp.form.fmtWorkshop") },
          { value: "internal", label: t("rp.form.fmtInternal") },
        ]}/>
      </FormRow>
      <FormRow label={t("rp.form.citeClaims")} hint={`${claims.length} ${t("rp.form.citeHint")}`}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 220, overflow: "auto", padding: 4, background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 6 }}>
          {FIX_CLAIMS.map(c => {
            const on = claims.includes(c.id);
            return (
              <label key={c.id} style={{ display: "flex", gap: 8, padding: "6px 8px", cursor: "pointer", borderRadius: 4, background: on ? "var(--accent-dim)" : "transparent" }}>
                <input type="checkbox" checked={on} onChange={() => setClaims(on ? claims.filter(id => id !== c.id) : [...claims, c.id])} style={{ accentColor: "var(--accent)" }}/>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 2 }}>
                    <ClaimStatusBadge status={c.status}/>
                    <span className="mono" style={{ fontSize: 9, color: "var(--fg-faint)" }}>{c.id.slice(4, 14)}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.4 }}>{c.statement.slice(0, 100)}…</div>
                </div>
              </label>
            );
          })}
        </div>
      </FormRow>
      <FormRow label={t("rp.form.compile")}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12 }}>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" defaultChecked style={{ accentColor: "var(--accent)" }}/> {t("rp.form.optFigures")}</label>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" defaultChecked style={{ accentColor: "var(--accent)" }}/> {t("rp.form.optManifest")}</label>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" style={{ accentColor: "var(--accent)" }}/> {t("rp.form.optFlag")}</label>
        </div>
      </FormRow>
    </div>
  );
};

Object.assign(window, { ReportsScreen });
