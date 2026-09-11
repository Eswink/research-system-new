import { useState } from "react";

import { api } from "../../api/client";
import { problemText } from "../../api/problemText";
import type { ProjectSettingsDto } from "../../api/types";

/** 项目设置单项保存：PUT last-write-wins（无 If-Match），失败可见且不自动重试。 */
export function useSettingsSave(onSaved: () => void) {
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<string | null>(null);
  const save = async (payload: ProjectSettingsDto): Promise<void> => {
    setBusy(true);
    setIssue(null);
    try {
      await api.saveProjectSettings(payload);
      onSaved();
    } catch (err) {
      setIssue(problemText(err));
    } finally {
      setBusy(false);
    }
  };
  return { busy, issue, save };
}
