import { RelayStepForm } from "./steps/RelayStepForm";
import { TestStep } from "./steps/TestStep";
import { ModelsStep } from "./steps/ModelsStep";
import { DoneStep } from "./steps/DoneStep";
import { WizardSteps } from "./steps/WizardSteps";
import { useWizardFlow } from "./useWizardFlow";

/**
 * First-run Relay Wizard（END_TO_END_USER_JOURNEY §1）：
 * Relay URL → Credential → Test Endpoint → Discover/Add Model → Probe → Defaults。
 *
 * 密钥纪律：api_key 只在创建请求体内发送一次，之后 UI 只显示
 * credential 安全状态（configured/missing），页面任何状态不保存明文 Key。
 */
export function RelayWizard({ onComplete }: { onComplete: (endpointId: string) => void }) {
  const flow = useWizardFlow();

  const submit = (payload: Parameters<typeof flow.createEndpoint>[0]) => {
    void flow.createEndpoint(payload);
  };

  const probeCurrent = () => {
    if (flow.endpoint !== null) {
      void flow.runProbe(flow.endpoint.id);
    }
  };

  const finish = () => {
    if (flow.endpoint !== null) {
      onComplete(flow.endpoint.id);
    }
  };

  return (
    <section className="wizard" data-testid="relay-wizard">
      <h2>First-run Setup</h2>
      <WizardSteps current={flow.step} />
      {flow.step === "relay" && (
        <RelayStepForm busy={flow.busy} error={flow.error} onSubmit={submit} />
      )}
      {flow.step === "test" && flow.endpoint !== null && (
        <TestStep
          endpoint={flow.endpoint}
          health={flow.health}
          busy={flow.busy}
          onContinue={flow.goToModels}
          onProbe={probeCurrent}
        />
      )}
      {flow.step === "models" && flow.endpoint !== null && (
        <ModelsStep busy={flow.busy} error={flow.error} onProbe={probeCurrent} />
      )}
      {flow.step === "done" && flow.probeResult !== null && flow.endpoint !== null && (
        <DoneStep probe={flow.probeResult} onFinish={finish} />
      )}
    </section>
  );
}