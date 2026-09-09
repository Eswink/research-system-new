import type { ClaimDto, ClaimMapDto, EvidenceDto } from "../../api/types";

export interface ProvenanceNode {
  id: string;
  entityId: string;
  kind: "source" | "evidence" | "claim";
  label: string;
  status: string;
  fields: readonly (readonly [string, string])[];
}

export interface ProvenanceEdge {
  id: string;
  from: string;
  to: string;
  label: string;
  strength?: number;
}

export interface ProvenanceModel {
  nodes: ProvenanceNode[];
  edges: ProvenanceEdge[];
  issues: string[];
}

const nodeId = (kind: string, id: string) => `${kind}:${id}`;

/** Only explicit DTO references form edges. Shared names, positions and counts imply nothing. */
export function buildProvenance(
  claims: ClaimMapDto,
  evidence: readonly EvidenceDto[] | null,
): ProvenanceModel {
  const nodes = new Map<string, ProvenanceNode>();
  const edges: ProvenanceEdge[] = [];
  const issues: string[] = [];
  for (const item of evidence ?? []) addEvidence(nodes, edges, item);
  for (const claim of claims.claims) nodes.set(nodeId("claim", claim.id), claimNode(claim));
  for (const claim of claims.claims) addRelations({ nodes, edges, issues }, claim);
  return { nodes: [...nodes.values()], edges, issues };
}

function claimNode(claim: ClaimDto): ProvenanceNode {
  return {
    id: nodeId("claim", claim.id),
    entityId: claim.id,
    kind: "claim",
    label: claim.statement,
    status: claim.status,
    fields: [
      ["Claim", claim.id],
      ["Statement", claim.statement],
      ["Status", claim.status],
      ["Author", claim.author ?? "—"],
    ],
  };
}

function addEvidence(
  nodes: Map<string, ProvenanceNode>,
  edges: ProvenanceEdge[],
  item: EvidenceDto,
) {
  const id = nodeId("evidence", item.id);
  nodes.set(id, {
    id,
    entityId: item.id,
    kind: "evidence",
    label: item.id,
    status: "RETURNED",
    fields: evidenceFields(item),
  });
  const sources = [
    ["source_ref", item.source_ref],
    ["artifact_id", item.artifact_id],
  ] as const;
  for (const [kind, reference] of sources) {
    if (reference === null || reference === "") continue;
    const sourceId = nodeId(kind, reference);
    nodes.set(sourceId, {
      id: sourceId,
      entityId: reference,
      kind: "source",
      label: reference,
      status: "REFERENCE ONLY",
      fields: [[kind, reference]],
    });
    edges.push({ id: `${sourceId}->${id}`, from: sourceId, to: id, label: kind });
  }
}

function evidenceFields(item: EvidenceDto): ProvenanceNode["fields"] {
  return [
    ["Evidence", item.id],
    ["Source ref", item.source_ref],
    ["Content digest", item.content_digest],
    ["Run", item.run_id ?? "—"],
    ["Experiment", item.experiment_run_id ?? "—"],
    ["Artifact", item.artifact_id ?? "—"],
    ["Image digest", item.image_digest ?? "—"],
    ["Environment digest", item.environment_digest ?? "—"],
    ["Manifest digest", item.manifest_digest ?? "—"],
    ["Model refs", item.model_refs.join(", ")],
  ];
}

function addRelations(
  context: {
    nodes: Map<string, ProvenanceNode>;
    edges: ProvenanceEdge[];
    issues: string[];
  },
  claim: ClaimDto,
) {
  for (const [index, relation] of claim.relations.entries()) {
    if (relation.claim_id !== claim.id) {
      context.issues.push(`${claim.id}: relation targets ${relation.claim_id}; edge not projected`);
      continue;
    }
    const from = nodeId("evidence", relation.evidence_id);
    if (!context.nodes.has(from))
      context.nodes.set(from, {
        id: from,
        entityId: relation.evidence_id,
        kind: "evidence",
        label: relation.evidence_id,
        status: "REFERENCE NOT RESOLVED",
        fields: [["Evidence ref", relation.evidence_id]],
      });
    context.edges.push({
      id: `${claim.id}:${String(index)}`,
      from,
      to: nodeId("claim", claim.id),
      label: relation.relation,
      strength: relation.strength,
    });
  }
}

/** Deterministic three-column layout; positions carry no causal or ranking meaning. */
export function layoutProvenance(model: ProvenanceModel) {
  const columns = { source: 0, evidence: 1, claim: 2 } as const;
  const counts = { source: 0, evidence: 0, claim: 0 };
  const nodes = model.nodes.map((node) => {
    const row = counts[node.kind];
    counts[node.kind] += 1;
    return { ...node, x: 20 + columns[node.kind] * 260, y: 44 + row * 100 };
  });
  return {
    nodes,
    width: 780,
    height: Math.max(340, 64 + Math.max(...Object.values(counts)) * 100),
  };
}
