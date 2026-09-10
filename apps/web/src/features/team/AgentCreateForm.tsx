import { useState } from "react";

import type { ModelReadDto, RoleDefinitionDto } from "../../api/types";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ErrorState } from "../../components/States";
import styles from "../shared/LivePage.module.css";
import type { CreateBundle } from "./agentCreateModel";

const ISSUE_TEXT: Record<string, { zh: string; en: string }> = {
  "no-role": {
    zh: "必须选择 Role（Role 定义职责，不绑定模型）",
    en: "A role must be selected (roles define duties, not models)",
  },
  "no-model": {
    zh: "EXPLICIT_MODEL 需要选择已注册模型",
    en: "EXPLICIT_MODEL requires a registered model",
  },
  "bad-context": {
    zh: "上下文预算必须为正整数",
    en: "Context budget must be a positive integer",
  },
  "bad-iterations": {
    zh: "迭代上限必须为正整数",
    en: "Iteration limit must be a positive integer",
  },
};

function CreateIssue({ code, zh }: { code: string; zh: boolean }) {
  const text = ISSUE_TEXT[code];
  return <ErrorState message={text === undefined ? code : zh ? text.zh : text.en} />;
}

export function AgentCreateForm({
  create,
  roles,
  models,
  zh,
}: {
  create: CreateBundle;
  roles: RoleDefinitionDto[] | null;
  models: ModelReadDto[] | null;
  zh: boolean;
}) {
  const [confirm, setConfirm] = useState(false);
  const { state, set } = create;
  return (
    <div className={styles.page} data-testid="agent-create-form">
      <RoleSelect {...{ state, set, roles, busy: create.busy, zh }} />
      <AgentCreateBinding {...{ state, set, models, zh, busy: create.busy }} />
      <AgentCreateLimits {...{ state, set, busy: create.busy, zh }} />
      {create.issue !== null && <CreateIssue code={create.issue} zh={zh} />}
      <button
        className="btn primary"
        type="button"
        disabled={create.busy || roles === null}
        onClick={() => {
          setConfirm(true);
        }}
      >
        {zh ? "创建 Agent…" : "Create agent…"}
      </button>
      <AgentCreateConfirm {...{ confirm, setConfirm, create, zh }} />
    </div>
  );
}

function RoleSelect({
  state,
  set,
  roles,
  busy,
  zh,
}: {
  state: CreateBundle["state"];
  set: CreateBundle["set"];
  roles: RoleDefinitionDto[] | null;
  busy: boolean;
  zh: boolean;
}) {
  return (
    <label className={styles.queryLabel}>
      Role
      <select
        className="input mono"
        value={state.role}
        disabled={roles === null || busy}
        onChange={(event) => {
          set({ role: event.target.value });
        }}
      >
        <option value="">{zh ? "选择职责定义…" : "Select role…"}</option>
        {(roles ?? []).map((role) => (
          <option key={role.id} value={role.id}>
            {role.id} · {role.category}
          </option>
        ))}
      </select>
    </label>
  );
}

function AgentCreateLimits({
  state,
  set,
  busy,
  zh,
}: {
  state: CreateBundle["state"];
  set: CreateBundle["set"];
  busy: boolean;
  zh: boolean;
}) {
  return (
    <div className={styles.toolbar}>
      <label className={styles.queryLabel}>
        {zh ? "上下文预算（可选）" : "Context budget (optional)"}
        <input
          className="input"
          type="number"
          min={1}
          value={state.contextTokens}
          disabled={busy}
          onChange={(event) => {
            set({ contextTokens: event.target.value });
          }}
        />
      </label>
      <label className={styles.queryLabel}>
        {zh ? "迭代上限（可选）" : "Max iterations (optional)"}
        <input
          className="input"
          type="number"
          min={1}
          value={state.iterations}
          disabled={busy}
          onChange={(event) => {
            set({ iterations: event.target.value });
          }}
        />
      </label>
    </div>
  );
}

function AgentCreateBinding({
  state,
  set,
  models,
  zh,
  busy,
}: {
  state: CreateBundle["state"];
  set: CreateBundle["set"];
  models: ModelReadDto[] | null;
  zh: boolean;
  busy: boolean;
}) {
  return (
    <div className={styles.toolbar}>
      <BindingMode {...{ state, set, busy, zh }} />
      {state.mode === "EXPLICIT_MODEL" && (
        <label className={styles.queryLabel}>
          {zh ? "模型" : "Model"}
          <select
            className="input mono"
            value={state.modelId}
            disabled={models === null || busy}
            onChange={(event) => {
              set({ modelId: event.target.value });
            }}
          >
            <option value="">{zh ? "选择已注册模型" : "Select registered model"}</option>
            {(models ?? []).map((model) => (
              <option key={model.id} value={model.id} disabled={!model.enabled}>
                {model.model_name} · {model.id}
              </option>
            ))}
          </select>
        </label>
      )}
    </div>
  );
}

function BindingMode({
  state,
  set,
  busy,
  zh,
}: {
  state: CreateBundle["state"];
  set: CreateBundle["set"];
  busy: boolean;
  zh: boolean;
}) {
  return (
    <label className={styles.queryLabel}>
      {zh ? "模型绑定" : "Model binding"}
      <select
        className="input"
        value={state.mode}
        disabled={busy}
        onChange={(event) => {
          set({ mode: event.target.value === "EXPLICIT_MODEL" ? "EXPLICIT_MODEL" : "INHERIT" });
        }}
      >
        <option value="INHERIT">INHERIT</option>
        <option value="EXPLICIT_MODEL">EXPLICIT_MODEL</option>
      </select>
    </label>
  );
}

function AgentCreateConfirm({
  confirm,
  setConfirm,
  create,
  zh,
}: {
  confirm: boolean;
  setConfirm: (value: boolean) => void;
  create: CreateBundle;
  zh: boolean;
}) {
  const consequence = zh
    ? "新实例立即持久化到项目 AgentStore；不影响已冻结的运行。"
    : "The new instance persists to the project agent store immediately; " +
      "frozen runs are unaffected.";
  return (
    <ConfirmDialog
      open={confirm}
      busy={create.busy}
      title={zh ? "确认创建 Agent 实例" : "Confirm agent creation"}
      consequence={<p>{consequence}</p>}
      confirmLabel={zh ? "创建" : "Create"}
      cancelLabel={zh ? "取消" : "Cancel"}
      onCancel={() => {
        setConfirm(false);
      }}
      onConfirm={() => {
        void create.submit().then(() => {
          setConfirm(false);
        });
      }}
    />
  );
}
