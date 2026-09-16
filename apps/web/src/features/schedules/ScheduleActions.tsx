import { api } from "../../api/client";
import type { ScheduleEntryDto } from "../../api/types";
import { ErrorState } from "../../components/States";
import { useAsyncAction } from "../../hooks/useAsyncAction";
import { canTrigger, schedulePageCopy as copy, triggerBlockReason } from "./scheduleCopy";

/** 单行写操作：启停 + 手动触发（写面的事实以下一次读面加载为准）。 */
export function ScheduleActions({
  row,
  zh,
  onChanged,
}: {
  row: ScheduleEntryDto;
  zh: boolean;
  onChanged: () => void;
}) {
  const action = useAsyncAction(onChanged);
  const blocked = triggerBlockReason(row, zh);
  return (
    <span className="row-actions">
      <button
        className="btn sm ghost"
        type="button"
        data-testid={`schedule-toggle-${row.name}`}
        disabled={action.busy}
        onClick={() => {
          action.run(() => api.updateSchedule(row.name, { enabled: !row.enabled }));
        }}
      >
        {row.enabled ? copy.toggleOff(zh) : copy.toggleOn(zh)}
      </button>
      <button
        className="btn sm ghost"
        type="button"
        data-testid={`schedule-trigger-${row.name}`}
        disabled={action.busy || !canTrigger(row)}
        title={blocked}
        onClick={() => {
          action.run(() => api.triggerSchedule(row.name));
        }}
      >
        {copy.trigger(zh)}
      </button>
      {action.error !== null && (
        <span data-testid={`schedule-action-error-${row.name}`}>
          <ErrorState message={action.error} />
        </span>
      )}
    </span>
  );
}
