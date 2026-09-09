import type { WizardStep } from "./types";

const STEPS: readonly WizardStep[] = ["relay", "test", "models", "done"];
const LABELS: Record<WizardStep, string> = {
  relay: "Relay",
  test: "Test",
  models: "Models",
  done: "Done",
};

export function WizardSteps({ current }: { current: WizardStep }) {
  return (
    <ol className="wizard-steps">
      {STEPS.map((step) => (
        <li key={step} className={current === step ? "active" : ""}>
          {LABELS[step]}
        </li>
      ))}
    </ol>
  );
}
