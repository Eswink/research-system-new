import { api } from "../../api/client";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState, ErrorState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

/** 选中审批所属 run 的历史（GET /runs/{id}/approvals；WP-B 面，含已裁决记录）。 */
export function RunApprovalHistory({ runId }: { runId: string }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const history = useResource(`run-approvals:${runId}`, () => api.runApprovals(runId));
  return (
    <PanelSection
      title={zh ? `运行审批历史 · ${runId}` : `Run approval history · ${runId}`}
      extra={
        <HistoryRefresh zh={zh} busy={history.phase === "loading"} onReload={history.reload} />
      }
    >
      <div data-testid="approval-history">
        {history.error !== null && <ErrorState message={history.error} />}
        {history.data !== null && <HistoryList approvals={history.data} zh={zh} />}
      </div>
    </PanelSection>
  );
}

function HistoryRefresh({
  zh,
  busy,
  onReload,
}: {
  zh: boolean;
  busy: boolean;
  onReload: () => void;
}) {
  return (
    <button
      type="button"
      className="btn sm ghost"
      onClick={onReload}
      disabled={busy}
    >
      {zh ? "刷新" : "Refresh"}
    </button>
  );
}

function HistoryList({
  approvals,
  zh,
}: {
  approvals: Awaited<ReturnType<typeof api.runApprovals>>;
  zh: boolean;
}) {
  if (approvals.length === 0) {
    return <EmptyState message={zh ? "该运行暂无审批记录" : "No approvals for this run"} />;
  }
  return (
    <ul className={styles.list}>
      {approvals.map((item) => (
        <li key={item.id}>
          <strong>{item.action}</strong>{" "}
          <Chip tone={item.status === "PENDING" ? "warn" : "neutral"}>{item.status}</Chip>{" "}
          <span className="mono">{item.id}</span>
        </li>
      ))}
    </ul>
  );
}
