import { useMemo, useState, type Dispatch, type SetStateAction } from "react";
import type { ClaimDto, ClaimMapDto, EvidenceDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { ProvenanceGraph } from "../lineage/ProvenanceGraph";
import {
  buildProvenance,
  type ProvenanceModel,
  type ProvenanceNode,
} from "../lineage/provenanceModel";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

export function ClaimsWorkspace({
  claims,
  evidence,
  initialView = "graph",
}: {
  claims: ClaimMapDto;
  evidence: EvidenceDto[] | null;
  initialView?: "graph" | "table";
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [view, setView] = useState(initialView);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const model = useMemo(() => buildProvenance(claims, evidence), [claims, evidence]);
  const selected =
    model.nodes.find((node) => node.id === selectedId) ??
    model.nodes.find((node) => node.kind === "claim");
  return (
    <ClaimsWorkspacePage
      {...{ claims, model, view, setView, zh, query, setQuery, selected, setSelectedId }}
    />
  );
}

interface ClaimsWorkspaceToolbarProps {
  view: string;
  setView: Dispatch<SetStateAction<"graph" | "table">>;
  zh: boolean;
  query: string;
  setQuery: Dispatch<SetStateAction<string>>;
  claims: ClaimMapDto;
}

interface ClaimsWorkspacePageProps {
  claims: ClaimMapDto;
  model: ProvenanceModel;
  view: string;
  setView: Dispatch<SetStateAction<"graph" | "table">>;
  zh: boolean;
  query: string;
  setQuery: Dispatch<SetStateAction<string>>;
  selected: ProvenanceNode | undefined;
  setSelectedId: Dispatch<SetStateAction<string | null>>;
}

function ClaimsWorkspacePage({
  claims,
  model,
  view,
  setView,
  zh,
  query,
  setQuery,
  selected,
  setSelectedId,
}: ClaimsWorkspacePageProps) {
  return (
    <div className={styles.page} data-testid="claim-map">
      <ClaimWarnings claims={claims} issues={model.issues} />
      <ClaimsWorkspaceToolbar {...{ view, setView, zh, query, setQuery, claims }} />
      <div className={styles.split}>
        <ProvenanceDetails node={selected} model={model} />
        {view === "graph" ? (
          <ProvenanceGraph
            model={model}
            selectedId={selected?.id ?? null}
            query={query}
            onSelect={(node) => {
              setSelectedId(node.id);
            }}
          />
        ) : (
          <ClaimsTable
            claims={claims.claims}
            query={query}
            selectedId={selected?.entityId ?? ""}
            onSelect={(claim) => {
              setSelectedId(`claim:${claim.id}`);
            }}
          />
        )}
      </div>
      <p className={styles.notice}>
        {zh
          ? "仅依据显式引用连边。未解析引用不等于证据已验证；来源引用不是下载链接。图节点位置不代表因果或排名。"
          : [
              "Only explicit references form edges. Unresolved references are not ",
              "verified evidence or download links. Position implies neither causation ",
              "nor ranking.",
            ].join("")}
      </p>
    </div>
  );
}

function ClaimsWorkspaceToolbar({
  view,
  setView,
  zh,
  query,
  setQuery,
  claims,
}: ClaimsWorkspaceToolbarProps) {
  return (
    <div className={styles.toolbar}>
      <button
        className="btn sm"
        type="button"
        aria-pressed={view === "graph"}
        onClick={() => {
          setView("graph");
        }}
      >
        {zh ? "关系图" : "Graph"}
      </button>
      <button
        className="btn sm"
        type="button"
        aria-pressed={view === "table"}
        onClick={() => {
          setView("table");
        }}
      >
        {zh ? "论断表" : "Claims table"}
      </button>
      <input
        type="search"
        className={`input ${styles.search ?? ""}`}
        value={query}
        aria-label={zh ? "搜索论断与引用" : "Search claims and references"}
        placeholder={zh ? "搜索文本、状态或 ID" : "Search text, state or ID"}
        onChange={(event) => {
          setQuery(event.target.value);
        }}
      />
      <Chip>{claims.claims.length} claims</Chip>
    </div>
  );
}

function ClaimsTable({
  claims,
  query,
  selectedId,
  onSelect,
}: {
  claims: ClaimDto[];
  query: string;
  selectedId: string;
  onSelect: (claim: ClaimDto) => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const columns: Column<ClaimDto>[] = [
    { key: "id", header: "Claim", render: (claim) => <span className="mono">{claim.id}</span> },
    { key: "statement", header: zh ? "论断" : "Statement", render: (claim) => claim.statement },
    {
      key: "state",
      header: zh ? "正式状态" : "Persisted state",
      render: (claim) => <Chip>{claim.status}</Chip>,
    },
    {
      key: "relations",
      header: zh ? "引用数" : "Relations",
      render: (claim) => claim.relations.length,
    },
  ];
  const needle = query.trim().toLocaleLowerCase();
  return (
    <Table
      columns={columns}
      rows={claims.filter((claim) =>
        `${claim.id} ${claim.statement} ${claim.status}`.toLocaleLowerCase().includes(needle),
      )}
      rowKey={(claim) => claim.id}
      selectable
      selectedKey={selectedId}
      onSelectRow={onSelect}
      ariaLabel={zh ? "论断表" : "Claims table"}
      empty={<EmptyState message={zh ? "没有匹配论断" : "No matching claims"} />}
    />
  );
}

function ClaimWarnings({ claims, issues }: { claims: ClaimMapDto; issues: string[] }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <>
      {claims.degraded && (
        <p className={styles.notice} role="status">
          DEGRADED · {zh ? "论断投影不完整" : "Claim projection is incomplete"}
        </p>
      )}
      {claims.unsupported_claims.length > 0 && (
        <p className={styles.notice} data-testid="unsupported-warning">
          {zh ? "缺少支持：" : "Unsupported claims: "}
          {claims.unsupported_claims.join(", ")}
        </p>
      )}
      {claims.contradictory_claims.length > 0 && (
        <p className={styles.notice} data-testid="contradiction-warning">
          {zh ? "矛盾关系：" : "Contradictions: "}
          {claims.contradictory_claims.join(", ")}
        </p>
      )}
      {issues.length > 0 && (
        <p className={styles.notice} role="status">
          {issues.join("; ")}
        </p>
      )}
    </>
  );
}

function ProvenanceDetails({
  node,
  model,
}: {
  node: ProvenanceNode | undefined;
  model: ProvenanceModel;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const relations = model.edges.filter((edge) => edge.from === node?.id || edge.to === node?.id);
  return (
    <PanelSection title={zh ? "来源与关系详情" : "Provenance and relation details"}>
      {node === undefined ? (
        <EmptyState message={zh ? "没有可检查节点" : "No nodes to inspect"} />
      ) : (
        <>
          <Chip>{node.status}</Chip>
          <KeyValueList fields={node.fields.map(([label, value]) => ({ label, value }))} />
          <ul className={styles.list}>
            {relations.map((edge) => (
              <li key={edge.id} className={styles.notice}>
                <strong>{edge.label}</strong>
                {edge.strength === undefined ? "" : ` · strength ${String(edge.strength)}`}
                <p className="mono">
                  {edge.from} → {edge.to}
                </p>
              </li>
            ))}
          </ul>
        </>
      )}
    </PanelSection>
  );
}
