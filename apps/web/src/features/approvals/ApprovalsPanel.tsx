import { useState, type Dispatch, type SetStateAction } from "react";
import type { ResourceState } from "../../hooks/useResource";
import type { ApprovalDto } from "../../api/types";
import { MetricCard } from "../../components/charts/MetricCard";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, ErrorState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { ApprovalConfirmation, ApprovalDetail, type PendingDecision } from "./ApprovalDetail";
import { RunApprovalHistory } from "./RunApprovalHistory";
import { useApprovals } from "./useApprovals";

export function ApprovalsPanel() {
  const { language } = useI18n();
  const zh = language === "zh";
  const flow = useApprovals();
  const [target, setTarget] = useState<PendingDecision | null>(null);
  const submit = async () => {
    if (target === null) return;
    await flow.decide(target.approval, target.action);
    setTarget(null);
  };
  return <ApprovalsPanelsection {...{ zh, flow, setTarget, target, submit }} />;
}

interface ApprovalsPanelsectionProps {
  zh: boolean;
  flow: {
    query: ResourceState<ApprovalDto[]>;
    error: string | null;
    decision: ApprovalDto | null;
    deciding: boolean;
    decide: (approval: ApprovalDto, action: "approve" | "deny") => Promise<void>;
  };
  setTarget: Dispatch<SetStateAction<PendingDecision | null>>;
  target: PendingDecision | null;
  submit: () => Promise<void>;
}

function ApprovalsPanelsection({
  zh,
  flow,
  setTarget,
  target,
  submit,
}: ApprovalsPanelsectionProps) {
  return (
    <section className={styles.page} data-testid="approvals-panel">
      <ApprovalsPanelPageHeader {...{ zh, flow }} />
      <ApprovalMetrics approvals={flow.query.phase === "ready" ? flow.query.data : null} />
      {flow.error !== null && <ErrorState message={flow.error} />}
      {flow.decision !== null && (
        <p className={styles.notice} role="status">
          {zh ? "后端已返回裁决结果：" : "Backend decision acknowledged: "}
          {flow.decision.id} · {flow.decision.status}
        </p>
      )}
      <ResourceBoundary state={flow.query}>
        {flow.query.data !== null && (
          <PendingApprovals
            approvals={flow.query.data}
            busy={flow.deciding || flow.query.phase !== "ready"}
            onRequest={setTarget}
          />
        )}
      </ResourceBoundary>
      <ApprovalConfirmation
        target={target}
        busy={flow.deciding}
        onConfirm={() => {
          void submit();
        }}
        onCancel={() => {
          setTarget(null);
        }}
      />
    </section>
  );
}

interface ApprovalsPanelPageHeaderProps {
  zh: boolean;
  flow: {
    query: ResourceState<ApprovalDto[]>;
    error: string | null;
    decision: ApprovalDto | null;
    deciding: boolean;
    decide: (approval: ApprovalDto, action: "approve" | "deny") => Promise<void>;
  };
}

function ApprovalsPanelPageHeader({ zh, flow }: ApprovalsPanelPageHeaderProps) {
  return (
    <PageHeader
      title={zh ? "审批中心" : "Approval center"}
      kicker="RUN / APPROVALS"
      description={
        zh
          ? "待决审批的真实投影。策略裁决、并发版本与正式审计由后端负责。"
          : [
              "Actual pending approvals. Policy, concurrent versions and formal audit ",
              "remain backend-owned.",
            ].join("")
      }
      actions={
        <button
          className="btn"
          type="button"
          onClick={flow.query.reload}
          disabled={flow.deciding || flow.query.phase === "loading"}
        >
          {zh ? "刷新审批" : "Refresh"}
        </button>
      }
    />
  );
}

