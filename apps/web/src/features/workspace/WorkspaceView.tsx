import { useState, type Dispatch, type SetStateAction } from "react";
import { api } from "../../api/client";
import type { ExperimentRunDto, ExperimentViewDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, UnavailableState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { ExperimentMetadata } from "../experiments/ExperimentMetadata";
import { ArtifactBrowser } from "./ArtifactBrowser";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";
import { useSelectedRun, type RunSelectionProps } from "../shared/useSelectedRun";

/** Artifact IDs identify persisted records; they are not file-content or download URLs. */
export function WorkspaceView(props: RunSelectionProps = {}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const { runId, selectRun } = useSelectedRun(props);
  const view = useResource(runId === "" ? null : runId, () => api.runExperiments(runId));
  return (
    <section className={styles.page} data-testid="workspace-page">
      <PageHeader
        title={zh ? "运行工作区" : "Run workspace"}
        kicker="RUN / WORKSPACE"
        description={
          zh
            ? "已持久化的实验、制品引用与环境指纹；不伪造文件内容或 Diff。"
            : [
                "Persisted experiments, artifact references and environment fingerprints; ",
                "no invented files or diffs.",
              ].join("")
        }
        actions={
          <RunQueryBar
            runId={runId}
            onSelect={(id) => {
              if (id === runId) view.reload();
              else selectRun(id);
            }}
            busy={view.phase === "loading"}
          />
        }
      />
      <ResourceBoundary state={view}>
        {view.data === null ? (
          <EmptyState message={zh ? "选择运行以读取工作区" : "Select a run to inspect"} />
        ) : (
          <ExperimentsBody key={runId} view={view.data} />
        )}
      </ResourceBoundary>
      {runId !== "" && <ArtifactBrowser runId={runId} />}
    </section>
  );
}

function ExperimentsBody({ view }: { view: ExperimentViewDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected =
    view.experiments.find((item) => item.experiment_run_id === selectedId) ?? view.experiments[0];
  return <WorkspaceViewPage {...{ zh, view, selected, setSelectedId }} />;
}

interface WorkspaceViewPageProps {
  zh: boolean;
  view: ExperimentViewDto;
  selected: ExperimentRunDto | undefined;
  setSelectedId: Dispatch<SetStateAction<string | null>>;
}

function WorkspaceViewPage({ zh, view, selected, setSelectedId }: WorkspaceViewPageProps) {
  return (
    <div className={styles.page} data-testid="experiments-view">
      <WorkspaceViewSplit {...{ zh, view, selected, setSelectedId }} />
      <p className={styles.notice}>{view.reproduction_note}</p>
      <UnavailableState
        title={zh ? "文件 Diff 未接入" : "File diff unavailable"}
        reason={
          zh
            ? "产物预览与下载已接入（GET /artifacts/{id}/content）；两个版本间的 Diff 尚无后端接口。"
            : [
                "Artifact preview and download are wired (GET /artifacts/{id}/content); ",
                "cross-version diff has no backend endpoint yet.",
              ].join("")
        }
      />
    </div>
  );
}

interface WorkspaceViewSplitProps {
  zh: boolean;
  view: ExperimentViewDto;
  selected: ExperimentRunDto | undefined;
  setSelectedId: Dispatch<SetStateAction<string | null>>;
}

function WorkspaceViewSplit({ zh, view, selected, setSelectedId }: WorkspaceViewSplitProps) {
  return (
    <div className={styles.split}>
      <PanelSection
        title={zh ? "实验与制品目录" : "Experiments and artifacts"}
        count={view.experiments.length}
      >
        <ul className={styles.list}>
          {view.experiments.map((experiment) => (
            <li key={experiment.experiment_run_id} data-testid="experiment-row">
              <button
                type="button"
                className={styles.listButton}
                aria-pressed={selected?.experiment_run_id === experiment.experiment_run_id}
                onClick={() => {
                  setSelectedId(experiment.experiment_run_id);
                }}
              >
                <span className="mono">{experiment.experiment_run_id}</span>
                <br />
                <Chip>{`${String(experiment.artifact_ids.length)} artifacts`}</Chip>
              </button>
            </li>
          ))}
        </ul>
        {view.experiments.length === 0 && (
          <EmptyState
            message={zh ? "此运行没有实验记录" : "No experiments associated with this run"}
          />
        )}
      </PanelSection>
      {selected === undefined ? (
        <EmptyState message={zh ? "没有可预览的元数据" : "No metadata to inspect"} />
      ) : (
        <ExperimentMetadata experiment={selected} />
      )}
    </div>
  );
}
