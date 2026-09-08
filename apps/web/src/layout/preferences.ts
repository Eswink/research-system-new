/**
 * 浏览器持久化偏好（唯一允许的 localStorage 面）：
 * 主题 / 密度 / 语言 / 编辑器模式。业务真相永不入浏览器存储。
 */

export type ThemePreference = "dark" | "light";
export type DensityPreference = "normal" | "compact";
export type LanguagePreference = "zh" | "en";
export type EditorModePreference = "form" | "yaml";

export interface ConsolePreferences {
  theme: ThemePreference;
  density: DensityPreference;
  language: LanguagePreference;
  editorMode: EditorModePreference;
  /** 工程版本（只读展示；来源：仓库根 VERSION，构建期注入） */
  version: string;
}

/** 工程版本展示（只读；来源：仓库根 VERSION，构建期由 vite define 注入。
 *  node:test 等无 define 环境回退 "dev"。 */
function appVersion(): string {
  return typeof __APP_VERSION__ === "string" ? __APP_VERSION__ : "dev";
}

export function defaultPreferences(): ConsolePreferences {
  return {
    theme: "dark",
    density: "normal",
    language: "zh",
    editorMode: "form",
    version: appVersion(),
  };
}

const STORAGE_KEY = "ros.console.preferences";

/** node:test 无 window；通过惰性访问 + 缺失回退保证可在纯 Node 环境测试 */
function storage(): Pick<Storage, "getItem" | "setItem"> | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage;
}

function readStored(raw: string | null): Partial<ConsolePreferences> {
  if (raw === null) {
    return {};
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) {
      return {};
    }
    const partial: Partial<ConsolePreferences> = {};
    const record = parsed as Record<string, unknown>;
    const theme = record.theme;
    if (theme === "dark" || theme === "light") {
      partial.theme = theme;
    }
    const density = record.density;
    if (density === "normal" || density === "compact") {
      partial.density = density;
    }
    const language = record.language;
    if (language === "zh" || language === "en") {
      partial.language = language;
    }
    const editorMode = record.editorMode;
    if (editorMode === "form" || editorMode === "yaml") {
      partial.editorMode = editorMode;
    }
    return partial;
  } catch {
    return {};
  }
}

export function loadPreferences(): ConsolePreferences {
  const store = storage();
  if (store === null) {
    return defaultPreferences();
  }
  const stored = readStored(store.getItem(STORAGE_KEY));
  return { ...defaultPreferences(), ...stored };
}

export function savePreferences(preferences: ConsolePreferences): void {
  const store = storage();
  if (store === null) {
    return;
  }
  store.setItem(STORAGE_KEY, JSON.stringify(preferences));
}

/** 把偏好写到 document root（data-theme / data-density / lang） */
export function applyPreferences(preferences: ConsolePreferences): void {
  if (typeof document === "undefined") {
    return;
  }
  const root = document.documentElement;
  root.dataset.theme = preferences.theme;
  root.dataset.density = preferences.density;
  root.lang = preferences.language === "zh" ? "zh-CN" : "en";
}
