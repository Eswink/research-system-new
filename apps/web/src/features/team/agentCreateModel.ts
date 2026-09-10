/** 新建 Agent 的表单模型与纯校验（与对话框组件解耦，避免循环导入）。 */

import type { AgentCreateDto } from "../../api/types";

export interface CreateState {
  role: string;
  mode: "INHERIT" | "EXPLICIT_MODEL";
  modelId: string;
  contextTokens: string;
  iterations: string;
}

export interface CreateBundle {
  state: CreateState;
  set: (patch: Partial<CreateState>) => void;
  busy: boolean;
  issue: string | null;
  submit: () => Promise<void>;
}

/** 校验并构建 POST 载荷；返回字符串表示校验错误码。 */
export function buildPayload(state: CreateState): AgentCreateDto | string {
  if (state.role.length === 0) return "no-role";
  const payload: AgentCreateDto = {
    role: state.role,
    model_binding:
      state.mode === "INHERIT"
        ? { mode: "INHERIT", value: null }
        : { mode: "EXPLICIT_MODEL", value: state.modelId },
  };
  if (state.mode === "EXPLICIT_MODEL" && state.modelId.length === 0) return "no-model";
  const context = state.contextTokens.trim();
  if (context.length > 0) {
    const value = Number(context);
    if (!Number.isInteger(value) || value <= 0) return "bad-context";
    payload.max_context_tokens = value;
  }
  const iterations = state.iterations.trim();
  if (iterations.length > 0) {
    const value = Number(iterations);
    if (!Number.isInteger(value) || value <= 0) return "bad-iterations";
    payload.max_iterations = value;
  }
  return payload;
}
