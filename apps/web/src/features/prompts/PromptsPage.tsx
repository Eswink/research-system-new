import { useI18n } from "../../i18n/useI18n";
import { pageSupport } from "../../navigation/pageSupport";
import { GapLayout } from "../shared/GapLayout";

/** 提示词库（T25）：列表 + 编辑/版本/A-B 结构；无后端 API，业务修改禁用。 */
export function PromptsPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "library", page: "prompts" });
  return (
    <div data-testid="gap-page-library-prompts">
      <GapLayout
        title={t("page.library.prompts")}
        support={support}
        columns={[t("gap.column.item"), t("prompts.version"), t("gap.column.status")]}
        actions={[{ label: t("action.create") }]}
        detailTitle={t("prompts.versions")}
      />
    </div>
  );
}
