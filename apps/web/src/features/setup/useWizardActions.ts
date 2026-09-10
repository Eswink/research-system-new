import { api } from "../../api/client";
import { useI18n } from "../../i18n/useI18n";
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

export interface WizardStrings {
  noModels: string;
  probe: string;
  health: string;
  create: string;
}

interface ProbeInput {
  endpointId: string;
  setters: WizardSetters;
  strings: WizardStrings;
}

async function runProbeStep({ endpointId, setters, strings }: ProbeInput) {
  setters.setBusy(true);
  setters.setError(null);
  try {
    const outcome = await probeFirstModel(endpointId);
    if (outcome.kind === "no-models") {
      setters.setError(strings.noModels);
      setters.setStep("models");
      return;
    }
    // ok=false 不静默等同成功：进入 Done 由 DoneStep 分支渲染失败态
    // （Retry Probe / Finish Anyway），不伪装成功外观。
    setters.setProbeResult(outcome.result);
    setters.setStep("done");
  } catch (err) {
    setters.setError(handleError(err, strings.probe));
  } finally {
    setters.setBusy(false);
  }
}

async function runTest(endpointId: string, setters: WizardSetters, strings: WizardStrings) {
  try {
    setters.setHealth(await api.endpointHealth(endpointId));
  } catch (err) {
    setters.setHealth({
      ok: false,
      error_category: null,
      error_message_redacted: handleError(err, strings.health),
      checked_at: new Date().toISOString(),
    });
  }
}

async function createEndpointStep(
  payload: LlmEndpointCreateDto,
  setters: WizardSetters,
  strings: WizardStrings,
) {
  setters.setBusy(true);
  setters.setError(null);
  try {
    const created = await api.createEndpoint(payload);
    setters.setEndpoint(created.dto);
    setters.setStep("test");
    await runTest(created.dto.id, setters, strings);
  } catch (err) {
    setters.setError(handleError(err, strings.create));
  } finally {
    setters.setBusy(false);
  }
}

/** Wizard 动作：API 调用 + 状态转移（server-state cache）。固定文案 i18n 化。 */
export function useWizardActions(setters: WizardSetters): WizardActions {
  const { t } = useI18n();
  const strings: WizardStrings = {
    noModels: t("setup.err.noModels"),
    probe: t("setup.err.probe"),
    health: t("setup.err.health"),
    create: t("setup.err.create"),
  };
  return {
    createEndpoint: (payload) => createEndpointStep(payload, setters, strings),
    runProbe: (endpointId) => runProbeStep({ endpointId, setters, strings }),
    goToModels: () => {
      setters.setStep("models");
    },
  };
}
