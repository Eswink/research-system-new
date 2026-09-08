import { GapLayout } from "../shared/GapLayout";
import { pageSupport } from "../../navigation/pageSupport";
import { useI18n } from "../../i18n/useI18n";

/** 笔记（T25）：列表 + 阅读/编辑布局；创建/保存/执行禁用。 */
export function NotebooksPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "library", page: "notebooks" });
  return (
    <div data-testid="gap-page-library-notebooks">
      <GapLayout
        title={t("page.library.notebooks")}
        support={support}
        columns={[t("gap.column.item"), t("notebooks.updated"), t("gap.column.status")]}
        actions={[{ label: t("action.create") }]}
        detailTitle={t("notebooks.cells")}
      />
    </div>
  );
}
