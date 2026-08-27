import { api } from "../../api/client";
import type {
  EndpointHealthDto,
  LlmEndpointCreateDto,
  LlmEndpointReadDto,
  ProbeResultDto,
} from "../../api/types";
import type { WizardStep } from "./steps/types";
import { probeFirstModel } from "./wizardApi";

const handleError = (err: unknown, fallback: string): string => {
  return err instanceof Error ? err.message : fallback;
};

export interface WizardActions {
  createEndpoint: (payload: LlmEndpointCreateDto) => Promise<void>;
  runProbe: (endpointId: string) => Promise<void>;
  goToModels: () => void;
}

export interface WizardSetters {
  setEndpoint: (value: LlmEndpointReadDto | null) => void;
  setHealth: (value: EndpointHealthDto | null) => void;
  setProbeResult: (value: ProbeResultDto | null) => void;
  setBusy: (value: boolean) => void;
  setError: (value: string | null) => void;
  setStep: (value: WizardStep) => void;
}

async function runProbeStep(endpointId: string, setters: WizardSetters) {
  setters.setBusy(true);
  setters.setError(null);
  try {
    const outcome = await probeFirstModel(endpointId);
    if (outcome.kind === "no-models") {
      setters.setError("no model configured on this endpoint; add one first");
      setters.setStep("models");
      return;
    }
    // ok=false 不静默等同成功：进入 Done 由 DoneStep 分支渲染失败态
    // （Retry Probe / Finish Anyway），不伪装成功外观。
    setters.setProbeResult(outcome.result);
    setters.setStep("done");
  } catch (err) {
    setters.setError(handleError(err, "probe failed"));
  } finally {
    setters.setBusy(false);
  }
}

/** Wizard 动作：API 调用 + 状态转移（server-state cache） */
export function useWizardActions(setters: WizardSetters): WizardActions {
  const runTest = async (endpointId: string) => {
    try {
      const result = await api.endpointHealth(endpointId);
      setters.setHealth(result);
    } catch (err) {
      setters.setHealth({
        ok: false,
        error_category: null,
        error_message_redacted: handleError(err, "health check failed"),
        checked_at: new Date().toISOString(),
      });
    }
  };

  const createEndpoint = async (payload: LlmEndpointCreateDto) => {
    setters.setBusy(true);
    setters.setError(null);
    try {
      const created = await api.createEndpoint(payload);
      setters.setEndpoint(created.dto);
      setters.setStep("test");
      await runTest(created.dto.id);
    } catch (err) {
      setters.setError(handleError(err, "create failed"));
    } finally {
      setters.setBusy(false);
    }
  };

  const runProbe = (endpointId: string) => runProbeStep(endpointId, setters);

  const goToModels = () => {
    setters.setStep("models");
  };

  return { createEndpoint, runProbe, goToModels };
}
