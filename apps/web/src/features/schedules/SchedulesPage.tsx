import { api } from "../../api/client";
import { Table } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { OpsViewPage } from "../ops-view/OpsViewPage";
import { scheduleColumns } from "../ops-view/opsViewColumns";

/** 调度（EC-03 第二批）：进程内 scheduler 配置事实；无用户可见调度 API。 */
export function SchedulesPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <OpsViewPage
      testid="schedules-page"
      title={zh ? "调度" : "Schedules"}
      kicker="OPS / SCHEDULES"
      description={
        zh
          ? "进程内守护 scheduler 的配置事实（租约恢复/outbox 中继/保留清理/worker 回收）。无创建/启停/触发 API。"
          : [
              "Configuration facts for the in-process schedulers (lease recovery, outbox ",
              "relay, retention, worker reaper). No create/start/stop/trigger API.",
            ].join("")
      }
      fetch={() => api.opsSchedules()}
      isEmpty={(data) => data.schedules.length === 0}
    >
      {(data) => (
        <Table
          columns={scheduleColumns(zh)}
          rows={data.schedules}
          rowKey={(row) => row.name}
          ariaLabel={zh ? "调度器" : "Schedulers"}
        />
      )}
    </OpsViewPage>
  );
}
