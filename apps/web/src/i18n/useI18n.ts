/** 缺 Provider 时回退中文，保证独立渲染的组件仍可测试。 */

import { useContext } from "react";

import { I18nContext, type I18nContextValue } from "./context";
import type { TranslationKey } from "./zh";
import { zh } from "./zh";

const ZH: Partial<Record<TranslationKey, string>> = zh;

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);
  if (context !== null) {
    return context;
  }
  return {
    language: "zh",
    setLanguage: () => undefined,
    t: (key: TranslationKey) => {
      const fallback = ZH[key];
      return fallback ?? key;
    },
  };
}
