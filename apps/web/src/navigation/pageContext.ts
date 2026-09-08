/** 页面渲染上下文（PageRenderer 与各 feature 页面共享；独立模块避免循环依赖）。 */

import type { LlmEndpointReadDto } from "../api/types";
import type { ConsolePreferences } from "../layout/preferences";

export interface PageContext {
  endpoints: LlmEndpointReadDto[];
  onAddRelay: () => void;
  selectedRunId: string;
  onSelectedRunIdChange: (runId: string) => void;
  onOpenSetup: () => void;
  preferences: ConsolePreferences;
  onPreferencesChange: (next: ConsolePreferences) => void;
}
