/* Screen 8: Workspace & Experiments */

const WorkspaceScreen = () => {
  const { t } = useI18n();
  const [selectedExp, setSelectedExp] = useState(FIX_EXPERIMENTS[3].experiment_run_id); // the "not reproducible" one
  const [selectedFile, setSelectedFile] = useState("analysis/es_dose_chi2.csv");

  const workspace = [
    { path: "data/", type: "dir", children: [
      { path: "medhalt_v2/", type: "dir", children: [
        { path: "medhalt_v2/en_1200.jsonl", type: "file", size: "4.2 MB", modified: "14:04" },
        { path: "medhalt_v2/es_1200.jsonl", type: "file", size: "4.6 MB", modified: "14:08" },
        { path: "medhalt_v2/zh_1200.jsonl", type: "file", size: "5.1 MB", modified: "14:12" },
        { path: "medhalt_v2/ar_1200.jsonl", type: "file", size: "6.3 MB", modified: "14:18" },
      ]},
      { path: "internal_dosage.v3.jsonl", type: "file", size: "2.4 MB", modified: "14:03" },
    ]},
    { path: "analysis/", type: "dir", children: [
      { path: "analysis/es_dose_chi2.csv", type: "file", size: "18 KB", modified: "14:30", highlight: true },
      { path: "analysis/cross_lingual_variance.csv", type: "file", size: "22 KB", modified: "14:33" },
      { path: "analysis/cot_baseline_delta.csv", type: "file", size: "9 KB", modified: "14:36" },
    ]},
    { path: "prompts/", type: "dir", children: [
      { path: "prompts/dosage_probe.tmpl", type: "file", size: "3.1 KB", modified: "14:02" },
      { path: "prompts/generic_name_probe.tmpl", type: "file", size: "2.8 KB", modified: "14:02" },
    ]},
    { path: "artifacts/", type: "dir", children: [
      { path: "artifacts/lit_es_47.parquet", type: "file", size: "1.2 MB", modified: "14:05" },
      { path: "artifacts/lit_zh_63.parquet", type: "file", size: "1.6 MB", modified: "14:09" },
    ]},
  ];

  const exp = FIX_EXPERIMENTS.find(e => e.experiment_run_id === selectedExp);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 12, flex: 1, minHeight: 0 }}>
      {/* Left: workspace tree */}
      <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
          <Icon name="hex" size={12} style={{ color: "var(--fg-muted)" }}/>
          <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ws.snapshot")}</span>
          <span className="chip" style={{ marginLeft: "auto", color: "var(--warn)", borderColor: "var(--warn-line)" }}>
            <Icon name="lock" size={9}/> {t("ws.readOnly")}
          </span>
        </div>
        <div style={{ padding: "6px 12px", background: "var(--bg-sunken)", borderBottom: "1px solid var(--border)", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
          {t("ws.snapshotId")} ws_snap_01K5FZ8H_r24 · {t("ws.at")} 14:36:12Z
        </div>
        <div style={{ flex: 1, overflow: "auto", padding: "6px 4px", fontFamily: "var(--font-mono)", fontSize: 11 }}>
          {workspace.map(node => <FileNode key={node.path} node={node} depth={0} selected={selectedFile} onSelect={setSelectedFile}/>)}
        </div>
      </div>

      {/* Right: experiments + selected file preview */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, minHeight: 0 }}>
        {/* Experiment table */}
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden", flex: 1, minHeight: 0 }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="flask" size={12} style={{ color: "var(--fg-muted)" }}/>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ws.experimentRuns")}</span>
            <span className="chip">{FIX_EXPERIMENTS.length}</span>
            <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--fg-muted)" }}>
              <span style={{ color: "var(--success)" }}>3 {t("ws.reproducible")}</span> · <span style={{ color: "var(--unknown)" }}>1 {t("ws.notReproducible")}</span>
            </span>
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            <div className="row head" style={{ gridTemplateColumns: "1fr 200px auto auto 90px" }}>
              <span>{t("ws.colLabelId")}</span><span>{t("ws.colMetrics")}</span><span>{t("ws.colReprod")}</span><span>{t("lbl.duration")}</span><span>{t("lbl.started")}</span>
            </div>
            {FIX_EXPERIMENTS.map(e => (
              <div key={e.experiment_run_id} onClick={() => setSelectedExp(e.experiment_run_id)} className="row" style={{
                gridTemplateColumns: "1fr 200px auto auto 90px",
                background: selectedExp === e.experiment_run_id ? "var(--bg-hover)" : undefined,
                cursor: "pointer",
                alignItems: "flex-start",
              }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500 }}>{e.label}</div>
                  <DigestText value={e.experiment_run_id} length={20} prefix={false}/>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {Object.entries(e.metrics).slice(0, 3).map(([k, v]) => (
                    <span key={k} style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)", background: "var(--bg-raised)", padding: "1px 5px", borderRadius: 2 }}>
                      <span style={{ color: "var(--fg-faint)" }}>{k}</span>={typeof v === "number" ? (v < 1 ? v.toFixed(3) : v.toString()) : String(v).slice(0, 20)}
                    </span>
                  ))}
                </div>
                <span>
                  {e.reproduction_available
                    ? <StatusBadge tone="success" icon="check" label={t("ws.stateReprod")} filled size="sm"/>
                    : <StatusBadge tone="unknown" icon="q" label={t("ws.stateNotReprod")} dashed size="sm"/>}
                </span>
                <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>{Math.floor(e.duration_s/60)}m{e.duration_s%60}s</span>
                <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{e.started_at.slice(11,16)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Selected experiment digests */}
        {exp && (
          <div className="panel" style={{ padding: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
              <Icon name="flask" size={12} style={{ color: "var(--fg-muted)" }}/>
              <span style={{ fontSize: 12, fontWeight: 500 }}>{exp.label}</span>
              {exp.reproduction_available
                ? <StatusBadge tone="success" icon="check" label={t("ws.stateReprod")} filled size="sm"/>
                : <StatusBadge tone="unknown" icon="q" label={t("ws.stateNotReprod")} dashed size="sm"/>}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 4 }}>{t("ws.imageDigest")}</div>
                {exp.image_digest
                  ? <DigestText value={exp.image_digest} length={16}/>
                  : <UnknownValue hint={t("ws.imageMissing")}/>}
              </div>
              <div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 4 }}>{t("ws.envDigest")}</div>
                <DigestText value={exp.environment_digest} length={16}/>
              </div>
            </div>
            {exp.reproduction_note && (
              <div style={{ marginTop: 12, padding: 12, background: "var(--unknown-dim)", border: "1px dashed var(--unknown-line)", borderRadius: 6, fontSize: 11, color: "var(--unknown)", lineHeight: 1.55 }}>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 4 }}>{t("ws.repNote")}</div>
                {exp.reproduction_note}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const FileNode = ({ node, depth, selected, onSelect }) => {
  const [open, setOpen] = useState(true);
  const isFile = node.type === "file";
  const isSelected = selected === node.path;
  return (
    <>
      <div style={{
        display: "grid", gridTemplateColumns: "1fr auto auto",
        gap: 8, padding: "3px 8px", paddingLeft: 8 + depth * 14,
        cursor: "pointer", borderRadius: 3,
        background: isSelected ? "var(--bg-hover)" : "transparent",
        color: node.highlight ? "var(--accent)" : "var(--fg-muted)",
      }} onClick={() => isFile ? onSelect(node.path) : setOpen(!open)}>
        <span style={{ display: "flex", alignItems: "center", gap: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {!isFile && <Icon name={open ? "chevron-d" : "chevron-r"} size={9}/>}
          {isFile && <span style={{ width: 9 }}/>}
          <Icon name={isFile ? "book" : "hex"} size={10} style={{ color: "var(--fg-faint)" }}/>
          <span>{node.path.split("/").filter(Boolean).pop()}{!isFile && "/"}</span>
        </span>
        {isFile && <span style={{ fontSize: 9, color: "var(--fg-faint)" }}>{node.size}</span>}
        {isFile && <span style={{ fontSize: 9, color: "var(--fg-faint)" }}>{node.modified}</span>}
      </div>
      {!isFile && open && node.children && node.children.map(child => (
        <FileNode key={child.path} node={child} depth={depth + 1} selected={selected} onSelect={onSelect}/>
      ))}
    </>
  );
};

Object.assign(window, { WorkspaceScreen });
