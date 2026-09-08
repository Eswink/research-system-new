import { GapLayout } from "../shared/GapLayout";
import { pageSupport } from "../../navigation/pageSupport";
import { useI18n } from "../../i18n/useI18n";

/** 项目集（T24）：列表/看板/卡片 + 详情结构；诚实限制为当前单项目上下文。 */
export function ProjectsPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "portfolio", page: "projects" });
  return (
    <div data-testid="gap-page-portfolio-projects">
      <GapLayout
        title={t("page.portfolio.projects")}
        support={support}
        columns={[t("projects.name"), t("projects.lifecycle"), t("gap.column.status")]}
        actions={[{ label: t("action.create") }]}
        detailTitle={t("projects.detail")}
      />
    </div>
  );
}
