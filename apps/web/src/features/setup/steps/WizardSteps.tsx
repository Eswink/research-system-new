import { Icon, type IconName } from "../../../components/Icon";
import { useI18n } from "../../../i18n/useI18n";
import type { TranslationKey } from "../../../i18n/zh";
import type { WizardStep } from "./types";
import styles from "./WizardSteps.module.css";

const STEPS: readonly { id: WizardStep; labelKey: TranslationKey; icon: IconName }[] = [
  { id: "relay", labelKey: "setup.step.relay", icon: "wifi" },
  { id: "test", labelKey: "setup.step.test", icon: "circle-o" },
  { id: "models", labelKey: "setup.step.models", icon: "hex" },
  { id: "done", labelKey: "setup.step.done", icon: "flask" },
];

type PillState = "done" | "active" | "todo";

function pillState(index: number, current: number): PillState {
  if (index < current) {
    return "done";
  }
  return index === current ? "active" : "todo";
}

/** 步骤指示器：已完成步骤显示 check，当前步骤高亮，未来步骤弱化（不承诺可跳转）。 */
export function WizardSteps({ current }: { current: WizardStep }) {
  const { t } = useI18n();
  const currentIndex = STEPS.findIndex((step) => step.id === current);
  return (
    <ol className={styles.stepper} aria-label={t("setup.title")}>
      {STEPS.map((step, index) => (
        <li key={step.id} className={styles.stepItem}>
          <span
            className={styles.pill}
            data-state={pillState(index, currentIndex)}
            aria-current={index === currentIndex ? "step" : undefined}
          >
            <Icon name={index < currentIndex ? "check" : step.icon} size={10} />
            <span>
              {String(index + 1).padStart(2, "0")} · {t(step.labelKey)}
            </span>
          </span>
          {index < STEPS.length - 1 && (
            <span className={styles.connector} data-done={index < currentIndex} aria-hidden />
          )}
        </li>
      ))}
    </ol>
  );
}
