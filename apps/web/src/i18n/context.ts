/** i18n context（I18nProvider 与 useI18n 共享；类型自包含，避免循环依赖）。 */

import { createContext } from "react";

import type { TranslationKey } from "./zh";

export type Language = "zh" | "en";

export interface I18nContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: TranslationKey) => string;
}

export const I18nContext = createContext<I18nContextValue | null>(null);
