import { api } from "../../api/client";
import type {
  EndpointHealthDto,
  LlmEndpointCreateDto,
  LlmEndpointReadDto,
  ProbeResultDto,
} from "../../api/types";
import type { WizardStep } from "./steps/types";

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

  const runProbe = async (endpointId: string) => {
    setters.setBusy(true);
    setters.setError(null);
    try {
      const models = await api.listModels(endpointId);
      if (models.length === 0) {
        throw new Error("no model configured on this endpoint; add one first");
      }
      const result = await api.probeModel(models[0]?.id ?? "");
      setters.setProbeResult(result);
      setters.setStep("done");
    } catch (err) {
      setters.setError(handleError(err, "probe failed"));
    } finally {
      setters.setBusy(false);
    }
  };

  const goToModels = () => {
    setters.setStep("models");
  };

  return { createEndpoint, runProbe, goToModels };
}