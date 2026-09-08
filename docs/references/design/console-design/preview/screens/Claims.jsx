/* Screen 7: Claims & Evidence Map — the differentiator (P2 hard rule).
   Graph ↔ Table dual view. PROPOSED = dashed / faded. */

const ClaimsScreen = ({ initialView = "graph" }) => {
  const { t } = useI18n();
  const [view, setView] = useState(initialView);
  const [selectedClaimId, setSelectedClaimId] = useState("clm_h3_opus_stable"); // DISPUTED — most interesting
  const [filter, setFilter] = useState("all");

  const filteredClaims = filter === "all" ? FIX_CLAIMS : FIX_CLAIMS.filter(c => c.status === filter);
  const selectedClaim = FIX_CLAIMS.find(c => c.id === selectedClaimId);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 380px", gap: 12, flex: 1, minHeight: 0 }}>
      <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Toolbar */}
        <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ display: "flex", gap: 4, background: "var(--bg-raised)", padding: 2, borderRadius: 6, border: "1px solid var(--border)" }}>
            {[["graph",t("tw.claimsGraph"),"graph"],["table",t("tw.claimsTable"),"menu"]].map(([v,l,icn]) => (
              <button key={v} onClick={() => setView(v)} className="btn sm ghost" style={{
                background: view === v ? "var(--bg-hover)" : "transparent",
                color: view === v ? "var(--fg)" : "var(--fg-muted)",
                fontWeight: view === v ? 500 : 400,
                border: view === v ? "1px solid var(--border-strong)" : "1px solid transparent",
              }}><Icon name={icn} size={10}/> {l}</button>
            ))}
          </div>
          <div className="vr" style={{ height: 20 }}/>
          <div style={{ display: "flex", gap: 4 }}>
            {[["all",FIX_CLAIMS.length],["VERIFIED",FIX_CLAIMS.filter(c=>c.status==="VERIFIED").length],["PROPOSED",FIX_CLAIMS.filter(c=>c.status==="PROPOSED").length],["DISPUTED",FIX_CLAIMS.filter(c=>c.status==="DISPUTED").length],["REFUTED",FIX_CLAIMS.filter(c=>c.status==="REFUTED").length]].map(([s,n]) => (
              <button key={s} onClick={() => setFilter(s)} className="btn sm ghost" style={{
                background: filter === s ? "var(--bg-hover)" : "transparent",
                color: filter === s ? "var(--fg)" : "var(--fg-muted)",
                fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.06em",
              }}>{s.toLowerCase()} <span style={{ opacity: 0.6, marginLeft: 4 }}>{n}</span></button>
            ))}
          </div>
          <span style={{ marginLeft: "auto", fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>
            {FIX_EVIDENCE.length} {t("cl.evidence")} {new Set(FIX_EVIDENCE.map(e => e.source_ref)).size} {t("cl.sources")}
          </span>
        </div>

        {/* View content */}
        <div style={{ flex: 1, overflow: "auto", position: "relative" }}>
          {view === "graph"
            ? <ClaimsGraph claims={filteredClaims} selectedId={selectedClaimId} onSelect={setSelectedClaimId}/>
            : <ClaimsTable claims={filteredClaims} selectedId={selectedClaimId} onSelect={setSelectedClaimId}/>}
        </div>
      </div>

      {/* Right rail: claim detail */}
      <ClaimDetail claim={selectedClaim}/>
    </div>
  );
};

