import { useState } from "react";

import { api } from "../../api/client";
import { problemText } from "../../api/problemText";
import type { ExperimentPlanDto } from "../../api/types";
import { Field } from "../../components/Field";
import { ErrorState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

interface EnqueueDraft {
  planId: string;
  source: string;
  protocolPath: string;
  draftId: string;
  draftRevision: string;
  notBefore: string;
  busy: boolean;
  issue: string | null;
}

const INITIAL: EnqueueDraft = {
  planId: "",
  source: "path",
  protocolPath: "",
  draftId: "",
  draftRevision: "1",
  notBefore: "",
  busy: false,
  issue: null,
};

type Enqueue = EnqueueDraft & {
  update: (patch: Partial<EnqueueDraft>) => void;
  submit: () => Promise<void>;
};

/** 入队表单：选计划 + 协议来源（路径或草稿修订）+ 可选排期；提交走真实 HTTP。 */
export function ExperimentEnqueueForm({
  plans,
  onEnqueued,
}: {
  plans: ExperimentPlanDto[];
  onEnqueued: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const enqueue = useEnqueue(onEnqueued);
  return (
    <div className={styles.toolbar} data-testid="enqueue-form">
      <PlanField enqueue={enqueue} plans={plans} zh={zh} />
      <SourceFields enqueue={enqueue} draftMode={enqueue.source === "draft"} zh={zh} />
      <WhenField enqueue={enqueue} zh={zh} />
      <button
        className="btn sm primary"
        type="button"
        disabled={enqueue.busy}
        onClick={() => {
          void enqueue.submit();
        }}
      >
        {enqueue.busy ? (zh ? "入队中…" : "Enqueueing…") : zh ? "入队" : "Enqueue"}
      </button>
      {enqueue.issue !== null && <ErrorState message={enqueue.issue} />}
    </div>
  );
}

function useEnqueue(onDone: () => void): Enqueue {
  const [state, setState] = useState<EnqueueDraft>(INITIAL);
  const update = (patch: Partial<EnqueueDraft>): void => {
    setState((prev) => ({ ...prev, ...patch }));
  };
  const submit = async (): Promise<void> => {
    if (state.planId === "") {
      update({ issue: "plan required" });
      return;
    }
    update({ busy: true, issue: null });
    try {
      await api.enqueueExperiment(state.planId, enqueuePayload(state));
      update({ protocolPath: "", draftId: "", notBefore: "" });
      onDone();
    } catch (err) {
      update({ issue: problemText(err) });
    } finally {
      update({ busy: false });
    }
  };
  return { ...state, update, submit };
}

function enqueuePayload(state: EnqueueDraft): {
  protocol_path?: string | null;
  draft_id?: string | null;
  draft_revision?: number | null;
  not_before?: string | null;
} {
  const notBefore = state.notBefore === "" ? null : new Date(state.notBefore).toISOString();
  if (state.source === "draft") {
    const revision = Number.parseInt(state.draftRevision, 10);
    return {
      draft_id: state.draftId.trim(),
      draft_revision: Number.isNaN(revision) ? null : revision,
      not_before: notBefore,
    };
  }
  return { protocol_path: state.protocolPath.trim(), not_before: notBefore };
}

function PlanField({
  enqueue,
  plans,
  zh,
}: {
  enqueue: Enqueue;
  plans: ExperimentPlanDto[];
  zh: boolean;
}) {
  return (
    <Field label={zh ? "计划" : "Plan"} htmlFor="queue-plan">
      <select
        id="queue-plan"
        className="input"
        value={enqueue.planId}
        disabled={enqueue.busy}
        onChange={(event) => {
          enqueue.update({ planId: event.target.value });
        }}
      >
        <option value="">{zh ? "选择预注册计划…" : "Select a preregistered plan…"}</option>
        {plans.map((plan) => (
          <option key={plan.id} value={plan.id}>
            {plan.name}
          </option>
        ))}
      </select>
    </Field>
  );
}

function WhenField({ enqueue, zh }: { enqueue: Enqueue; zh: boolean }) {
  return (
    <Field label={zh ? "排期（可选）" : "Not before (optional)"} htmlFor="queue-when">
      <input
        id="queue-when"
        className="input"
        type="datetime-local"
        value={enqueue.notBefore}
        disabled={enqueue.busy}
        onChange={(event) => {
          enqueue.update({ notBefore: event.target.value });
        }}
      />
    </Field>
  );
}

function SourceFields({
  enqueue,
  draftMode,
  zh,
}: {
  enqueue: Enqueue;
  draftMode: boolean;
  zh: boolean;
}) {
  return (
    <>
      <Field label={zh ? "来源" : "Source"} htmlFor="queue-source">
        <select
          id="queue-source"
          className="input"
          value={enqueue.source}
          onChange={(event) => {
            enqueue.update({ source: event.target.value });
          }}
        >
          <option value="path">{zh ? "协议路径" : "Protocol path"}</option>
          <option value="draft">{zh ? "草稿修订" : "Draft revision"}</option>
        </select>
      </Field>
      {draftMode ? (
        <DraftSourceFields enqueue={enqueue} zh={zh} />
      ) : (
        <Field
          label={zh ? "协议路径" : "Protocol path"}
          htmlFor="queue-path"
          hint={zh ? "examples/protocols/ 内（入队即解析）" : "resolved at enqueue time"}
        >
          <input
            id="queue-path"
            className="input"
            value={enqueue.protocolPath}
            disabled={enqueue.busy}
            placeholder="m12_reference_research_v1.yaml"
            onChange={(event) => {
              enqueue.update({ protocolPath: event.target.value });
            }}
          />
        </Field>
      )}
    </>
  );
}

function DraftSourceFields({ enqueue, zh }: { enqueue: Enqueue; zh: boolean }) {
  return (
    <>
      <Field label={zh ? "草稿 ID" : "Draft ID"} htmlFor="queue-draft">
        <input
          id="queue-draft"
          className="input"
          value={enqueue.draftId}
          disabled={enqueue.busy}
          onChange={(event) => {
            enqueue.update({ draftId: event.target.value });
          }}
        />
      </Field>
      <Field label={zh ? "修订号" : "Revision"} htmlFor="queue-revision">
        <input
          id="queue-revision"
          className="input"
          type="number"
          min={1}
          value={enqueue.draftRevision}
          disabled={enqueue.busy}
          onChange={(event) => {
            enqueue.update({ draftRevision: event.target.value });
          }}
        />
      </Field>
    </>
  );
}
