import { useState } from "react";

import { api } from "../../api/client";
import type { IncidentCandidateDto, IncidentItemDto } from "../../api/types";
import { ErrorState } from "../../components/States";
import styles from "./OpsActions.module.css";
import { InlineSelect, InlineTextInput } from "../../components/InlineFields";
import { useAsyncAction } from "../../hooks/useAsyncAction";

const SEVERITIES = ["CRITICAL", "WARNING", "INFO"] as const;

/** 登记事故：从失败 Run 候选带入 run_id 时可一键声明（G7）。 */
export function DeclareIncidentForm({
  zh,
  onDeclared,
  candidate,
}: {
  zh: boolean;
  onDeclared: () => void;
  candidate?: IncidentCandidateDto | undefined;
}) {
  const [title, setTitle] = useState(candidate !== undefined ? candidate.run_id : "");
  const [severity, setSeverity] = useState("WARNING");
  const action = useAsyncAction(onDeclared);
  const submit = (): void => {
    const trimmed = title.trim();
    if (trimmed === "") return;
    action.run(() =>
      api.declareIncident({ title: trimmed, severity, run_id: candidate?.run_id ?? null }),
    );
    setTitle("");
  };
  return (
    <form
      className="toolbar"
      data-testid="incident-declare"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <InlineTextInput
        value={title}
        onChange={setTitle}
        placeholder={zh ? "事故标题" : "Incident title"}
      />
      <InlineSelect value={severity} onChange={setSeverity} options={SEVERITIES} />
      <button className="btn" type="submit" disabled={action.busy || title.trim() === ""}>
        {zh ? "登记事故" : "Declare"}
      </button>
      {action.error !== null && <ErrorState message={action.error} />}
    </form>
  );
}

/** 候选行的一键登记：把该失败 Run 作为来源 run 显式登记（不自动登记）。 */
export function DeclareCandidateButton({
  candidate,
  zh,
  onDone,
}: {
  candidate: IncidentCandidateDto;
  zh: boolean;
  onDone: () => void;
}) {
  const action = useAsyncAction(onDone);
  return (
    <span className={styles.row}>
      <button
        className="btn sm"
        type="button"
        data-testid="declare-candidate"
        disabled={action.busy}
        onClick={() => {
          action.run(() =>
            api.declareIncident({
              title: candidate.run_id,
              severity: "WARNING",
              run_id: candidate.run_id,
            }),
          );
        }}
      >
        {zh ? "登记为事故" : "Declare"}
      </button>
      {action.error !== null && <ErrorState message={action.error} />}
    </span>
  );
}

/** 处置列：已关闭 → 只显示结论；未关闭 → 指派 + 关闭两个动作。 */
export function IncidentActions({
  incident,
  zh,
  onDone,
}: {
  incident: IncidentItemDto;
  zh: boolean;
  onDone: () => void;
}) {
  if (incident.status === "CLOSED") {
    return (
      <span className="mono" data-testid="incident-closed">
        {incident.resolution ?? (zh ? "已关闭" : "closed")}
      </span>
    );
  }
  return (
    <span className={styles.row} data-testid="incident-actions">
      <AssignControl incidentId={incident.id} zh={zh} onDone={onDone} />
      <CloseControl incidentId={incident.id} zh={zh} onDone={onDone} />
    </span>
  );
}

function AssignControl({
  incidentId,
  zh,
  onDone,
}: {
  incidentId: string;
  zh: boolean;
  onDone: () => void;
}) {
  const [assignee, setAssignee] = useState("");
  const action = useAsyncAction(onDone);
  return (
    <span className={styles.row}>
      <InlineTextInput
        value={assignee}
        onChange={setAssignee}
        placeholder={zh ? "处理人" : "Assignee"}
      />
      <button
        className="btn sm"
        type="button"
        disabled={action.busy || assignee.trim() === ""}
        onClick={() => {
          action.run(() => api.assignIncident(incidentId, { assignee: assignee.trim() }));
          setAssignee("");
        }}
      >
        {zh ? "指派" : "Assign"}
      </button>
      {action.error !== null && <ErrorState message={action.error} />}
    </span>
  );
}

function CloseControl({
  incidentId,
  zh,
  onDone,
}: {
  incidentId: string;
  zh: boolean;
  onDone: () => void;
}) {
  const [resolution, setResolution] = useState("");
  const action = useAsyncAction(onDone);
  return (
    <span className={styles.row}>
      <InlineTextInput
        value={resolution}
        onChange={setResolution}
        placeholder={zh ? "处理结论" : "Resolution"}
      />
      <button
        className="btn sm danger"
        type="button"
        disabled={action.busy || resolution.trim() === ""}
        onClick={() => {
          action.run(() => api.closeIncident(incidentId, { resolution: resolution.trim() }));
          setResolution("");
        }}
      >
        {zh ? "关闭" : "Close"}
      </button>
      {action.error !== null && <ErrorState message={action.error} />}
    </span>
  );
}
