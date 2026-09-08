import { api } from "../../api/client";
import type { ExperimentRunDto, ExperimentViewDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { useResource } from "../../hooks/useResource";
import type { PageContext } from "../../navigation/pageContext";
import styles from "../shared/FeaturePage.module.css";

interface ExperimentRow {
  id: string;
  artifacts: number;
  image: string;
  metrics: number;
  reproducible: boolean;
}

function experimentRows(list: readonly ExperimentRunDto[]): ExperimentRow[] {
  return list.map((e) => ({
    id: e.experiment_run_id,
    artifacts: e.artifact_ids.length,
    image: (e.image_digest ?? "").slice(0, 16),
    metrics: Object.keys(e.metrics).length,
    reproducible: e.reproduction_available,
  }));
}

function columnsFor(
  t: (key: "exp.artifacts" | "exp.image" | "exp.metrics" | "exp.repro") => string,
): Column<ExperimentRow>[] {
  return [
    {
      key: "id",
      header: "Experiment",
      render: (r) => <span className="mono">{r.id.slice(0, 20)}</span>,
    },
    {
      key: "artifacts",
      header: t("exp.artifacts"),
      align: "right",
      render: (r) => String(r.artifacts),
    },
    {
      key: "image",
      header: t("exp.image"),
      render: (r) => <span className="mono">{r.image || "—"}</span>,
    },
    {
      key: "metrics",
      header: t("exp.metrics"),
      align: "right",
      render: (r) => String(r.metrics),
    },
    {
      key: "repro",
      header: t("exp.repro"),
      render: (r) => (
        <Chip tone={r.reproducible ? "success" : "warn"}>{r.reproducible ? "✓" : "✗"}</Chip>
      ),
    },
  ];
}

function ReproNote({ note }: { note: string | undefined }) {
  const { t } = useI18n();
  if (note === undefined) {
    return null;
  }
  return (
    <div className={styles.panel}>
      <div className={styles.panelTitle}>{t("exp.reproNote")}</div>
      <p style={{ margin: 0, fontSize: "var(--fs-caption)", color: "var(--fg-muted)" }}>{note}</p>
    </div>
  );
}

/**
 * 实验（T20）：Run 级实验列表 + 已有指标 + Artifact/镜像/环境摘要 + 复现可用性。
 * 明确当前 Run 范围；reproduction_available 恒 false 如实呈现；创建/排队/日历禁用。
 */
export function ExperimentsPage({ ctx }: { ctx: PageContext }) {
  const { t } = useI18n();
  const runId = ctx.selectedRunId;
  const data = useResource(runId === "" ? null : runId, () => api.runExperiments(runId));

  if (runId === "") {
    return (
      <div className={styles.page}>
        <h2 className={styles.heading}>{t("page.portfolio.experiments")}</h2>
        <EmptyState message={t("overview.noRun")} />
      </div>
    );
  }
  if (data.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (data.phase === "error") {
    return <ErrorState message={data.error ?? t("state.error")} />;
  }
  const view: ExperimentViewDto | null = data.data;
  return (
    <div className={styles.page}>
      <div className={styles.head}>
        <h2 className={styles.heading}>{t("page.portfolio.experiments")}</h2>
        <Chip tone="accent">{`${t("run.context.label")}: ${runId.slice(0, 12)}`}</Chip>
      </div>
      <Table
        ariaLabel={t("page.portfolio.experiments")}
        columns={columnsFor(t)}
        rows={experimentRows(view?.experiments ?? [])}
        rowKey={(r) => r.id}
        empty={<EmptyState message={t("state.empty")} />}
      />
      <ReproNote note={view?.reproduction_note} />
    </div>
  );
}
