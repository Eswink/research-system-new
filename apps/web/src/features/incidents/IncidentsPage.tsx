import { GapLayout } from "../shared/GapLayout";
import { pageSupport } from "../../navigation/pageSupport";
import { useI18n } from "../../i18n/useI18n";

/** 事故（T26）：事件处置流程结构；失败 Run 不转换成已登记事故。 */
export function IncidentsPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "ops", page: "incidents" });
  return (
    <div data-testid="gap-page-ops-incidents">
      <GapLayout
        title={t("page.ops.incidents")}
        support={support}
        columns={[t("incidents.severity"), t("incidents.owner"), t("gap.column.status")]}
        actions={[{ label: t("incidents.declare") }]}
        detailTitle={t("incidents.timeline")}
      />
    </div>
  );
}