// ─── Graph view — SVG ───────────────────────────────────
const ClaimsGraph = ({ claims, selectedId, onSelect }) => {
  // Layout: place claims left/center, evidence orbiting.
  const W = 900, H = 620;

  // Position claims in a rough grid
  const layout = useMemo(() => {
    const positions = {};
    // Central claim (selected) gets center, others around it.
    const rows = 3;
    claims.forEach((c, i) => {
      const col = Math.floor(i / rows);
      const row = i % rows;
      positions[c.id] = {
        x: 150 + col * 260,
        y: 100 + row * 180,
      };
    });
    return positions;
  }, [claims]);

  // Evidence positions relative to their claim
  const evidencePositions = {};
  FIX_EVIDENCE.forEach(ev => {
    const claimPos = layout[ev.claim_id];
    if (!claimPos) return;
    if (!evidencePositions[ev.claim_id]) evidencePositions[ev.claim_id] = [];
    const idx = evidencePositions[ev.claim_id].length;
    const angle = (idx * 60 + 90) * Math.PI / 180;
    const r = 90;
    evidencePositions[ev.claim_id].push({
      ...ev,
      x: claimPos.x + Math.cos(angle) * r,
      y: claimPos.y + Math.sin(angle) * r,
    });
  });

  return (
    <div style={{ width: "100%", height: "100%", overflow: "auto", background: "var(--bg-sunken)" }}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ display: "block" }}>
        <defs>
          <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
            <path d="M 24 0 L 0 0 0 24" fill="none" stroke="var(--border-subtle)" strokeWidth="0.5"/>
          </pattern>
          <marker id="arrow-supports" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--success)"/>
          </marker>
          <marker id="arrow-refutes" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--danger)"/>
          </marker>
        </defs>
        <rect width={W} height={H} fill="url(#grid)" opacity="0.5"/>

        {/* Edges */}
        {Object.values(evidencePositions).flat().map(ev => {
          const claimPos = layout[ev.claim_id];
          const color = ev.relation === "REFUTES" ? "var(--danger)" : "var(--success)";
          return (
            <line key={`edge-${ev.id}`}
              x1={ev.x} y1={ev.y} x2={claimPos.x} y2={claimPos.y}
              stroke={color} strokeWidth={1 + ev.strength * 1.2} strokeOpacity={0.35}
              strokeDasharray={ev.relation === "REFUTES" ? "4 3" : undefined}
              markerEnd={`url(#arrow-${ev.relation.toLowerCase()})`}
            />
          );
        })}

        {/* Evidence nodes */}
        {Object.values(evidencePositions).flat().map(ev => {
          const kindIcon = ev.kind === "literature" ? "book" : ev.kind === "experiment" ? "flask" : "square";
          return (
            <g key={ev.id} style={{ cursor: "pointer" }}>
              <circle cx={ev.x} cy={ev.y} r={12}
                fill="var(--bg-raised)" stroke="var(--border-strong)" strokeWidth="1"/>
              <foreignObject x={ev.x - 6} y={ev.y - 6} width="12" height="12">
                <div style={{ color: "var(--fg-muted)" }}><Icon name={kindIcon} size={12}/></div>
              </foreignObject>
              <text x={ev.x} y={ev.y + 26} textAnchor="middle" fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-faint)">
                {ev.id}
              </text>
            </g>
          );
        })}

        {/* Claim nodes */}
        {claims.map(c => {
          const pos = layout[c.id];
          if (!pos) return null;
          const selected = c.id === selectedId;
          const isProposed = c.status === "PROPOSED";
          const statusColor = {
            VERIFIED: "var(--success)", PROPOSED: "var(--fg-faint)",
            DISPUTED: "var(--warn)", REFUTED: "var(--danger)",
          }[c.status];
          return (
            <g key={c.id} style={{ cursor: "pointer" }} onClick={() => onSelect(c.id)}>
              {selected && (
                <rect x={pos.x - 96} y={pos.y - 32} width={192} height={64} rx={6}
                  fill="none" stroke="var(--accent)" strokeWidth={1.5} strokeDasharray="4 3" opacity={0.8}/>
              )}
              <rect x={pos.x - 88} y={pos.y - 26} width={176} height={52} rx={4}
                fill={isProposed ? "transparent" : "var(--bg-panel)"}
                stroke={statusColor}
                strokeWidth={selected ? 2 : 1}
                strokeDasharray={isProposed ? "3 3" : undefined}
                opacity={isProposed ? 0.75 : 1}
              />
              <foreignObject x={pos.x - 82} y={pos.y - 22} width={164} height={44}>
                <div style={{
                  fontSize: 10, lineHeight: 1.35, color: isProposed ? "var(--fg-muted)" : "var(--fg)",
                  overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical",
                  fontStyle: isProposed ? "italic" : "normal",
                }}>{c.statement}</div>
              </foreignObject>
              <foreignObject x={pos.x - 88} y={pos.y - 44} width={176} height={16}>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <ClaimStatusBadge status={c.status}/>
                  <span style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{c.evidence_count}ev</span>
                </div>
              </foreignObject>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// ─── Table view ─────────────────────────────────────────
const ClaimsTable = ({ claims, selectedId, onSelect }) => { const { t } = useI18n(); return (
  <div>
    <div className="row head" style={{ gridTemplateColumns: "auto 1fr 90px 60px 60px 130px" }}>
      <span>{t("lbl.status")}</span><span>{t("cl.tHead.statement")}</span><span>{t("cl.tHead.id")}</span><span>{t("cl.tHead.ev")}</span><span>{t("cl.tHead.src")}</span><span>{t("lbl.updated")}</span>
    </div>
    {claims.map(c => {
      const isProposed = c.status === "PROPOSED";
      return (
        <div key={c.id} className="row"
          style={{
            gridTemplateColumns: "auto 1fr 90px 60px 60px 130px",
            background: c.id === selectedId ? "var(--bg-hover)" : undefined,
            cursor: "pointer",
            opacity: isProposed ? 0.75 : 1,
          }}
          onClick={() => onSelect(c.id)}>
          <ClaimStatusBadge status={c.status}/>
          <span style={{
            fontSize: 12, lineHeight: 1.45,
            fontStyle: isProposed ? "italic" : "normal",
            color: isProposed ? "var(--fg-muted)" : "var(--fg)",
          }}>{c.statement}</span>
          <DigestText value={c.id} length={8} prefix={false}/>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: c.evidence_count === 0 ? "var(--unknown)" : "var(--fg-muted)" }}>
            {c.evidence_count === 0 ? "0*" : c.evidence_count}
          </span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: c.source_count === 0 ? "var(--unknown)" : "var(--fg-muted)" }}>
            {c.source_count === 0 ? "0*" : c.source_count}
          </span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--fg-faint)" }}>{c.updated_at.slice(5,16).replace("T"," ")}</span>
        </div>
      );
    })}
  </div>
)};

