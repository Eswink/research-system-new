import { GapLayout } from "../shared/GapLayout";
import { pageSupport } from "../../navigation/pageSupport";
import { useI18n } from "../../i18n/useI18n";

/** 数据集（T25）：目录 + 字段/版本/血缘结构；注册/上传/删除/查询禁用。 */
export function DatasetsPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "library", page: "datasets" });
  return (
    <div data-testid="gap-page-library-datasets">
      <GapLayout
        title={t("page.library.datasets")}
        support={support}
        columns={[t("gap.column.item"), t("datasets.rows"), t("gap.column.status")]}
        actions={[{ label: t("datasets.register") }]}
        detailTitle={t("datasets.schema")}
      />
    </div>
  );
}
