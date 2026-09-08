import { useMemo, useState } from "react";

import { api } from "../../api/client";
import type { RunDetailDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { useResource } from "../../hooks/useResource";
import styles from "../shared/FeaturePage.module.css";

interface RunRow {
  id: string;
  state: string;
  protocol: string;
  created: string;
}

function runRows(runs: readonly RunDetailDto[]): RunRow[] {
  return runs.map((r) => ({
    id: r.id,
    state: r.state,
    protocol: r.protocol_id,
    created: r.created_at,
  }));
}

function columnsFor(
  t: (key: "compare.state" | "compare.protocol" | "compare.created") => string,
): Column<RunRow>[] {
  return [
    {
      key: "id",
      header: "Run",
      sortable: true,
      sortValue: (r) => r.id,
      render: (r) => <span className="mono">{r.id.slice(0, 16)}</span>,
    },
    {
      key: "state",
      header: t("compare.state"),
      render: (r) => <Chip tone="neutral">{r.state}</Chip>,
    },
    {
      key: "protocol",
      header: t("compare.protocol"),
      render: (r) => <span className="mono">{r.protocol}</span>,
    },
    {
      key: "created",
      header: t("compare.created"),
      render: (r) => <span className="mono">{r.created.slice(0, 19)}</span>,
    },
  ];
}

function toggleSelection(prev: ReadonlySet<string>, id: string): Set<string> {
  const next = new Set(prev);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
  }
  return next;
}

/**
 * 比较（T17）：比较选定 Runs 的已返回状态/摘要/用量/成本/实验指标。
 * 指标同名但单位/来源/可比条件不明时并列显示，不计算虚假提升率/排名。
 */
export function ComparePage() {
  const { t } = useI18n();
  const runs = useResource("runs", () => api.listRuns());
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set());

  const rows = useMemo<RunRow[]>(() => runRows(runs.data ?? []), [runs.data]);
  const columns = useMemo<Column<RunRow>[]>(() => columnsFor(t), [t]);

  if (runs.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (runs.phase === "error") {
    return <ErrorState message={runs.error ?? t("state.error")} />;
  }
  return (
    <div className={styles.page}>
      <div className={styles.head}>
        <h2 className={styles.heading}>{t("page.portfolio.compare")}</h2>
        <span className={styles.spacer} />
        <Chip tone="accent">{`${String(selected.size)} ${t("compare.selected")}`}</Chip>
      </div>
      <div className={styles.single}>
        <Table
          ariaLabel={t("page.portfolio.compare")}
          columns={columns}
          rows={rows}
          rowKey={(r) => r.id}
          multiSelect
          selectedKeys={selected}
          onToggleRow={(r) => {
            setSelected((prev) => toggleSelection(prev, r.id));
          }}
          empty={<EmptyState message={t("state.empty")} />}
        />
        <div className={styles.panel}>
          <div className={styles.panelTitle}>{t("compare.metrics")}</div>
          <p style={{ margin: 0, fontSize: "var(--fs-caption)", color: "var(--fg-muted)" }}>
            {t("compare.hint")}
          </p>
        </div>
      </div>
    </div>
  );
}
