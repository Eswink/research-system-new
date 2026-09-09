import { useI18n } from "../../i18n/useI18n";
import { pageSupport } from "../../navigation/pageSupport";
import { GapLayout } from "../shared/GapLayout";

/** 报告（T26）：列表 + 阅读预览 + 编辑抽屉结构；生成/编辑/PDF/发布禁用。 */
export function ReportsPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "insights", page: "reports" });
  return (
    <div data-testid="gap-page-insights-reports">
      <GapLayout
        title={t("page.insights.reports")}
        support={support}
        columns={[t("gap.column.item"), t("reports.run"), t("gap.column.status")]}
        actions={[{ label: t("reports.generate") }]}
        detailTitle={t("reports.preview")}
      />
    </div>
  );
}
