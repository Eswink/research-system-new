import { useState } from "react";

import { api } from "../../api/client";
import { problemText } from "../../api/problemText";
import type { ExperimentPlanDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { Field } from "../../components/Field";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, ErrorState } from "../../components/States";
import { useResource, type ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

type ProjectsView = Awaited<ReturnType<typeof api.projectExperiments>>;

/** 预注册计划与项目级实验视图（WP-E；无队列语义，状态来自域）。 */
export function ExperimentPlanPanel() {
  const { language } = useI18n();
  const zh = language === "zh";
  const view = useResource("project-experiments", () => api.projectExperiments());
  const [plans, setPlans] = useState<ExperimentPlanDto[]>([]);
  return (
    <PanelSection title={zh ? "预注册实验计划" : "Preregistered experiment plans"}>
      <div className={styles.page} data-testid="experiment-plan-panel">
        <PlanCreateForm
        onCreated={(plan) => {
          setPlans((p) => [plan, ...p]);
        }}
        zh={zh}
      />
        {plans.length > 0 && <PlanRows plans={plans} zh={zh} onChanged={setPlans} />}
        <PlanProjectRuns view={view} zh={zh} />
      </div>
    </PanelSection>
  );
}

function PlanProjectRuns({ view, zh }: { view: ResourceState<ProjectsView>; zh: boolean }) {
  const rows = view.data?.experiments ?? [];
  return (
    <ResourceBoundary state={view}>
      {view.phase === "ready" && rows.length === 0 && (
        <EmptyState
          message={
            zh ? "项目内暂无已登记实验（evidence 视图）" : "No experiments in this project yet"
          }
        />
      )}
      {rows.length > 0 && (
        <ul className={styles.list}>
          {rows.map((row) => (
            <ProjectRunRow key={`${row.run_id}:${row.experiment_run_id}`} row={row} />
          ))}
        </ul>
      )}
    </ResourceBoundary>
  );
}

function ProjectRunRow({ row }: { row: ProjectsView["experiments"][number] }) {
  const href = `#/run/timeline?run=${encodeURIComponent(row.run_id)}`;
  return (
    <li className={styles.notice}>
      <span className="mono">{row.experiment_run_id}</span> · run{" "}
      <a href={href}>{row.run_id}</a> · {row.artifact_ids.length} artifacts
    </li>
  );
}

function usePlanCreate(onCreated: (plan: ExperimentPlanDto) => void) {
  const [name, setName] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<string | null>(null);
  const submit = async (): Promise<void> => {
    const trimmed = name.trim();
    if (trimmed.length === 0) {
      setIssue("name required");
      return;
    }
    setBusy(true);
    setIssue(null);
    try {
      const payload = { name: trimmed, hypothesis: hypothesis.trim() || null };
      onCreated(await api.createExperimentPlan(payload));
      setName("");
      setHypothesis("");
    } catch (err) {
      setIssue(problemText(err));
    } finally {
      setBusy(false);
    }
  };
  return { name, setName, hypothesis, setHypothesis, busy, issue, submit };
}

function PlanCreateForm({
  onCreated,
  zh,
}: {
  onCreated: (plan: ExperimentPlanDto) => void;
  zh: boolean;
}) {
  const create = usePlanCreate(onCreated);
  return (
    <div className={styles.toolbar} data-testid="plan-create-form">
      <PlanNameFields create={create} zh={zh} />
      <button
        className="btn sm primary"
        type="button"
        disabled={create.busy}
        onClick={() => {
          void create.submit();
        }}
      >
        {create.busy ? (zh ? "创建中…" : "Creating…") : zh ? "预注册计划" : "Preregister plan"}
      </button>
      {create.issue !== null && <ErrorState message={create.issue} />}
    </div>
  );
}

type PlanCreate = ReturnType<typeof usePlanCreate>;

function PlanNameFields({ create, zh }: { create: PlanCreate; zh: boolean }) {
  const hint = zh
    ? "创建即预注册（PREREGISTERED）；队列/调度无 API，不伪装。SQLite 开发路径返回 503。"
    : "Create = preregister; no queue/schedule API. SQLite dev path returns 503.";
  return (
    <>
      <Field label={zh ? "计划名称" : "Plan name"} htmlFor="plan-name">
        <input
          id="plan-name"
          className="input"
          value={create.name}
          disabled={create.busy}
          onChange={(event) => {
            create.setName(event.target.value);
          }}
        />
      </Field>
      <Field label={zh ? "假设（可选）" : "Hypothesis (optional)"} htmlFor="plan-hypo" hint={hint}>
        <input
          id="plan-hypo"
          className="input"
          value={create.hypothesis}
          disabled={create.busy}
          onChange={(event) => {
            create.setHypothesis(event.target.value);
          }}
        />
      </Field>
    </>
  );
}

function PlanRows({
  plans,
  zh,
  onChanged,
}: {
  plans: ExperimentPlanDto[];
  zh: boolean;
  onChanged: (plans: ExperimentPlanDto[]) => void;
}) {
  const archive = async (plan: ExperimentPlanDto): Promise<void> => {
    try {
      const updated = await api.archiveExperimentPlan(plan.id);
      onChanged(plans.map((item) => (item.id === updated.id ? updated : item)));
    } catch {
      onChanged([...plans]);
    }
  };
  return (
    <ul className={styles.list} data-testid="plan-rows">
      {plans.map((plan) => (
        <li key={plan.id} className={styles.notice}>
          <span className="mono">{plan.id}</span> · {plan.name}{" "}
          <Chip tone={plan.state === "ARCHIVED" ? "neutral" : "accent"}>{plan.state}</Chip>
          {plan.state !== "ARCHIVED" && (
            <button
              className="btn sm ghost"
              type="button"
              onClick={() => {
                void archive(plan);
              }}
            >
              {zh ? "归档" : "Archive"}
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
