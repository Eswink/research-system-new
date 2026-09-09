import { useState, type Dispatch, type SetStateAction } from "react";
import { api } from "../../api/client";
import type { RunDetailDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { Drawer } from "../../components/Drawer";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

export function RunHistoryPage({ ctx }: { ctx: PageContext }) {
  const { language, t } = useI18n();
  const runs = useResource("runs-list", () => api.listRuns());
  return (
    <section className={styles.page} data-testid="run-history">
      <PageHeader
        title={t("page.portfolio.runs-history")}
        kicker="PORTFOLIO / RUN HISTORY"
        description={
          language === "zh"
            ? "筛选只作用于已返回的运行集合；选择会保留 Run 上下文，详情可进入正式时间线。"
            : [
                "Filters apply only to returned runs. Selection preserves run context; ",
                "details open the persisted timeline.",
              ].join("")
        }
        actions={
          <button
            type="button"
            className="btn"
            onClick={runs.reload}
            disabled={runs.phase === "loading"}
          >
            {language === "zh" ? "刷新运行" : "Refresh runs"}
          </button>
        }
      />
      <ResourceBoundary state={runs}>
        {runs.data !== null && <RunHistoryList runs={runs.data} ctx={ctx} />}
      </ResourceBoundary>
    </section>
  );
}

function RunHistoryList({ runs, ctx }: { runs: RunDetailDto[]; ctx: PageContext }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("ALL");
  const [detailId, setDetailId] = useState<string | null>(null);
  const details = runs.find((run) => run.id === detailId);
  const filtered = runs.filter(
    (run) =>
      (status === "ALL" || run.state === status) &&
      `${run.id} ${run.protocol_id} ${run.project_id}`
        .toLocaleLowerCase()
        .includes(query.trim().toLocaleLowerCase()),
  );
  return (
    <RunHistoryPagePage
      {...{ query, zh, setQuery, status, setStatus, runs, filtered, ctx, setDetailId, details }}
    />
  );
}

interface RunHistoryPagePageProps {
  query: string;
  zh: boolean;
  setQuery: Dispatch<SetStateAction<string>>;
  status: string;
  setStatus: Dispatch<SetStateAction<string>>;
  runs: RunDetailDto[];
  filtered: RunDetailDto[];
  ctx: PageContext;
  setDetailId: Dispatch<SetStateAction<string | null>>;
  details: RunDetailDto | undefined;
}

function RunHistoryPagePage({
  query,
  zh,
  setQuery,
  status,
  setStatus,
  runs,
  filtered,
  ctx,
  setDetailId,
  details,
}: RunHistoryPagePageProps) {
  return (
    <div className={styles.page}>
      <RunHistoryPageToolbar {...{ query, zh, setQuery, status, setStatus, runs, filtered }} />
      <Table
        columns={historyColumns(zh)}
        rows={filtered}
        rowKey={(run) => run.id}
        selectable
        selectedKey={ctx.selectedRunId}
        onSelectRow={(run) => {
          ctx.onSelectedRunIdChange(run.id);
          setDetailId(run.id);
        }}
        ariaLabel={zh ? "运行历史" : "Run history"}
        empty={<EmptyState message={zh ? "没有匹配运行" : "No matching runs"} />}
      />
      <Drawer
        open={details !== undefined}
        onClose={() => {
          setDetailId(null);
        }}
        title={zh ? "运行详情" : "Run details"}
      >
        {details !== undefined && <RunHistoryDetails run={details} />}
      </Drawer>
    </div>
  );
}

interface RunHistoryPageToolbarProps {
  query: string;
  zh: boolean;
  setQuery: Dispatch<SetStateAction<string>>;
  status: string;
  setStatus: Dispatch<SetStateAction<string>>;
  runs: RunDetailDto[];
  filtered: RunDetailDto[];
}

function RunHistoryPageToolbar({
  query,
  zh,
  setQuery,
  status,
  setStatus,
  runs,
  filtered,
}: RunHistoryPageToolbarProps) {
  return (
    <div className={styles.toolbar}>
      <input
        className={`input ${styles.search ?? ""}`}
        type="search"
        value={query}
        aria-label={zh ? "搜索运行" : "Search runs"}
        placeholder={zh ? "按运行、协议、项目筛选" : "Filter run, protocol or project"}
        onChange={(event) => {
          setQuery(event.target.value);
        }}
      />
      <select
        className="input"
        value={status}
        aria-label={zh ? "运行状态筛选" : "Run state filter"}
        onChange={(event) => {
          setStatus(event.target.value);
        }}
      >
        <option value="ALL">{zh ? "全部状态" : "All states"}</option>
        {[...new Set(runs.map((run) => run.state))].sort().map((state) => (
          <option key={state}>{state}</option>
        ))}
      </select>
      <Chip>{`${String(filtered.length)} / ${String(runs.length)}`}</Chip>
    </div>
  );
}

function historyColumns(zh: boolean): Column<RunDetailDto>[] {
  return [
    {
      key: "id",
      header: "Run",
      sortable: true,
      sortValue: (run) => run.id,
      render: (run) => (
        <span className="mono" title={run.id}>
          {run.id.slice(0, 20)}
        </span>
      ),
    },
    {
      key: "state",
      header: zh ? "状态" : "State",
      sortable: true,
      sortValue: (run) => run.state,
      render: (run) => <Chip>{run.state}</Chip>,
    },
    { key: "protocol", header: zh ? "协议" : "Protocol", render: (run) => run.protocol_id },
    {
      key: "created",
      header: zh ? "创建时间" : "Created",
      sortable: true,
      sortValue: (run) => run.created_at,
      render: (run) => <time dateTime={run.created_at}>{run.created_at}</time>,
    },
  ];
}

function RunHistoryDetails({ run }: { run: RunDetailDto }) {
  const { language } = useI18n();
  return (
    <div className={styles.page}>
      <KeyValueList
        fields={[
          { label: "Run", value: run.id },
          { label: "Project", value: run.project_id },
          { label: "Protocol", value: run.protocol_id },
          { label: "State", value: run.state },
          { label: "Manifest", value: run.manifest_digest ?? "NOT FROZEN" },
          { label: "Created", value: run.created_at },
          { label: "Updated", value: run.updated_at },
        ]}
      />
      <a className="btn primary" href={`#/run/timeline?run=${encodeURIComponent(run.id)}`}>
        {language === "zh" ? "打开运行时间线" : "Open run timeline"} →
      </a>
    </div>
  );
}
