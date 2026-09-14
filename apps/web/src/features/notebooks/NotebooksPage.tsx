import { useI18n } from "../../i18n/useI18n";
import { LibraryPage } from "../library/LibraryPage";

/** 笔记（EC-03）：真实库目录（notebook kind）；创建/保存/执行结构仍无 API。 */
export function NotebooksPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <LibraryPage
      kind="notebook"
      title={zh ? "笔记" : "Notebooks"}
      kicker="LIBRARY / NOTEBOOKS"
      description={
        zh
          ? "项目内登记的 notebook 条目（名称/描述/标签）。单元格编辑与执行无 API，不伪造。"
          : [
              "Notebook entries for the active project (name/description/tags). ",
              "Cell editing and execution have no API and are not faked.",
            ].join("")
      }
    />
  );
}