// ─── Claim detail rail ──────────────────────────────────
const ClaimDetail = ({ claim }) => { const { t } = useI18n();
  if (!claim) return null;
  const evidence = FIX_EVIDENCE.filter(e => e.claim_id === claim.id);
  const supports = evidence.filter(e => e.relation === "SUPPORTS");
  const refutes = evidence.filter(e => e.relation === "REFUTES");
  const isProposed = claim.status === "PROPOSED";

  return (
    <div className="panel" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
          <ClaimStatusBadge status={claim.status}/>
          <DigestText value={claim.id} length={12} prefix={false}/>
        </div>
        <div style={{
          fontSize: 13, lineHeight: 1.5,
          color: isProposed ? "var(--fg-muted)" : "var(--fg)",
          fontStyle: isProposed ? "italic" : "normal",
        }}>
          {claim.statement}
        </div>
        {claim.dispute_note && (
          <div style={{ marginTop: 8, padding: 8, background: "var(--warn-dim)", border: "1px solid var(--warn-line)", borderRadius: 4, fontSize: 11, color: "var(--warn)" }}>
            <Icon name="warn-tri" size={10}/> {claim.dispute_note}
          </div>
        )}
        {claim.refutation_note && (
          <div style={{ marginTop: 8, padding: 8, background: "var(--danger-dim)", border: "1px solid var(--danger-line)", borderRadius: 4, fontSize: 11, color: "var(--danger)" }}>
            <Icon name="x" size={10}/> {claim.refutation_note}
          </div>
        )}
      </div>

      <div style={{ flex: 1, overflow: "auto" }}>
        {isProposed && claim.evidence_count === 0 && (
          <div style={{ padding: 16, margin: 12, border: "1px dashed var(--border-strong)", borderRadius: 6, textAlign: "center" }}>
            <div style={{ color: "var(--fg-muted)", fontSize: 12, marginBottom: 4 }}>
              <Icon name="circle-dash" size={12}/> {t("cl.noEvidence")}
            </div>
            <div style={{ color: "var(--fg-faint)", fontSize: 11, lineHeight: 1.5 }}>
              {t("cl.awaitingEv").replace("{a}", "").split("PROPOSED")[0]}<span className="mono">ag_pi_01</span>{t("cl.awaitingEv").split("{a}")[1]}
            </div>
          </div>
        )}

        {supports.length > 0 && (
          <>
            <div style={{ padding: "8px 14px", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", background: "var(--bg-raised)", display: "flex", justifyContent: "space-between" }}>
              <span>{t("cl.supporting")} {supports.length}</span>
              <span style={{ color: "var(--success)" }}>SUPPORTS</span>
            </div>
            {supports.map(ev => <EvidenceRow key={ev.id} ev={ev}/>)}
          </>
        )}

        {refutes.length > 0 && (
          <>
            <div style={{ padding: "8px 14px", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)", letterSpacing: "0.06em", textTransform: "uppercase", background: "var(--bg-raised)", display: "flex", justifyContent: "space-between" }}>
              <span>{t("cl.refuting")} {refutes.length}</span>
              <span style={{ color: "var(--danger)" }}>REFUTES</span>
            </div>
            {refutes.map(ev => <EvidenceRow key={ev.id} ev={ev}/>)}
          </>
        )}
      </div>

      {claim.status === "PROPOSED" && (
        <div style={{ padding: 12, borderTop: "1px solid var(--border)", background: "var(--bg-raised)" }}>
          <div style={{ fontSize: 10, color: "var(--fg-faint)", marginBottom: 6, fontFamily: "var(--font-mono)", letterSpacing: "0.06em", textTransform: "uppercase" }}>{t("cl.upgradePath")}</div>
          <div style={{ fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.5, marginBottom: 8 }}>
            {t("cl.upgradeMsg").split("{a}")[0]}<span className="mono" style={{ color: "var(--accent)" }}>promote_claim_to_verified</span>{t("cl.upgradeMsg").split("{a}")[1]}
          </div>
          <button className="btn sm" disabled aria-disabled="true" title={t("cl.needEv")}>
            <Icon name="lock" size={10}/> {t("cl.requestUpgrade")}
          </button>
        </div>
      )}
    </div>
  );
};

const EvidenceRow = ({ ev }) => { const { t } = useI18n();
  const kindIcon = ev.kind === "literature" ? "book" : ev.kind === "experiment" ? "flask" : "square";
  const kindColor = ev.kind === "literature" ? "var(--accent)" : ev.kind === "experiment" ? "var(--warn)" : "var(--fg-muted)";
  return (
    <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-subtle)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <Icon name={kindIcon} size={11} style={{ color: kindColor }}/>
        <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: kindColor, textTransform: "uppercase", letterSpacing: "0.04em" }}>{ev.kind}</span>
        <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--fg-faint)" }}>{t("cl.evStrength")} {ev.strength.toFixed(2)}</span>
      </div>
      <div style={{ fontSize: 12, color: "var(--fg)", marginBottom: 4 }}>{ev.source_ref}</div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <DigestText value={ev.content_digest} label="content:" length={8}/>
        {ev.image_digest && <DigestText value={ev.image_digest} label="image:" length={8}/>}
        {ev.environment_digest && <DigestText value={ev.environment_digest} label="env:" length={8}/>}
      </div>
    </div>
  );
};

Object.assign(window, { ClaimsScreen });
