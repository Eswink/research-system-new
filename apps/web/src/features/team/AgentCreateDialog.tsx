import { useState } from "react";

import { api } from "../../api/client";
import { problemText } from "../../api/problemText";
import type { ModelReadDto, RoleDefinitionDto } from "../../api/types";
import { Drawer } from "../../components/Drawer";
import { useI18n } from "../../i18n/useI18n";
import { AgentCreateForm } from "./AgentCreateForm";
import { buildPayload, type CreateBundle, type CreateState } from "./agentCreateModel";

function useAgentCreate(onCreated: () => void): CreateBundle {
  const [state, setState] = useState<CreateState>({
    role: "",
    mode: "INHERIT",
    modelId: "",
    contextTokens: "",
    iterations: "",
  });
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<string | null>(null);
  const set = (patch: Partial<CreateState>): void => {
    setState((current) => ({ ...current, ...patch }));
  };
  const submit = async (): Promise<void> => {
    const built = buildPayload(state);
    if (typeof built === "string") {
      setIssue(built);
      return;
    }
    setBusy(true);
    setIssue(null);
    try {
      await api.createAgent(built);
      onCreated();
    } catch (err) {
      setIssue(problemText(err, "create failed"));
    } finally {
      setBusy(false);
    }
  };
  return { state, set, busy, issue, submit };
}

/** 新建 Agent 配置实例（POST /projects/{id}/agents；Role/模型引用真实校验）。 */
export function AgentCreateDialog({
  open,
  onClose,
  roles,
  models,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  roles: RoleDefinitionDto[] | null;
  models: ModelReadDto[] | null;
  onCreated: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const create = useAgentCreate(() => {
    onCreated();
    onClose();
  });
  return (
    <Drawer open={open} onClose={onClose} title={zh ? "新建 Agent 实例" : "New agent instance"}>
      <AgentCreateForm create={create} roles={roles} models={models} zh={zh} />
    </Drawer>
  );
}
