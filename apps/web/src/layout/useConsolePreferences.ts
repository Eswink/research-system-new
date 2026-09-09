import { useEffect, useState } from "react";
import { applyPreferences, loadPreferences, savePreferences } from "./preferences";

export function useConsolePreferences() {
  const [preferences, setPreferences] = useState(loadPreferences);
  useEffect(() => {
    applyPreferences(preferences);
    savePreferences(preferences);
  }, [preferences]);
  return [preferences, setPreferences] as const;
}
