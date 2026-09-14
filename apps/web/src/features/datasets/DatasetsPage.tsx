import { useI18n } from "../../i18n/useI18n";
import { LibraryPage } from "../library/LibraryPage";

/** 数据集（EC-03）：真实库目录（dataset kind）；上传/字段 schema 结构仍无 API。
 *  评测输入由 eval spec 承载，本页只登记目录引用，不与其耦合。 */
export function DatasetsPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <LibraryPage
      kind="dataset"
      title={zh ? "数据集" : "Datasets"}
      kicker="LIBRARY / DATASETS"
      description={
        zh
          ? "项目内登记的数据集引用（名称/描述/标签/内容引用）。上传与字段 schema 无 API；评测输入仍由 eval spec 承载。"
          : [
              "Dataset references for the active project (name/description/tags/content ref). ",
              "Upload and column schema have no API; evaluation inputs remain eval-spec owned.",
            ].join("")
      }
    />
  );
}
