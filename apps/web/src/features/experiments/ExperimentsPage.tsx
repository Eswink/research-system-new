import { useState, type Dispatch, type SetStateAction } from "react";
import { api } from "../../api/client";
import type { ExperimentRunDto, ExperimentViewDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { Drawer } from "../../components/Drawer";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";
import { ExperimentMetadata } from "./ExperimentMetadata";
import { ExperimentPlanPanel } from "./ExperimentPlanPanel";
import { ExperimentQueuePanel } from "./ExperimentQueuePanel";

export function ExperimentsPage({ ctx }: { ctx: PageContext }) {
  const { language, t } = useI18n();
  const runId = ctx.selectedRunId;
  const resource = useResource(runId === "" ? null : runId, () => api.runExperiments(runId));
  return (
    <section className={styles.page} data-testid="experiments-page">
      <PageHeader
        title={t("page.portfolio.experiments")}
        kicker="PORTFOLIO / EXPERIMENTS"
        description={
          language === "zh"
            ? "当前运行的实验与指标；计划预注册、排队与调度走真实控制面；复现执行与日历/矩阵视图无 API。"
            : [
                "Experiments and metrics for the selected run. Preregistration, queueing and ",
                "scheduling go through the live control plane; reproduction runs and ",
                "calendar/matrix views have no API.",
              ].join("")
        }
        actions={
          <RunQueryBar
            runId={runId}
            onSelect={(id) => {
              if (id === runId) resource.reload();
              else ctx.onSelectedRunIdChange(id);
            }}
            busy={resource.phase === "loading"}
          />
        }
      />
      {runId === "" && <EmptyState message={t("overview.noRun")} />}
      <ResourceBoundary state={resource}>
        {resource.data !== null && <ExperimentCatalog key={runId} view={resource.data} />}
      </ResourceBoundary>
      <ExperimentPlanPanel />
      <ExperimentQueuePanel />
    </section>
  );
}

function ExperimentCatalog({ view }: { view: ExperimentViewDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("list");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = view.experiments.find((item) => item.experiment_run_id === selectedId);
  const filtered = view.experiments.filter((item) =>
    `${item.experiment_run_id} ${item.image_digest ?? ""}`
      .toLocaleLowerCase()
      .includes(query.trim().toLocaleLowerCase()),
  );
  return (
    <div className={styles.page}>
      <ExperimentsPageToolbar {...{ query, zh, setQuery, mode, setMode, filtered }} />
      {mode === "list" ? (
        <Table
          columns={experimentColumns(zh)}
          rows={filtered}
          rowKey={(item) => item.experiment_run_id}
          ariaLabel={zh ? "实验列表" : "Experiments"}
          selectable
          selectedKey={selectedId ?? ""}
          onSelectRow={(item) => {
            setSelectedId(item.experiment_run_id);
          }}
          empty={<EmptyState message={zh ? "没有匹配实验" : "No matching experiments"} />}
        />
      ) : (
        <ExperimentCards experiments={filtered} onSelect={setSelectedId} />
      )}
      <p className={styles.notice}>{view.reproduction_note}</p>
      <Drawer
        open={selected !== undefined}
        onClose={() => {
          setSelectedId(null);
        }}
        title={zh ? "实验详情" : "Experiment details"}
      >
        {selected !== undefined && <ExperimentMetadata experiment={selected} />}
      </Drawer>
    </div>
  );
}

interface ExperimentsPageToolbarProps {
  query: string;
  zh: boolean;
  setQuery: Dispatch<SetStateAction<string>>;
  mode: string;
  setMode: Dispatch<SetStateAction<string>>;
  filtered: ExperimentRunDto[];
}

function ExperimentsPageToolbar({
  query,
  zh,
  setQuery,
  mode,
  setMode,
  filtered,
}: ExperimentsPageToolbarProps) {
  return (
    <div className={styles.toolbar}>
      <input
        type="search"
        className={`input ${styles.search ?? ""}`}
        value={query}
        aria-label={zh ? "搜索实验" : "Search experiments"}
        placeholder={zh ? "按 ID 或镜像筛选" : "Filter ID or image"}
        onChange={(event) => {
          setQuery(event.target.value);
        }}
      />
      <button
        type="button"
        className="btn sm"
        aria-pressed={mode === "list"}
        onClick={() => {
          setMode("list");
        }}
      >
        {zh ? "列表" : "List"}
      </button>
      <button
        type="button"
        className="btn sm"
        aria-pressed={mode === "grid"}
        onClick={() => {
          setMode("grid");
        }}
      >
        {zh ? "网格" : "Grid"}
      </button>
      <Chip>{filtered.length} experiments</Chip>
    </div>
  );
}

function experimentColumns(zh: boolean): Column<ExperimentRunDto>[] {
  return [
    {
      key: "id",
      header: "Experiment",
      sortable: true,
      sortValue: (item) => item.experiment_run_id,
      render: (item) => <span className="mono">{item.experiment_run_id}</span>,
    },
    {
      key: "artifacts",
      header: zh ? "制品引用" : "Artifact references",
      render: (item) => item.artifact_ids.length,
    },
    {
      key: "image",
      header: zh ? "镜像指纹" : "Image digest",
      render: (item) => (
        <span title={item.image_digest ?? ""}>{item.image_digest?.slice(0, 20) ?? "UNKNOWN"}</span>
      ),
    },
    {
      key: "metrics",
      header: zh ? "指标字段" : "Metric fields",
      render: (item) => Object.keys(item.metrics).length,
    },
    {
      key: "reproduction",
      header: zh ? "复现能力（非结果）" : "Reproduction capability (not a result)",
      render: (item) => <Chip>{item.reproduction_available ? "AVAILABLE" : "UNAVAILABLE"}</Chip>,
    },
  ];
}

function ExperimentCards({
  experiments,
  onSelect,
}: {
  experiments: ExperimentRunDto[];
  onSelect: (id: string) => void;
}) {
  const { language } = useI18n();
  if (experiments.length === 0)
    return <EmptyState message={language === "zh" ? "没有匹配实验" : "No matching experiments"} />;
  return (
    <div className={styles.cards}>
      {experiments.map((item) => (
        <article key={item.experiment_run_id} className={styles.card}>
          <h2 className={styles.cardTitle}>{item.experiment_run_id}</h2>
          <p>{item.artifact_ids.length} artifacts</p>
          <Chip>
            {item.reproduction_available ? "REPRODUCTION AVAILABLE" : "REPRODUCTION UNAVAILABLE"}
          </Chip>
          <p className="mono">{item.environment_digest ?? "UNKNOWN ENVIRONMENT"}</p>
          <button
            type="button"
            className="btn sm"
            onClick={() => {
              onSelect(item.experiment_run_id);
            }}
          >
            {language === "zh" ? "检查指标与元数据" : "Inspect metrics and metadata"}
          </button>
        </article>
      ))}
    </div>
  );
}
