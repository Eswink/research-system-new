import { useState } from "react";

import { api } from "../../api/client";
import type { RunDetailDto } from "../../api/types";
import { useI18n } from "../../i18n/useI18n";
import { canRequestCancellation } from "./runTransitions";
import { RunActionButtonRow } from "./RunActionButtons";
import { useRunControlPlane } from "./useRunControlPlane";

/** No start shortcut bypasses the editor's compile/preflight flow. Cancellation is explicit. */
export function RunActions({
  run,
  busy,
  onChanged,
}: {
  run: RunDetailDto;
  busy: boolean;
  onChanged: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [confirm, setConfirm] = useState(false);
  const control = useRunControlPlane(busy, onChanged);
  const cancel = async (): Promise<void> => {
    if (!canRequestCancellation(run.state)) return;
    await control.request(() => api.cancelRun(run.id));
    setConfirm(false);
  };
  return (
    <RunActionButtonRow
      {...{
        run,
        zh,
        busy,
        control,
        setConfirm,
        cancel,
        confirm,
        pause: () => {
          void control.request(() => api.pauseRun(run.id));
        },
        resume: () => {
          void control.request(() => api.resumeRun(run.id));
        },
      }}
    />
  );
}
