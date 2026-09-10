import { Button } from "../../../components/Button";
import { cx } from "../../../components/cx";
import { StatusBadge } from "../../../components/StatusBadge";
import { useI18n } from "../../../i18n/useI18n";
import type { ProbeResultDto } from "../../../api/types";
import { ErrorRow } from "./ErrorRow";
import { ProbeFacts } from "./ProbeFacts";
import styles from "./steps.module.css";

/**
 * Done 步骤（M13-R1 WP-B2）：probe 失败态如实分支渲染——
 * ok=false 时显示失败 banner（error_category + redacted message），
 * CTA 变为 Retry Probe / Finish Anyway，不伪装成功外观。
 * 可复现性只声明"配置可重复"；供应商指纹不可用时明说（AGENTS.md §4）。
 */
export function DoneStep({
  probe,
  onRetry,
  onFinish,
}: {
  probe: ProbeResultDto;
  onRetry: () => void;
  onFinish: () => void;
}) {
  const { t } = useI18n();
  const failed = !probe.ok;
  return (
    <div className={cx("panel", styles.panel)} data-testid="wizard-done">
      <div className={styles.head}>
        <div className={styles.title}>{t("setup.done.title")}</div>
        <StatusBadge
          tone={failed ? "danger" : "success"}
          label={failed ? t("setup.done.failed") : t("setup.done.passed")}
        />
      </div>
      {failed && (
        <ErrorRow
          testid="probe-failure"
          message={t("setup.done.failed")}
          detail={`${probe.error_category ?? "unknown category"} · ${
            probe.error_message_redacted ?? t("setup.done.none")
          }`}
        />
      )}
      <ProbeFacts probe={probe} />
      <div className={styles.actions}>
        {failed ? (
          <>
            <Button icon="spin" onClick={onRetry}>
              {t("setup.done.retry")}
            </Button>
            <Button variant="danger" onClick={onFinish}>
              {t("setup.done.finishAnyway")}
            </Button>
          </>
        ) : (
          <Button variant="primary" icon="check" onClick={onFinish}>
            {t("setup.done.finish")}
          </Button>
        )}
      </div>
    </div>
  );
}
