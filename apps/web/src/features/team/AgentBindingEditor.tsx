import { useState, type Dispatch, type SetStateAction } from "react";
import { api } from "../../api/client";
import type { AgentSpecDto, ModelReadDto } from "../../api/types";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ErrorState } from "../../components/States";
import { useCommand } from "../../hooks/useCommand";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import { bindingDescription, editedModelBinding, type EditableBindingMode } from "./modelBinding";

interface AgentBindingEditorProps {
  agent: AgentSpecDto;
  models: ModelReadDto[] | null;
  onSaved: () => void;
}

export function AgentBindingEditor({ agent, models, onSaved }: AgentBindingEditorProps) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [mode, setMode] = useState<EditableBindingMode>(
    agent.model_binding.mode === "EXPLICIT_MODEL" ? "EXPLICIT_MODEL" : "INHERIT",
  );
  const [modelId, setModelId] = useState(agent.model_binding.value ?? "");
  const [confirm, setConfirm] = useState(false);
  const command = useCommand(
    async () =>
      api.updateAgent(
        agent.id,
        { model_binding: editedModelBinding(mode, modelId) },
        agent.version,
      ),
    onSaved,
  );
  const valid =
    mode === "INHERIT" || models?.some((model) => model.id === modelId && model.enabled) === true;
  return (
    <div className={styles.page}>
      <AgentBindingSummary agent={agent} zh={zh} />
      <BindingFields
        mode={mode}
        setMode={setMode}
        modelId={modelId}
        setModelId={setModelId}
        models={models ?? []}
        disabled={models === null || command.pending}
      />
      {command.error !== null && <ErrorState message={command.error} />}
      <AgentBindingSaveButton
        disabled={!valid || models === null || command.pending}
        zh={zh}
        setConfirm={setConfirm}
      />
      <AgentBindingEditorConfirmDialog
        {...{ confirm, command, zh, agent, mode, modelId, setConfirm }}
      />
    </div>
  );
}

function AgentBindingSaveButton({
  disabled,
  zh,
  setConfirm,
}: {
  disabled: boolean;
  zh: boolean;
  setConfirm: Dispatch<SetStateAction<boolean>>;
}) {
  return (
    <button
      type="button"
      className="btn primary"
      disabled={disabled}
      onClick={() => {
        setConfirm(true);
      }}
    >
      {zh ? "保存绑定…" : "Save binding…"}
    </button>
  );
}

function AgentBindingSummary({ agent, zh }: { agent: AgentSpecDto; zh: boolean }) {
  return (
    <>
      <AgentMetadata agent={agent} />
      <p className={styles.notice} data-testid="binding-display">
        {zh ? "当前正式绑定：" : "Persisted binding: "}
        {bindingDescription(agent.model_binding)}
      </p>
    </>
  );
}

interface AgentBindingEditorConfirmDialogProps {
  confirm: boolean;
  command: {
    run: (argument: unknown) => Promise<void>;
    pending: boolean;
    result: AgentSpecDto | null;
    error: string | null;
  };
  zh: boolean;
  agent: AgentSpecDto;
  mode: string;
  modelId: string;
  setConfirm: Dispatch<SetStateAction<boolean>>;
}

function AgentBindingEditorConfirmDialog({
  confirm,
  command,
  zh,
  agent,
  mode,
  modelId,
  setConfirm,
}: AgentBindingEditorConfirmDialogProps) {
  return (
    <ConfirmDialog
      open={confirm}
      busy={command.pending}
      title={zh ? "确认更新 Agent 模型绑定" : "Confirm agent binding change"}
      consequence={
        <p>
          {agent.id} · {bindingDescription({ mode, value: mode === "INHERIT" ? null : modelId })}
          <br />
          {zh
            ? "仅修改配置，不改写已冻结的运行。保存使用当前 ETag；版本冲突不自动重试。"
            : [
                "Updates configuration, not frozen runs. The displayed ETag is submitted; ",
                "conflicts are never retried automatically.",
              ].join("")}
        </p>
      }
      confirmLabel={zh ? "确认保存" : "Save binding"}
      cancelLabel={zh ? "取消" : "Cancel"}
      onCancel={() => {
        setConfirm(false);
      }}
      onConfirm={() => {
        void command.run(undefined);
      }}
    />
  );
}

function BindingFields({
  mode,
  setMode,
  modelId,
  setModelId,
  models,
  disabled,
}: {
  mode: EditableBindingMode;
  setMode: (mode: EditableBindingMode) => void;
  modelId: string;
  setModelId: (id: string) => void;
  models: ModelReadDto[];
  disabled: boolean;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <AgentBindingEditorPage {...{ zh, mode, disabled, setMode, modelId, setModelId, models }} />
  );
}

interface AgentBindingEditorPageProps {
  zh: boolean;
  mode: string;
  disabled: boolean;
  setMode: (mode: EditableBindingMode) => void;
  modelId: string;
  setModelId: (id: string) => void;
  models: ModelReadDto[];
}

function AgentBindingEditorPage({
  zh,
  mode,
  disabled,
  setMode,
  modelId,
  setModelId,
  models,
}: AgentBindingEditorPageProps) {
  return (
    <div className={styles.page}>
      <label className={styles.queryLabel}>
        {zh ? "新的绑定方式" : "New binding mode"}
        <select
          className="input"
          value={mode}
          disabled={disabled}
          onChange={(event) => {
            setMode(event.target.value === "INHERIT" ? "INHERIT" : "EXPLICIT_MODEL");
          }}
        >
          <option value="INHERIT">INHERIT</option>
          <option value="EXPLICIT_MODEL">EXPLICIT_MODEL</option>
        </select>
      </label>
      {mode === "EXPLICIT_MODEL" && (
        <label className={styles.queryLabel}>
          {zh ? "模型" : "Model"}
          <select
            className="input"
            value={modelId}
            disabled={disabled}
            onChange={(event) => {
              setModelId(event.target.value);
            }}
          >
            <option value="">{zh ? "选择已注册模型" : "Select registered model"}</option>
            {models.map((model) => (
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

function AgentMetadata({ agent }: { agent: AgentSpecDto }) {
  return (
    <KeyValueList
      fields={[
        { label: "Agent", value: agent.id },
        { label: "Role", value: agent.role },
        { label: "ETag", value: agent.version },
        { label: "Runtime", value: agent.runtime_kind ?? "INHERIT" },
        { label: "Workspace", value: agent.workspace_policy ?? "INHERIT" },
        { label: "Skills", value: agent.skill_refs.join(", ") || "—" },
        { label: "Capabilities", value: agent.capability_refs.join(", ") || "—" },
        { label: "Context tokens", value: agent.max_context_tokens ?? "INHERIT" },
        { label: "Iterations", value: agent.max_iterations ?? "INHERIT" },
      ]}
    />
  );
}
