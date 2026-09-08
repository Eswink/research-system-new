import { GapLayout } from "../shared/GapLayout";
import { pageSupport } from "../../navigation/pageSupport";
import { useI18n } from "../../i18n/useI18n";

/** 数据健康（T26）：质量指标 + 数据详情布局；无后端质量报告时明确不可用。 */
export function DataHealthPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "ops", page: "data-health" });
  return (
    <div data-testid="gap-page-ops-data-health">
      <GapLayout
        title={t("page.ops.data-health")}
        support={support}
        columns={[t("dataHealth.metric"), t("dataHealth.value"), t("gap.column.status")]}
        detailTitle={t("dataHealth.quality")}
      />
    </div>
  );
}