function ApprovalMetrics({ approvals }: { approvals: ApprovalDto[] | null }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const metrics = [
    [zh ? "待决审批" : "Pending approvals", approvals?.length],
    [zh ? "高风险" : "High risk", approvals?.filter((item) => item.risk === "HIGH").length],
    [
      zh ? "严重风险" : "Critical risk",
      approvals?.filter((item) => item.risk === "CRITICAL").length,
    ],
    [
      zh ? "关联运行" : "Associated runs",
      approvals === null ? undefined : new Set(approvals.map((item) => item.run_id)).size,
    ],
  ] as const;
  return (
    <div className={styles.metrics}>
      {metrics.map(([label, value]) => (
        <MetricCard
          key={label}
          label={label}
          value={value === undefined ? "—" : String(value)}
          sub={zh ? "仅当前返回的待决集合" : "Current returned pending set only"}
          unknownWarn={value === undefined}
        />
      ))}
    </div>
  );
}

function PendingApprovals({
  approvals,
  busy,
  onRequest,
}: {
  approvals: ApprovalDto[];
  busy: boolean;
  onRequest: (target: PendingDecision) => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const filtered = approvals.filter((item) =>
    `${item.action} ${item.risk} ${item.run_id}`
      .toLocaleLowerCase()
      .includes(query.trim().toLocaleLowerCase()),
  );
  const selected = filtered.find((item) => item.id === selectedId) ?? filtered[0];
  return (
    <ApprovalsPanelPage
      {...{ query, zh, setQuery, filtered, selected, setSelectedId, busy, onRequest }}
    />
  );
}

interface ApprovalsPanelPageProps {
  query: string;
  zh: boolean;
  setQuery: Dispatch<SetStateAction<string>>;
  filtered: ApprovalDto[];
  selected: ApprovalDto | undefined;
  setSelectedId: Dispatch<SetStateAction<string>>;
  busy: boolean;
  onRequest: (target: PendingDecision) => void;
}

function ApprovalsPanelPage({
  query,
  zh,
  setQuery,
  filtered,
  selected,
  setSelectedId,
  busy,
  onRequest,
}: ApprovalsPanelPageProps) {
  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <input
          className={`input ${styles.search ?? ""}`}
          type="search"
          value={query}
          aria-label={zh ? "筛选待决审批" : "Filter pending approvals"}
          placeholder={zh ? "按动作、风险、运行筛选…" : "Filter action, risk or run…"}
          onChange={(event) => {
            setQuery(event.target.value);
          }}
        />
        <Chip>{zh ? "待决" : "Pending"}</Chip>
        <span className="muted">
          {zh
            ? "选中审批后展示该运行的完整审批历史"
            : "Select an approval to view its run's full approval history"}
        </span>
      </div>
      <div className={styles.split}>
        <ApprovalQueue
          approvals={filtered}
          selectedId={selected?.id ?? ""}
          onSelect={setSelectedId}
        />
        {selected !== undefined && (
          <ApprovalDetail approval={selected} busy={busy} onRequest={onRequest} />
        )}
      </div>
      {selected !== undefined && <RunApprovalHistory runId={selected.run_id} />}
    </div>
  );
}

function ApprovalQueue({
  approvals,
  selectedId,
  onSelect,
}: {
  approvals: ApprovalDto[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <PanelSection title={zh ? "待决队列" : "Pending queue"} count={approvals.length}>
      {approvals.length === 0 ? (
        <div data-testid="approvals-empty">
          <EmptyState message={zh ? "没有匹配的待决审批" : "No matching pending approvals"} />
        </div>
      ) : (
        <ul className={styles.list} data-testid="approvals-list">
          {approvals.map((approval) => (
            <li key={approval.id}>
              <button
                type="button"
                className={styles.listButton}
                aria-pressed={selectedId === approval.id}
                onClick={() => {
                  onSelect(approval.id);
                }}
              >
                <strong>{approval.action}</strong>
                <br />
                <Chip tone="warn">{approval.risk}</Chip>{" "}
                <span className="mono">{approval.run_id}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </PanelSection>
  );
}
