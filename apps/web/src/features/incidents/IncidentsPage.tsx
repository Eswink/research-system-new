import { api } from "../../api/client";
import { Table } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { OpsViewPage } from "../ops-view/OpsViewPage";
import { incidentColumns } from "../ops-view/opsViewColumns";

/** 事故（EC-03 第二批）：FAILED run 候选；无 declare/assign/close 处置工作流。 */
export function IncidentsPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <OpsViewPage
      testid="incidents-page"
      title={zh ? "事故" : "Incidents"}
      kicker="OPS / INCIDENTS"
      description={
        zh
          ? "失败 Run 的事故候选列表（只读）。失败 Run 不自动登记为事故；无处置工作流。"
          : [
              "Candidates for incidents (failed runs, read-only). Failed runs are not ",
              "auto-registered as incidents; no disposition workflow exists.",
            ].join("")
      }
      fetch={() => api.opsIncidents()}
      isEmpty={(data) => data.incidents.length === 0}
    >
      {(data) => (
        <Table
          columns={incidentColumns(zh)}
          rows={data.incidents}
          rowKey={(row) => row.run_id}
          ariaLabel={zh ? "事故候选" : "Incident candidates"}
        />
      )}
    </OpsViewPage>
  );
}
