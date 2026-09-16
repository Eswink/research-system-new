import { api } from "../../api/client";
import type { SchedulesViewDto } from "../../api/types";
import { PanelSection } from "../../components/PanelSection";
import { Table } from "../../components/Table";
import { EmptyState, UnavailableState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { OpsViewPage } from "../ops-view/OpsViewPage";
import { scheduleColumns } from "../ops-view/opsViewColumns";
import { ScheduleCreateForm } from "./ScheduleCreateForm";
import { schedulePageCopy as copy } from "./scheduleCopy";

/**
 * 调度（EC-03）：定义可写（登记 / 启停 / 手动触发），执行体仍是进程内守护线程。
 * 写面的效果由随后的读面加载呈现——`运行事实` 列就是那份证据。
 */
export function SchedulesPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <OpsViewPage
      testid="schedules-page"
      title={zh ? "调度" : "Schedules"}
      kicker="OPS / SCHEDULES"
      description={copy.description(zh)}
      fetch={() => api.opsSchedules()}
      isEmpty={() => false}
    >
      {(data, reload) => <SchedulesBody data={data} zh={zh} onChanged={reload} />}
    </OpsViewPage>
  );
}

function SchedulesBody({
  data,
  zh,
  onChanged,
}: {
  data: SchedulesViewDto;
  zh: boolean;
  onChanged: () => void;
}) {
  return (
    <>
      {!data.management_available && (
        <UnavailableState
          title={copy.unavailableTitle(zh)}
          reason={data.management_reason ?? ""}
        />
      )}
      <PanelSection title={copy.createTitle(zh)} count={data.schedules.length}>
        <div data-testid="schedules-panel">
          {data.management_available && (
            <ScheduleCreateForm zh={zh} jobs={data.jobs} onCreated={onChanged} />
          )}
          {data.schedules.length === 0 ? (
            <EmptyState message={copy.empty(zh)} />
          ) : (
            <Table
              columns={scheduleColumns(zh, onChanged)}
              rows={data.schedules}
              rowKey={(row) => row.name}
              ariaLabel={zh ? "调度定义" : "Schedule definitions"}
            />
          )}
        </div>
      </PanelSection>
      <p className="hint" data-testid="schedules-note">
        {data.note}
      </p>
    </>
  );
}
