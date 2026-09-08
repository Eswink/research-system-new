/* Datasets — table + lineage graph (parent-child) + schema panel. */

const DatasetsScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState("ds_medqa_multi_v3");
  const [tab, setTab] = useState("preview");
  const [drawer, setDrawer] = useState(null);
  const [q, setQ] = useState("");
  const selected = FIX_DATASETS.find(d => d.id === selectedId);
  const filtered = q ? FIX_DATASETS.filter(d => d.name.toLowerCase().includes(q.toLowerCase())) : FIX_DATASETS;

  // Build lineage graph nodes + edges
  const { nodes, edges } = useMemo(() => {
    const ns = FIX_DATASETS.map(d => ({ id: d.id, label: d.name.split(" ")[0], group: d.lineage.parents.length === 0 ? "root" : d.lineage.children.length === 0 ? "leaf" : "mid" }));
    const es = [];
    FIX_DATASETS.forEach(d => d.lineage.children.forEach(c => es.push({ from: d.id, to: c })));
    return { nodes: ns, edges: es };
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("ds.title")} subtitle={t("ds.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("ds.search")} width={220}/>
        <button className="btn sm"><Icon name="external" size={11}/> {t("ds.upload")}</button>
        <button className="btn primary sm" onClick={() => setDrawer({ mode: "create" })}>
          <Icon name="plus" size={11}/> {t("ds.new")}
        </button>
      </PageToolbar>

      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 12, flex: 1, minHeight: 0 }}>
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div className="row head" style={{ gridTemplateColumns: "minmax(200px, 1.8fr) 90px 70px 70px 70px 90px" }}>
            <span>{t("ds.colDataset")}</span>
            <span>{t("lbl.version")}</span>
            <span>{t("lbl.rows")}</span>
            <span>{t("lbl.size")}</span>
            <span>{t("lbl.format")}</span>
            <span>{t("lbl.schema")}</span>
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {filtered.map(d => {
              const active = d.id === selectedId;
              return (
                <div key={d.id} className="row" onClick={() => setSelectedId(d.id)} style={{
                  gridTemplateColumns: "minmax(200px, 1.8fr) 90px 70px 70px 70px 90px",
                  cursor: "pointer",
                  background: active ? "var(--bg-hover)" : undefined,
                  borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
                }}>
                  <div className="row-cell-wrap" style={{ minWidth: 0, overflow: "hidden" }}>
                    <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{d.name}</div>
                    <div style={{ display: "flex", gap: 4, alignItems: "center", overflow: "hidden", whiteSpace: "nowrap" }}>
                      {d.tags.slice(0, 2).map(tg => <span key={tg} className="chip" style={{ fontSize: 9, height: 15, flexShrink: 0 }}>{tg}</span>)}
                      {d.tags.length > 2 && <span style={{ fontSize: 9, color: "var(--fg-faint)", flexShrink: 0 }}>+{d.tags.length - 2}</span>}
                    </div>
                  </div>
                  <span className="mono" style={{ fontSize: 11 }}>{d.version}</span>
                  <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
                    {d.rows == null ? <span className="empty-mark">—</span> : d.rows.toLocaleString()}
                  </span>
                  <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
                    {d.size_mb < 1000 ? `${d.size_mb} MB` : `${(d.size_mb/1024).toFixed(1)} GB`}
                  </span>
                  <span className="chip" style={{ fontSize: 9 }}>{d.format}</span>
                  <span>
                    {d.schema_valid === true && <StatusBadge tone="success" icon="check" label="OK" size="sm"/>}
                    {d.schema_valid === false && <StatusBadge tone="danger" icon="x" label={`${d.schema_errors?.length || 0} ${t("ds.err")}`} size="sm" filled/>}
                    {d.schema_valid == null && <span className="empty-mark">{t("ds.unvalidated")}</span>}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {selected && (
          <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 3 }}>
                    {t("lbl.dataset")} · {selected.version}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 500, fontFamily: "var(--font-mono)" }}>{selected.name}</div>
                </div>
                {selected.checksum && <DigestText value={selected.checksum} length={10} label="sha:"/>}
              </div>
              <div style={{ display: "flex", gap: 4, marginTop: 8 }}>
                {[["preview",t("ds.tabPreview")],["schema",t("ds.tabSchema")],["lineage",t("ds.tabLineage")]].map(([v,l]) => (
                  <button key={v} onClick={() => setTab(v)} className="btn sm ghost" style={{
                    background: tab === v ? "var(--bg-hover)" : "transparent",
                    color: tab === v ? "var(--fg)" : "var(--fg-muted)",
                    fontWeight: tab === v ? 500 : 400,
                    borderColor: tab === v ? "var(--border-strong)" : "transparent",
                  }}>{l}</button>
                ))}
              </div>
            </div>

            <div style={{ flex: 1, overflow: "auto", padding: 14 }}>
              {tab === "preview" && (
                <div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12 }}>
                    <MetricCard label={t("ds.rowsCol")} value={selected.rows?.toLocaleString() || "—"}/>
                    <MetricCard label={t("ds.columnsCol")} value={selected.columns || "—"}/>
                  </div>
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 6 }}>{t("ds.sampleRows")}</div>
                  <div style={{ overflow: "auto", background: "var(--bg-sunken)", borderRadius: 6, border: "1px solid var(--border)" }}>
                    <table style={{ borderCollapse: "collapse", fontSize: 10, fontFamily: "var(--font-mono)", minWidth: "100%" }}>
                      <thead>
                        <tr style={{ background: "var(--bg-raised)" }}>
                          {["id", "language", "question", "gold_answer", "model_output"].map(c => (
                            <th key={c} style={{ padding: "6px 10px", textAlign: "left", color: "var(--fg-faint)", letterSpacing: "0.06em", borderBottom: "1px solid var(--border)" }}>{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          ["mqa_001", "es", "¿Cuál es la dosis de amoxicilina…", "500mg tid×7d", "500 mg cada 8h"],
                          ["mqa_002", "zh", "阿莫西林的成人剂量是…", "500mg tid×7d", "0.5g q8h"],
                          ["mqa_003", "en", "Adult dose of amoxicillin…", "500mg tid×7d", "500mg q8h"],
                          ["mqa_004", "ar", "ما هي جرعة الأموكسيسيلين…", "500mg tid×7d", "500 mg every 8 hours"],
                        ].map((row, i) => (
                          <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                            {row.map((c, j) => (
                              <td key={j} style={{ padding: "6px 10px", color: j === 0 ? "var(--accent)" : "var(--fg-muted)", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div style={{ marginTop: 8, fontSize: 10, color: "var(--fg-faint)", fontFamily: "var(--font-mono)" }}>{t("ds.showingRows").replace("{n}", selected.rows?.toLocaleString() || "?")}</div>
                </div>
              )}
              {tab === "schema" && (
                <div>
                  {selected.schema_valid === false && selected.schema_errors && (
                    <div style={{ padding: 10, background: "var(--danger-dim)", border: "1px solid var(--danger-line)", borderRadius: 6, marginBottom: 12 }}>
                      <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 6 }}>
                        <Icon name="x" size={11} style={{ color: "var(--danger)" }}/>
                        <span style={{ fontSize: 11, fontWeight: 500, color: "var(--danger)" }}>{selected.schema_errors.length} {t("ds.schemaErrors")}</span>
                      </div>
                      {selected.schema_errors.map((e, i) => (
                        <div key={i} style={{ fontSize: 11, color: "var(--fg-muted)", marginTop: 4 }}>
                          <span className="mono" style={{ color: "var(--danger)" }}>{e.column}</span>: {e.issue}
                        </div>
                      ))}
                    </div>
                  )}
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 8 }}>{t("ds.columnSchema")}</div>
                  {[
                    ["id", "string", "unique row id"],
                    ["language", "enum[en,es,zh,ar,pt,fr,de]", "target language"],
                    ["question", "string", "clinical query"],
                    ["gold_answer", "string", "clinician-verified answer"],
                    ["model_output", "string", "model response"],
                    ["dose_mg", "float?", "extracted dose in mg (nullable)"],
                    ["source_doi", "string", "PubMed / WHO reference"],
                  ].map(([col, type, desc]) => (
                    <div key={col} style={{ display: "grid", gridTemplateColumns: "140px 200px 1fr", gap: 8, padding: "6px 10px", borderBottom: "1px solid var(--border-subtle)", fontSize: 11 }}>
                      <span className="mono" style={{ color: "var(--fg)" }}>{col}</span>
                      <span className="mono" style={{ color: "var(--accent)" }}>{type}</span>
                      <span style={{ color: "var(--fg-muted)" }}>{desc}</span>
                    </div>
                  ))}
                </div>
              )}
              {tab === "lineage" && (
                <div>
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", marginBottom: 8 }}>{t("ds.dataLineage")} · {selected.name}</div>
                  <div style={{ background: "var(--bg-sunken)", border: "1px solid var(--border)", borderRadius: 6, padding: 8 }}>
                    <ForceGraph nodes={nodes} edges={edges} width={440} height={300} groupColors={{
                      root: "var(--fg-muted)", mid: "var(--accent)", leaf: "var(--success)"
                    }}/>
                  </div>
                  <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                    <div>
                      <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", marginBottom: 4 }}>{t("ds.parents")} ({selected.lineage.parents.length})</div>
                      {selected.lineage.parents.length === 0 ? (
                        <span className="empty-mark">{t("ds.noParents")}</span>
                      ) : selected.lineage.parents.map(p => {
                        const parent = FIX_DATASETS.find(d => d.id === p);
                        return parent ? (
                          <div key={p} style={{ fontSize: 11, marginBottom: 3, cursor: "pointer" }} onClick={() => setSelectedId(p)}>
                            <Icon name="chevron-r" size={8} style={{ color: "var(--fg-faint)" }}/> <span className="mono" style={{ color: "var(--accent)" }}>{parent.name}</span>
                          </div>
                        ) : null;
                      })}
                    </div>
                    <div>
                      <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", marginBottom: 4 }}>{t("ds.children")} ({selected.lineage.children.length})</div>
                      {selected.lineage.children.length === 0 ? (
                        <span className="empty-mark">{t("ds.noChildren")}</span>
                      ) : selected.lineage.children.map(p => {
                        const child = FIX_DATASETS.find(d => d.id === p);
                        return child ? (
                          <div key={p} style={{ fontSize: 11, marginBottom: 3, cursor: "pointer" }} onClick={() => setSelectedId(p)}>
                            <Icon name="chevron-r" size={8} style={{ color: "var(--fg-faint)" }}/> <span className="mono" style={{ color: "var(--accent)" }}>{child.name}</span>
                          </div>
                        ) : null;
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <Drawer open={!!drawer} onClose={() => setDrawer(null)} title={t("ds.new")} subtitle={t("ds.newSub")} width={480}
        footer={<>
          <button className="btn ghost" onClick={() => setDrawer(null)}>{t("act.cancel")}</button>
          <button className="btn primary" style={{ marginLeft: "auto" }} onClick={() => setDrawer(null)}><Icon name="check" size={11}/> {t("act.register")}</button>
        </>}>
        <FormRow label={t("lbl.name")} required><TextInput placeholder="my-dataset-name" mono/></FormRow>
        <FormRow label={t("lbl.version")} required><TextInput placeholder="v1.0.0" mono/></FormRow>
        <FormRow label={t("ds.form.source")} required>
          <Select value="upload" onChange={() => {}} options={[
            { value: "upload", label: t("ds.form.srcUpload") },
            { value: "s3", label: t("ds.form.srcS3") },
            { value: "derive", label: t("ds.form.srcDerive") },
          ]}/>
        </FormRow>
        <FormRow label={t("ds.form.upload")}>
          <div style={{ padding: "20px 16px", border: "1px dashed var(--border-strong)", borderRadius: 6, textAlign: "center", background: "var(--bg-raised)" }}>
            <Icon name="external" size={20} style={{ color: "var(--fg-faint)" }}/>
            <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 6 }}>{t("ds.form.dropHint")}</div>
            <div style={{ fontSize: 10, color: "var(--fg-faint)", marginTop: 2, fontFamily: "var(--font-mono)" }}>{t("ds.form.dropSpec")}</div>
          </div>
        </FormRow>
        <FormRow label={t("lbl.tags")}><TagInput tags={["draft"]} onChange={() => {}}/></FormRow>
      </Drawer>
    </div>
  );
};

Object.assign(window, { DatasetsScreen });
