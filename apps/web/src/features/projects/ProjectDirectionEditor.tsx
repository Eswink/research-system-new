/**
 * 研究方向编辑面（GOAL-20261103-104 EC-03）。
 *
 * **它补的一格**：`PUT /projects/{id}/direction` 是专用写面（GOAL-20261019-089 EC-02），
 * `ProjectDirectionUpdateDto` 早在 `types.ts` 里，但前端没有消费者 —— 用户能在建项目时
 * 填方向，却**改不了**它。
 *
 * 语义照抄后端：**空串 = 清除**（发 `null`），不是「设成空字符串」。这个区别在域里是
 * 有意义的（`direction: null` = 未声明），所以 UI 把它说清楚，而不是静默归一。
 */

import { useState, type FormEvent } from "react";

import { api } from "../../api/client";
import type { ProjectDto } from "../../api/types";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

/** 把界面上的「空输入」翻译成域语义（`null` = 清除），只做一次。 */
function toPayload(raw: string): { direction: string | null } {
  const trimmed = raw.trim();
  return { direction: trimmed === "" ? null : trimmed };
}

function useSaveDirection(project: ProjectDto, onChanged: () => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const save = (raw: string): void => {
    if (busy) return;
    setBusy(true);
    setError(null);
    void api
      .setProjectDirection(project.id, toPayload(raw))
      .then(() => {
        onChanged();
      })
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : String(cause));
      })
      .finally(() => {
        setBusy(false);
      });
  };
  return { busy, error, save };
}

/** 输入框 + 保存按钮（拆出来是为了守住 50 行函数门，不是为复用）。 */
function DirectionFields({
  projectId,
  value,
  busy,
  dirty,
  zh,
  onChange,
}: {
  projectId: string;
  value: string;
  busy: boolean;
  dirty: boolean;
  zh: boolean;
  onChange: (next: string) => void;
}) {
  return (
    <>
      <input
        id={`direction-input-${projectId}`}
        className="input"
        value={value}
        placeholder={zh ? "留空 = 清除方向" : "Empty = clear the direction"}
        disabled={busy}
        data-testid={`project-direction-input-${projectId}`}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      />
      <button
        type="submit"
        className="btn sm"
        disabled={busy || !dirty}
        data-testid={`project-direction-save-${projectId}`}
      >
        {busy ? (zh ? "保存中…" : "Saving…") : zh ? "保存方向" : "Save direction"}
      </button>
    </>
  );
}

export function ProjectDirectionEditor({
  project,
  onChanged,
}: {
  project: ProjectDto;
  onChanged: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const current = project.direction ?? "";
  const [value, setValue] = useState(current);
  const { busy, error, save } = useSaveDirection(project, onChanged);
  const dirty = value.trim() !== current;
  const submit = (event: FormEvent): void => {
    event.preventDefault();
    // 没改就不发请求：写面会产生版本与审计事实，不该为「保持不变」付这笔账。
    if (dirty) save(value);
  };
  return (
    <form
      className={styles.toolbar}
      onSubmit={submit}
      data-testid={`project-direction-${project.id}`}
    >
      <label className="mono" htmlFor={`direction-input-${project.id}`}>
        {zh ? "研究方向" : "Research direction"}
      </label>
      <DirectionFields
        projectId={project.id}
        value={value}
        busy={busy}
        dirty={dirty}
        zh={zh}
        onChange={setValue}
      />
      {error === null ? null : (
        <span className={styles.notice} role="alert">
          {error}
        </span>
      )}
    </form>
  );
}
