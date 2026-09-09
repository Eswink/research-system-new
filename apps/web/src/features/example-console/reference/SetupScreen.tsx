import * as React from "react";
import { useState } from "react";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import visual from "./SetupScreen.module.css";
import { StepDefaults } from "./StepDefaults";
import { StepModels } from "./StepModels";
import { StepProbe } from "./StepProbe";
import { StepRelay } from "./StepRelay";
import { StepTest } from "./StepTest";

/** Reference: screens/Setup.jsx; EXAMPLE ONLY. */
export const SetupScreen = () => {
  const { t } = useI18n();
  const [step, setStep] = useState(3); // Show probe step to demo the interesting state
  const steps = [
    { id: "relay", label: t("st.step.relay"), icon: "wifi" },
    { id: "test", label: t("st.step.test"), icon: "circle-o" },
    { id: "models", label: t("st.step.models"), icon: "hex" },
    { id: "probe", label: t("st.step.probe"), icon: "flask" },
    { id: "defaults", label: t("st.step.defaults"), icon: "check" },
  ];

  return <SetupSection {...{ t, steps, step, setStep }} />;
};

interface SetupSectionProps {
  t: (key: string, fallback?: string) => string;
  steps: { id: string; label: string; icon: string }[];
  step: number;
  setStep: React.Dispatch<React.SetStateAction<number>>;
}

function SetupSection({ t, steps, step, setStep }: SetupSectionProps) {
  return (
    <div className={visual.grid}>
      <SetupInfoCard t={t} />
      <SetupSection2 {...{ steps, step, setStep, t }} />
    </div>
  );
}

function SetupInfoCard({ t }: Pick<SetupSectionProps, "t">) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.caption}>
        <Icon name="shield" size={10} /> {t("st.kicker")}
      </div>
      <div className={visual.label}>{t("st.title")}</div>
      <div className={visual.label2}>{t("st.desc")}</div>
      <div className={visual.column}>
        <div className={visual.row}>
          <Icon name="check" size={11} className={visual.surface} />
          <div>
            <strong className={visual.surface2}>{t("st.pt1")}</strong> {t("st.pt1b")}{" "}
            <span className="mono">configured / missing</span>.
          </div>
        </div>
        <div className={visual.row2}>
          <Icon name="check" size={11} className={visual.surface3} />
          <div>
            <strong className={visual.surface4}>{t("st.pt2")}</strong> {t("st.pt2b")}
          </div>
        </div>
        <div className={visual.row3}>
          <Icon name="check" size={11} className={visual.surface5} />
          <div>
            <strong className={visual.surface6}>{t("st.pt3")}</strong> {t("st.pt3b")}
          </div>
        </div>
        <div className={visual.indicator} />
        <div className={visual.row4}>
          <Icon name="ban" size={11} className={visual.surface7} />
          <div>
            {t("st.no1")} <em>{t("st.no1b")}</em> {t("st.no1c")}
          </div>
        </div>
        <div className={visual.row5}>
          <Icon name="ban" size={11} className={visual.surface8} />
          <div>
            {t("st.no2")} <em>{t("st.no2b")}</em> {t("st.no2c")}
          </div>
        </div>
      </div>
    </div>
  );
}

interface SetupSection2Props {
  steps: { id: string; label: string; icon: string }[];
  step: number;
  setStep: React.Dispatch<React.SetStateAction<number>>;
  t: (key: string, fallback?: string) => string;
}

function SetupSection2({ steps, step, setStep, t }: SetupSection2Props) {
  return (
    <div className={visual.column2}>
      {/* Step indicator */}
      <SetupSection3 {...{ steps, step, setStep }} />

      {/* Current step body */}
      {step === 0 && <StepRelay />}
      {step === 1 && <StepTest />}
      {step === 2 && <StepModels />}
      {step === 3 && <StepProbe />}
      {step === 4 && <StepDefaults />}

      <div className={visual.row8}>
        <button
          className="btn"
          disabled={step === 0}
          onClick={() => {
            setStep(step - 1);
          }}
        >
          {t("st.back")}
        </button>
        <div className={visual.label3}>
          {t("st.stepN")} {step + 1} {t("st.stepOf")} {steps.length}
        </div>
        <button
          className="btn primary"
          disabled={step === steps.length - 1}
          onClick={() => {
            setStep(step + 1);
          }}
        >
          {t("st.continue")}
        </button>
      </div>
    </div>
  );
}

interface SetupSection3Props {
  steps: { id: string; label: string; icon: string }[];
  step: number;
  setStep: React.Dispatch<React.SetStateAction<number>>;
}

function SetupSection3({ steps, step, setStep }: SetupSection3Props) {
  return (
    <div className={visual.row6}>
      {steps.map((s, i) => (
        <React.Fragment key={s.id}>
          <div
            className={visual.row7}
            style={{
              background: i === step ? "var(--accent-dim)" : "transparent",
              color: i === step ? "var(--accent)" : i < step ? "var(--success)" : "var(--fg-faint)",
              border: `1px solid ${i === step ? "var(--accent-line)" : "transparent"}`,
              cursor: i < step ? "pointer" : "default",
            }}
            onClick={() => {
              if (i <= step) setStep(i);
            }}
          >
            <Icon name={i < step ? "check" : s.icon} size={10} />
            <span>
              {String(i + 1).padStart(2, "0")} · {s.label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div
              className={visual.surface9}
              style={{ background: i < step ? "var(--success)" : "var(--border)" }}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
