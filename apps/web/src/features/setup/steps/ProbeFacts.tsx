import { cx } from "../../../components/cx";
import { Icon } from "../../../components/Icon";
import { useI18n } from "../../../i18n/useI18n";
import type { ProbeResultDto } from "../../../api/types";
import styles from "./steps.module.css";

function CapList({ caps }: { caps: string[] }) {
  const { t } = useI18n();
  if (caps.length === 0) {
    return <span className={styles.hint}>{t("setup.done.none")}</span>;
  }
  return (
    <>
      {caps.map((cap) => (
        <span key={cap} className={cx("chip", styles.chipOk)}>
          <Icon name="check" size={9} />
          {cap}
        </span>
      ))}
    </>
  );
}

/** probe 事实行：返回模型 / 观测能力 / 可复现性（只声明配置可重复，AGENTS.md §4）。 */
export function ProbeFacts({ probe }: { probe: ProbeResultDto }) {
  const { t } = useI18n();
  return (
    <div className={styles.kv}>
      <div className={styles.kvRow}>
        <span className={styles.kvKey}>{t("setup.done.model")}</span>
        <span className={styles.kvValue}>
          {probe.returned_model_name !== null ? (
            <span className="mono">{probe.returned_model_name}</span>
          ) : (
            <span className={styles.hint}>{t("setup.done.notProvided")}</span>
          )}
        </span>
      </div>
      <div className={styles.kvRow}>
        <span className={styles.kvKey}>{t("setup.done.caps")}</span>
        <span className={styles.kvValue}>
          <CapList caps={probe.observed_capabilities} />
        </span>
      </div>
      <div className={styles.kvRow} data-testid="probe-reproducibility">
        <span className={styles.kvKey}>{t("setup.done.repro")}</span>
        <span className={styles.kvValue}>
          <Icon name="q" size={12} className={styles.hint} />
          {probe.provider_fingerprint_available
            ? t("setup.done.fpAvailable")
            : t("setup.done.fpUnavailable")}
        </span>
      </div>
    </div>
  );
}
