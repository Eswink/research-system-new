import { useI18n } from "../../i18n/useI18n";
import source from "./data/translations.json";

const dictionaries: Record<string, Record<string, string>> = source;
const local: Record<string, Record<string, string>> = {
  en: { "example.saveDraft": "Save example draft" },
  "zh-CN": { "example.saveDraft": "保存示例草稿" },
};

/** Reference terminology shares the real console language preference, not business state. */
export function useExampleI18n() {
  const { language, setLanguage } = useI18n();
  const lang = language === "en" ? "en" : "zh-CN";
  return {
    lang,
    setLang: (next: string) => {
      setLanguage(next === "en" ? "en" : "zh");
    },
    t: (key: string, fallback?: string): string =>
      local[lang]?.[key] ?? dictionaries[lang]?.[key] ?? dictionaries.en?.[key] ?? fallback ?? key,
  };
}
