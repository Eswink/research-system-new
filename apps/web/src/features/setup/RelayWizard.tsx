import type { ReactNode } from "react";

import type { LlmEndpointCreateDto } from "../../api/types";
import { cx } from "../../components/cx";
import { Icon } from "../../components/Icon";
import { useI18n } from "../../i18n/useI18n";
import visual from "./RelayWizard.module.css";
import { DoneStep } from "./steps/DoneStep";
import { ModelsStep } from "./steps/ModelsStep";
import { RelayStepForm } from "./steps/RelayStepForm";
import { TestStep } from "./steps/TestStep";
import type { WizardStep } from "./steps/types";
import { WizardSteps } from "./steps/WizardSteps";
import type { WizardFlow } from "./useWizardFlow";
import { useWizardFlow } from "./useWizardFlow";

const STEP_ORDER: readonly WizardStep[] = ["relay", "test", "models", "done"];

function InfoPoint({ tone, children }: { tone: "ok" | "no"; children: ReactNode }) {
  return (
    <div className={visual.point}>
      <Icon
        name={tone === "ok" ? "check" : "ban"}
        size={11}
        className={cx(
          visual.pointIcon,
          tone === "ok" ? visual.pointIconOk : visual.pointIconNo,
        )}
      />
      <span>{children}</span>
    </div>
  );
}

/** 信息卡：编排定位 + 密钥/代理/指纹三条纪律 + 两条"我们不做"（移植 reference SetupScreen）。 */
function SetupInfoCard() {
  const { t } = useI18n();
  return (
    <aside className={cx("panel", visual.info)}>
      <div className={visual.kicker}>
        <Icon name="shield" size={10} /> {t("setup.kicker")}
      </div>
      <div className={visual.title}>{t("setup.title")}</div>
      <p className={visual.desc}>{t("setup.desc")}</p>
      <div className={visual.points}>
        <InfoPoint tone="ok">
          <strong className={visual.pointStrong}>{t("setup.pt1")}</strong> {t("setup.pt1b")}{" "}
          <span className="mono">configured / missing</span>.
        </InfoPoint>
        <InfoPoint tone="ok">
          <strong className={visual.pointStrong}>{t("setup.pt2")}</strong> {t("setup.pt2b")}
        </InfoPoint>
        <InfoPoint tone="ok">
          <strong className={visual.pointStrong}>{t("setup.pt3")}</strong> {t("setup.pt3b")}
        </InfoPoint>
        <div className={visual.divider} />
        <InfoPoint tone="no">
          {t("setup.no1")} <em>{t("setup.no1b")}</em> {t("setup.no1c")}
        </InfoPoint>
        <InfoPoint tone="no">
          {t("setup.no2")} <em>{t("setup.no2b")}</em> {t("setup.no2c")}
        </InfoPoint>
      </div>
    </aside>
  );
}

interface WizardBodyProps {
  flow: WizardFlow;
  submit: (payload: LlmEndpointCreateDto) => void;
  onProbe: () => void;
  onFinish: () => void;
}

function WizardBody({ flow, submit, onProbe, onFinish }: WizardBodyProps) {
  return (
    <>
      {flow.step === "relay" && (
        <RelayStepForm busy={flow.busy} error={flow.error} onSubmit={submit} />
      )}
      {flow.step === "test" && flow.endpoint !== null && (
        <TestStep
          endpoint={flow.endpoint}
          health={flow.health}
          busy={flow.busy}
          onContinue={flow.goToModels}
          onProbe={onProbe}
        />
      )}
      {flow.step === "models" && flow.endpoint !== null && (
        <ModelsStep
          endpoint={flow.endpoint}
          busy={flow.busy}
          error={flow.error}
          onProbe={onProbe}
        />
      )}
      {flow.step === "done" && flow.probeResult !== null && flow.endpoint !== null && (
        <DoneStep probe={flow.probeResult} onRetry={flow.goToModels} onFinish={onFinish} />
      )}
    </>
  );
}

/**
 * First-run Relay Wizard（END_TO_END_USER_JOURNEY §1）：
 * Relay URL → Credential → Test Endpoint → Discover/Add Model → Probe。
 *
 * 密钥纪律：api_key 只在创建请求体内发送一次，之后 UI 只显示
 * credential 安全状态（configured/missing），页面任何状态不保存明文 Key。
 */
export function RelayWizard({ onComplete }: { onComplete: (endpointId: string) => void }) {
  const { t } = useI18n();
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

  const stepIndex = STEP_ORDER.indexOf(flow.step);

  return (
    <section className={visual.grid} data-testid="relay-wizard" aria-label={t("setup.title")}>
      <SetupInfoCard />
      <div className={visual.column}>
        <WizardSteps current={flow.step} />
        <WizardBody flow={flow} submit={submit} onProbe={probeCurrent} onFinish={finish} />
        <footer className={visual.footer}>
          <span className={visual.stepCount}>
            {t("setup.stepN")} {stepIndex + 1} {t("setup.stepOf")} {STEP_ORDER.length}
          </span>
        </footer>
      </div>
    </section>
  );
}
