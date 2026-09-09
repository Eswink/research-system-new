import { useI18n } from "../../i18n/useI18n";
import { pageSupport } from "../../navigation/pageSupport";
import { GapLayout } from "../shared/GapLayout";

/** 告警（T26）：规则 + 收件箱结构；配置与处理禁用。 */
export function AlertsPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "ops", page: "alerts" });
  return (
    <div data-testid="gap-page-ops-alerts">
      <GapLayout
        title={t("page.ops.alerts")}
        support={support}
        columns={[t("alerts.rule"), t("alerts.severity"), t("gap.column.status")]}
        actions={[{ label: t("alerts.newRule") }]}
        detailTitle={t("alerts.inbox")}
      />
    </div>
  );
}
