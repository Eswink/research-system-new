import { useI18n } from "../../i18n/useI18n";
import { LibraryPage } from "../library/LibraryPage";

/** 提示词库（EC-03）：真实库目录（prompt kind）；版本/A-B 结构仍无 API。 */
export function PromptsPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <LibraryPage
      kind="prompt"
      title={zh ? "提示词库" : "Prompt library"}
      kicker="LIBRARY / PROMPTS"
      description={
        zh
          ? "项目内登记的提示词条目（名称/描述/标签/内容引用）。版本树与 A-B 无 API，不伪造。"
          : [
              "Prompt entries for the active project (name/description/tags/content ref). ",
              "Version trees and A-B testing have no API and are not faked.",
            ].join("")
      }
    />
  );
}
