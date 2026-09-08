import { GapLayout } from "../shared/GapLayout";
import { pageSupport } from "../../navigation/pageSupport";
import { useI18n } from "../../i18n/useI18n";

/** 调度（T26）：计划任务 + 日历结构；创建/启停/触发禁用。 */
export function SchedulesPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "ops", page: "schedules" });
  return (
    <div data-testid="gap-page-ops-schedules">
      <GapLayout
        title={t("page.ops.schedules")}
        support={support}
        columns={[t("schedules.cron"), t("schedules.target"), t("gap.column.status")]}
        actions={[{ label: t("schedules.create") }]}
        detailTitle={t("schedules.calendar")}
      />
    </div>
  );
}
