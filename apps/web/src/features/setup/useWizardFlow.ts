import { useState } from "react";

import type {
  EndpointHealthDto,
  LlmEndpointCreateDto,
  LlmEndpointReadDto,
  ProbeResultDto,
} from "../../api/types";
import type { WizardStep } from "./steps/types";
import { useWizardActions } from "./useWizardActions";

export interface WizardState {
  step: WizardStep;
  endpoint: LlmEndpointReadDto | null;
  health: EndpointHealthDto | null;
  probeResult: ProbeResultDto | null;
  busy: boolean;
  error: string | null;
}

export interface WizardFlow extends WizardState {
  createEndpoint: (payload: LlmEndpointCreateDto) => Promise<void>;
  runProbe: (endpointId: string) => Promise<void>;
  goToModels: () => void;
}

/** Wizard 状态与动作（server-state cache；刷新后从 API 恢复） */
export function useWizardFlow(): WizardFlow {
  const [step, setStep] = useState<WizardStep>("relay");
  const [endpoint, setEndpoint] = useState<LlmEndpointReadDto | null>(null);
  const [health, setHealth] = useState<EndpointHealthDto | null>(null);
  const [probeResult, setProbeResult] = useState<ProbeResultDto | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const actions = useWizardActions({
    setEndpoint,
    setHealth,
    setProbeResult,
    setBusy,
    setError,
    setStep,
  });

  return {
    step,
    endpoint,
    health,
    probeResult,
    busy,
    error,
    createEndpoint: actions.createEndpoint,
    runProbe: actions.runProbe,
    goToModels: actions.goToModels,
  };
}
