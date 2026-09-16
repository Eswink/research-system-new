import { useState } from "react";

import { api } from "../../api/client";
import type { ScheduleJobDto } from "../../api/types";
import { ErrorState } from "../../components/States";
import { InlineSelect, InlineTextInput } from "../../components/InlineFields";
import { useAsyncAction } from "../../hooks/useAsyncAction";
import { intervalError, schedulePageCopy as copy } from "./scheduleCopy";

const DEFAULT_INTERVAL = "60";

/** 表单状态与提交语义（渲染在 `ScheduleCreateForm`，拆开以守函数行数上限）。 */
function useCreateSchedule(jobs: ScheduleJobDto[], zh: boolean, onCreated: () => void) {
  const [name, setName] = useState("");
  const [job, setJob] = useState(jobs[0]?.job ?? "");
  const [interval, setInterval] = useState(DEFAULT_INTERVAL);
  const action = useAsyncAction(onCreated);
  const localError = intervalError(interval, zh);
  const ready = name.trim() !== "" && job !== "" && localError === null;
  const submit = (): void => {
    if (!ready) return;
    const payload = { job, interval_seconds: Number(interval), enabled: true };
    action.run(() => api.createSchedule({ name: name.trim(), ...payload }));
    setName("");
  };
  return { name, setName, job, setJob, interval, setInterval, action, localError, ready, submit };
}

type CreateFormState = ReturnType<typeof useCreateSchedule>;

function CreateFields({
  form,
  zh,
  jobs,
}: {
  form: CreateFormState;
  zh: boolean;
  jobs: ScheduleJobDto[];
}) {
  return (
    <>
      <InlineTextInput
        value={form.name}
        onChange={form.setName}
        placeholder={copy.namePlaceholder(zh)}
        testid="schedule-name-input"
      />
      <InlineSelect
        value={form.job}
        onChange={form.setJob}
        options={jobs.map((item) => item.job)}
        testid="schedule-job-select"
      />
      <InlineTextInput
        value={form.interval}
        onChange={form.setInterval}
        placeholder={copy.intervalPlaceholder(zh)}
        testid="schedule-interval-input"
      />
      <button
        className="btn"
        type="submit"
        disabled={form.action.busy || !form.ready}
        data-testid="schedule-create-submit"
      >
        {copy.create(zh)}
      </button>
    </>
  );
}

function CreateFeedback({ form, zh }: { form: CreateFormState; zh: boolean }) {
  return (
    <>
      <span className="hint" data-testid="schedule-create-hint">
        {copy.createHint(zh)}
      </span>
      {form.localError !== null && (
        <span data-testid="schedule-create-local-error">
          <ErrorState message={form.localError} />
        </span>
      )}
      {form.action.error !== null && (
        <span data-testid="schedule-create-error">
          <ErrorState message={form.action.error} />
        </span>
      )}
    </>
  );
}

/** 登记一条调度定义（POST /ops/schedules）。 */
export function ScheduleCreateForm({
  zh,
  jobs,
  onCreated,
}: {
  zh: boolean;
  jobs: ScheduleJobDto[];
  onCreated: () => void;
}) {
  const form = useCreateSchedule(jobs, zh, onCreated);
  return (
    <form
      className="toolbar"
      data-testid="schedule-create-form"
      onSubmit={(event) => {
        event.preventDefault();
        form.submit();
      }}
    >
      <CreateFields form={form} zh={zh} jobs={jobs} />
      <CreateFeedback form={form} zh={zh} />
    </form>
  );
}
