import { useCallback, useMemo, type ReactNode } from "react";

import { I18nContext, type I18nContextValue, type Language } from "./context";
import { en } from "./en";
import { zh, type TranslationKey } from "./zh";

export type { I18nContextValue, Language } from "./context";

const DICTS: Record<Language, Partial<Record<TranslationKey, string>>> = { zh, en };

export function I18nProvider({
  language,
  onLanguageChange,
  children,
}: {
  language: Language;
  onLanguageChange: (language: Language) => void;
  children: ReactNode;
}) {
  const t = useCallback(
    (key: TranslationKey): string => {
      const dict = DICTS[language];
      const primary = dict[key];
      if (typeof primary === "string") {
        return primary;
      }
      const fallback = DICTS.zh[key];
      return typeof fallback === "string" ? fallback : key;
    },
    [language],
  );

  const value = useMemo<I18nContextValue>(
    () => ({ language, setLanguage: onLanguageChange, t }),
    [language, onLanguageChange, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
