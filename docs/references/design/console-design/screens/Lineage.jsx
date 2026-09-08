/* Lineage Screen — provenance DAG.
   Shows dataset → prompt → run → model → endpoint → claim chain.
   Uses ForceGraph for the map; a side panel shows breadcrumb + impact. */

const LineageScreen = () => {
  const { t } = useI18n();
  const [selectedNode, setSelectedNode] = useState("mdl_claude_opus_41");
  const [filter, setFilter] = useState("all"); // all | upstream | downstream

  // Build the DAG from existing fixtures.
  const nodes = useMemo(() => {
    const n = [];
    (FIX_DATASETS || []).slice(0, 3).forEach(d => n.push({ id: d.id, label: d.name.slice(0, 20), kind: "dataset" }));
    (FIX_PROMPTS || []).slice(0, 3).forEach(p => n.push({ id: p.id, label: p.name.slice(0, 20), kind: "prompt" }));
    (FIX_RUNS_HISTORY || []).slice(0, 4).forEach(r => n.push({ id: r.id, label: r.label.slice(0, 20), kind: "run" }));
    (FIX_REGISTERED_MODELS || []).slice(0, 3).forEach(m => n.push({ id: m.id, label: m.family.slice(0, 20), kind: "model" }));
    (FIX_CLAIMS || []).slice(0, 4).forEach(c => n.push({ id: c.id, label: (c.statement || c.id).slice(0, 20), kind: "claim" }));
    // add a couple synthetic endpoints for the deploy stage
    n.push({ id: "ep_prod_us_east", label: "prod-us-east", kind: "endpoint" });
    n.push({ id: "ep_stg_eu", label: "stg-eu-frankfurt", kind: "endpoint" });
    return n;
  }, []);

  const edges = useMemo(() => {
    const ds = (FIX_DATASETS || []).slice(0, 3);
    const pr = (FIX_PROMPTS || []).slice(0, 3);
    const rn = (FIX_RUNS_HISTORY || []).slice(0, 4);
    const md = (FIX_REGISTERED_MODELS || []).slice(0, 3);
    const cl = (FIX_CLAIMS || []).slice(0, 4);
    const e = [];
    // dataset → prompt (2 datasets feed the first 2 prompts)
    ds.forEach((d, i) => pr[i] && e.push({ from: d.id, to: pr[i].id }));
    // prompt+dataset → run
    pr.forEach((p, i) => rn[i] && e.push({ from: p.id, to: rn[i].id }));
    ds.forEach((d, i) => rn[i] && e.push({ from: d.id, to: rn[i].id }));
    // model → run (models called by runs)
    rn.forEach((r, i) => md[i % md.length] && e.push({ from: md[i % md.length].id, to: r.id }));
    // run → claim
    rn.forEach((r, i) => cl[i] && e.push({ from: r.id, to: cl[i].id }));
    // model → endpoint (deploy)
    e.push({ from: md[0].id, to: "ep_prod_us_east" });
    e.push({ from: md[1].id, to: "ep_stg_eu" });
    return e;
  }, []);

  const selected = nodes.find(n => n.id === selectedNode);

  // Compute upstream/downstream sets from the selected node.
  const traverse = (startId, direction) => {
    const visited = new Set([startId]);
    const stack = [startId];
    while (stack.length) {
      const cur = stack.pop();
      edges.forEach(ed => {
        const next = direction === "up" ? (ed.to === cur ? ed.from : null) : (ed.from === cur ? ed.to : null);
        if (next && !visited.has(next)) { visited.add(next); stack.push(next); }
      });
    }
    visited.delete(startId);
    return [...visited];
  };
  const upstream = selectedNode ? traverse(selectedNode, "up") : [];
  const downstream = selectedNode ? traverse(selectedNode, "down") : [];

  const kindColors = {
    dataset: "var(--success)",
    prompt: "var(--accent)",
    run: "var(--warn)",
    model: "var(--unknown)",
    endpoint: "var(--fg-muted)",
    claim: "var(--danger)",
  };
  const kindIcons = {
    dataset: "book",
    prompt: "diamond",
    run: "play",
    model: "hex",
    endpoint: "wifi",
    claim: "shield",
  };

  const filteredNodeIds = filter === "all" ? null
    : filter === "upstream" ? new Set([selectedNode, ...upstream])
    : new Set([selectedNode, ...downstream]);

  const graphNodes = nodes.map(n => ({
    id: n.id,
    label: n.label,
    group: n.kind,
    highlighted: filteredNodeIds ? filteredNodeIds.has(n.id) : (n.id === selectedNode || upstream.includes(n.id) || downstream.includes(n.id)),
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1, minHeight: 0 }}>
      <PageToolbar title={t("ln.title")} subtitle={t("ln.subtitle")}>
        <ViewSwitcher value={filter} onChange={setFilter} views={[
          { value: "all", label: t("ln.filterAll") },
          { value: "upstream", label: t("ln.filterUp") },
          { value: "downstream", label: t("ln.filterDown") },
        ]}/>
        <button className="btn sm"><Icon name="external" size={11}/> {t("ln.exportDot")}</button>
      </PageToolbar>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 12, flex: 1, minHeight: 0 }}>
        {/* Graph */}
        <div className="panel" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span style={{ fontSize: 12, fontWeight: 500 }}>{t("ln.provGraph")}</span>
            <span className="chip">{nodes.length} {t("ln.nodes")}</span>
            <span className="chip">{edges.length} {t("ln.edges")}</span>
            <div style={{ marginLeft: "auto", display: "flex", gap: 10, fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-muted)" }}>
              {Object.entries(kindColors).map(([k, c]) => (
                <span key={k} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <Icon name={kindIcons[k]} size={9} style={{ color: c }}/>
                  {t(`ln.kind.${k}`)}
                </span>
              ))}
            </div>
          </div>
          <div style={{ flex: 1, minHeight: 0, background: "var(--bg-sunken)", padding: 8, overflow: "auto" }} className="canvas-bg">
            <ForceGraph
              nodes={graphNodes}
              edges={edges}
              width={900} height={520}
              groupColors={kindColors}
              onNodeClick={(id) => setSelectedNode(id)}
              selectedId={selectedNode}
            />
          </div>
        </div>

        {/* Side panel — selected details */}
        <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          {selected ? (
            <>
              <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <Icon name={kindIcons[selected.kind]} size={13} style={{ color: kindColors[selected.kind] }}/>
                  <span className="mono" style={{ fontSize: 10, color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase" }}>{selected.kind}</span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 500, fontFamily: "var(--font-mono)" }}>{selected.label}</div>
                <div className="mono" style={{ fontSize: 10, color: "var(--fg-faint)", marginTop: 4 }}>{selected.id}</div>
              </div>
              <div style={{ flex: 1, overflow: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 12 }}>
                {/* Impact stats */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  <div style={{ padding: 10, background: "var(--bg-raised)", borderRadius: 6 }}>
                    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{t("ln.upstream")}</div>
                    <div style={{ fontSize: 20, fontFamily: "var(--font-mono)", fontWeight: 500, marginTop: 2 }}>{upstream.length}</div>
                  </div>
                  <div style={{ padding: 10, background: "var(--bg-raised)", borderRadius: 6 }}>
                    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em" }}>{t("ln.downstream")}</div>
                    <div style={{ fontSize: 20, fontFamily: "var(--font-mono)", fontWeight: 500, marginTop: 2, color: "var(--warn)" }}>{downstream.length}</div>
                  </div>
                </div>

                {/* Upstream list */}
                {upstream.length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>{t("ln.upstreamDeps")}</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      {upstream.map(id => {
                        const nn = nodes.find(x => x.id === id);
                        if (!nn) return null;
                        return (
                          <button key={id} onClick={() => setSelectedNode(id)} style={{
                            display: "flex", alignItems: "center", gap: 8,
                            padding: "6px 8px", background: "var(--bg-raised)",
                            border: "1px solid var(--border)", borderRadius: 4,
                            cursor: "pointer", textAlign: "left", color: "inherit",
                            fontFamily: "inherit",
                          }}>
                            <Icon name={kindIcons[nn.kind]} size={11} style={{ color: kindColors[nn.kind] }}/>
                            <span style={{ fontSize: 11, fontWeight: 500 }}>{nn.label}</span>
                            <span className="mono" style={{ marginLeft: "auto", fontSize: 9, color: "var(--fg-faint)" }}>{nn.kind}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Downstream list */}
                {downstream.length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>{t("ln.downstreamImpact")}</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      {downstream.map(id => {
                        const nn = nodes.find(x => x.id === id);
                        if (!nn) return null;
                        return (
                          <button key={id} onClick={() => setSelectedNode(id)} style={{
                            display: "flex", alignItems: "center", gap: 8,
                            padding: "6px 8px", background: "var(--bg-raised)",
                            border: "1px solid var(--border)", borderRadius: 4,
                            borderLeft: "2px solid var(--warn-line)",
                            cursor: "pointer", textAlign: "left", color: "inherit",
                            fontFamily: "inherit",
                          }}>
                            <Icon name={kindIcons[nn.kind]} size={11} style={{ color: kindColors[nn.kind] }}/>
                            <span style={{ fontSize: 11, fontWeight: 500 }}>{nn.label}</span>
                            <span className="mono" style={{ marginLeft: "auto", fontSize: 9, color: "var(--fg-faint)" }}>{nn.kind}</span>
                          </button>
                        );
                      })}
                    </div>
                    <div style={{ marginTop: 8, padding: 8, background: "var(--warn-dim)", border: "1px solid var(--warn-line)", borderRadius: 4, fontSize: 10, color: "var(--warn)", display: "flex", gap: 6 }}>
                      <Icon name="warn-tri" size={11}/>
                      {t("ln.impactWarn").replace("{n}", downstream.length)}
                    </div>
                  </div>
                )}
              </div>
              <div style={{ padding: 12, borderTop: "1px solid var(--border)", display: "flex", gap: 6 }}>
                <button className="btn sm" style={{ flex: 1 }}><Icon name="external" size={10}/> {t("ln.openNode")}</button>
                <button className="btn sm ghost"><Icon name="copy" size={10}/></button>
              </div>
            </>
          ) : (
            <EmptyState icon="graph" title={t("ln.emptyTitle")} description={t("ln.emptyDesc")}/>
          )}
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { LineageScreen });
