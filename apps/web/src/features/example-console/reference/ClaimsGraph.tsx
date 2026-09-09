import { useMemo } from "react";
import FIX_EVIDENCE from "../data/evidence.json";
import type * as E from "../exampleTypes";
import { ClaimStatusBadge } from "./ClaimStatusBadge";
import visual from "./ClaimsGraph.module.css";
import { Icon } from "./Icon";
import { ClaimsGraphdefs } from "./claims-graph/ClaimsGraphdefs";
import { ClaimsGraphrect } from "./claims-graph/ClaimsGraphrect";

interface GraphPoint {
  x: number;
  y: number;
}

type ClaimLayout = Record<string, GraphPoint>;
type PositionedEvidence = E.Evidence & GraphPoint;
type EvidenceLayout = Record<string, PositionedEvidence[]>;

function buildClaimLayout(claims: E.Claim[]): ClaimLayout {
  const positions: ClaimLayout = {};
  const rows = 3;
  claims.forEach((claim, index) => {
    const col = Math.floor(index / rows);
    const row = index % rows;
    positions[claim.id] = { x: 150 + col * 260, y: 100 + row * 180 };
  });
  return positions;
}

function buildEvidenceLayout(layout: ClaimLayout): EvidenceLayout {
  const positions: EvidenceLayout = {};
  FIX_EVIDENCE.forEach((evidence) => {
    const claimPos = layout[evidence.claim_id];
    if (claimPos === undefined) return;
    const cluster = positions[evidence.claim_id] ?? [];
    positions[evidence.claim_id] = cluster;
    const angle = ((cluster.length * 60 + 90) * Math.PI) / 180;
    const radius = 90;
    cluster.push({
      ...evidence,
      x: claimPos.x + Math.cos(angle) * radius,
      y: claimPos.y + Math.sin(angle) * radius,
    });
  });
  return positions;
}

export const ClaimsGraph = ({
  claims,
  selectedId,
  onSelect,
}: {
  claims: E.Claim[];
  selectedId: string;
  onSelect: (id: string) => void;
}) => {
  const W = 900,
    H = 620;
  const layout = useMemo(() => buildClaimLayout(claims), [claims]);
  const evidencePositions = useMemo(() => buildEvidenceLayout(layout), [layout]);

  return (
    <div className={visual.indicator}>
      <svg width={W} height={H} viewBox={`0 0 ${String(W)} ${String(H)}`} className={visual.chart}>
        <ClaimsGraphdefs {...{}} />
        <rect width={W} height={H} fill="url(#grid)" opacity="0.5" />
        <ClaimEvidenceEdges evidence={evidencePositions} layout={layout} />
        <ClaimEvidenceNodes evidence={evidencePositions} />
        <ClaimNodes {...{ claims, layout, selectedId, onSelect }} />
      </svg>
    </div>
  );
};

function ClaimEvidenceEdges({
  evidence,
  layout,
}: {
  evidence: EvidenceLayout;
  layout: ClaimLayout;
}) {
  return (
    <>
      {Object.values(evidence)
        .flat()
        .map((item) => {
          const claimPos = layout[item.claim_id];
          if (claimPos === undefined) return null;
          return (
            <line
              key={`edge-${item.id}`}
              x1={item.x}
              y1={item.y}
              x2={claimPos.x}
              y2={claimPos.y}
              stroke={item.relation === "REFUTES" ? "var(--danger)" : "var(--success)"}
              strokeWidth={1 + item.strength * 1.2}
              strokeOpacity={0.35}
              strokeDasharray={item.relation === "REFUTES" ? "4 3" : undefined}
              markerEnd={`url(#arrow-${item.relation.toLowerCase()})`}
            />
          );
        })}
    </>
  );
}

function ClaimEvidenceNodes({ evidence }: { evidence: EvidenceLayout }) {
  return (
    <>
      {Object.values(evidence)
        .flat()
        .map((item) => (
          <ClaimEvidenceNode key={item.id} evidence={item} />
        ))}
    </>
  );
}

function ClaimEvidenceNode({ evidence }: { evidence: PositionedEvidence }) {
  const icon =
    evidence.kind === "literature" ? "book" : evidence.kind === "experiment" ? "flask" : "square";
  return (
    <g className={visual.surface}>
      <circle
        cx={evidence.x}
        cy={evidence.y}
        r={12}
        fill="var(--bg-raised)"
        stroke="var(--border-strong)"
        strokeWidth="1"
      />
      <foreignObject x={evidence.x - 6} y={evidence.y - 6} width="12" height="12">
        <div className={visual.surface2}>
          <Icon name={icon} size={12} />
        </div>
      </foreignObject>
      <text
        x={evidence.x}
        y={evidence.y + 26}
        textAnchor="middle"
        fontSize="9"
        fontFamily="var(--font-mono)"
        fill="var(--fg-faint)"
      >
        {evidence.id}
      </text>
    </g>
  );
}

function ClaimNodes({
  claims,
  layout,
  selectedId,
  onSelect,
}: {
  claims: E.Claim[];
  layout: ClaimLayout;
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <>
      {claims.map((claim) => {
        const pos = layout[claim.id];
        return pos === undefined ? null : (
          <ClaimNode
            key={claim.id}
            claim={claim}
            pos={pos}
            selected={claim.id === selectedId}
            onSelect={onSelect}
          />
        );
      })}
    </>
  );
}

function ClaimNode({
  claim,
  pos,
  selected,
  onSelect,
}: {
  claim: E.Claim;
  pos: GraphPoint;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const isProposed = claim.status === "PROPOSED";
  const statusColor = {
    VERIFIED: "var(--success)",
    PROPOSED: "var(--fg-faint)",
    DISPUTED: "var(--warn)",
    REFUTED: "var(--danger)",
  }[claim.status];
  return (
    <g
      className={visual.surface3}
      onClick={() => {
        onSelect(claim.id);
      }}
    >
      {selected && <ClaimSelectionOutline pos={pos} />}
      <ClaimsGraphrect {...{ pos, isProposed, statusColor, selected }} />
      <ClaimNodeContent {...{ claim, pos, isProposed }} />
    </g>
  );
}

function ClaimSelectionOutline({ pos }: { pos: GraphPoint }) {
  return (
    <rect
      x={pos.x - 96}
      y={pos.y - 32}
      width={192}
      height={64}
      rx={6}
      fill="none"
      stroke="var(--accent)"
      strokeWidth={1.5}
      strokeDasharray="4 3"
      opacity={0.8}
    />
  );
}

function ClaimNodeContent({
  claim,
  pos,
  isProposed,
}: {
  claim: E.Claim;
  pos: GraphPoint;
  isProposed: boolean;
}) {
  return (
    <>
      <foreignObject x={pos.x - 82} y={pos.y - 22} width={164} height={44}>
        <div
          className={visual.caption}
          style={{
            color: isProposed ? "var(--fg-muted)" : "var(--fg)",
            fontStyle: isProposed ? "italic" : "normal",
          }}
        >
          {claim.statement}
        </div>
      </foreignObject>
      <foreignObject x={pos.x - 88} y={pos.y - 44} width={176} height={16}>
        <div className={visual.row}>
          <ClaimStatusBadge status={claim.status} />
          <span className={visual.caption2}>{claim.evidence_count}ev</span>
        </div>
      </foreignObject>
    </>
  );
}
