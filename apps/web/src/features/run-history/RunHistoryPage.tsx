import { api } from "../../api/client";
import { Chip } from "../../components/Chip";
import { Table, type Column } from "../../components/Table";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { RunDetailDto } from "../../api/types";
import type { PageContext } from "../../navigation/pageContext";
import styles from "../shared/FeaturePage.module.css";

function columnsFor(t: (k: never) => string): Column<RunDetailDto>[] {
  return [
    {
      key: "id",
      header: "Run",
      sortable: true,
      sortValue: (r) => r.id,
      render: (r) => <span className="mono">{r.id.slice(0, 18)}</span>,
    },
    {
      key: "state",
      header: t("compare.state" as never),
      render: (r) => <Chip tone="neutral">{r.state}</Chip>,
    },
    {
      key: "protocol",
      header: t("compare.protocol" as never),
      render: (r) => <span className="mono">{r.protocol_id}</span>,
    },
    {
      key: "created",
      header: t("compare.created" as never),
      render: (r) => <span className="mono">{r.created_at.slice(0, 19)}</span>,
    },
  ];
}

/** 运行历史（T17）：真实列表筛选/选择/详情跳转/刷新恢复；筛选注明作用于已加载范围。 */
export function RunHistoryPage({ ctx }: { ctx: PageContext }) {
  const { t } = useI18n();
  const runs = useResource("runs-list", () => api.listRuns());
  if (runs.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (runs.phase === "error") {
    return <ErrorState message={runs.error ?? t("state.error")} />;
  }
  return (
    <div className={styles.page} data-testid="run-history">
      <div className={styles.head}>
        <h2 className={styles.heading}>{t("page.portfolio.runs-history")}</h2>
        <Chip tone="neutral">{t("runs.scopeNote")}</Chip>
      </div>
      <Table
        ariaLabel={t("page.portfolio.runs-history")}
        columns={columnsFor(t)}
        rows={runs.data ?? []}
        rowKey={(r) => r.id}
        selectable
        selectedKey={ctx.selectedRunId}
        onSelectRow={(r) => { ctx.onSelectedRunIdChange(r.id); }}
        rowHref={(r) => `#/run/timeline?run=${encodeURIComponent(r.id)}`}
        empty={<EmptyState message={t("state.empty")} />}
      />
    </div>
  );
}
