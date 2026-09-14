import { api } from "../../api/client";
import { Table } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { OpsViewPage } from "../ops-view/OpsViewPage";
import { alertColumns } from "../ops-view/opsViewColumns";

/** 告警（EC-03 第二批）：真实派生收件箱（失败 run/降级端点/离线 worker）。 */
export function AlertsPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <OpsViewPage
      testid="alerts-page"
      title={zh ? "告警" : "Alerts"}
      kicker="OPS / ALERTS"
      description={
        zh
          ? "由真实状态派生的只读告警收件箱（失败 Run、非健康端点、离线/排水 worker）。规则 CRUD 无 API。"
          : [
              "Read-only alert inbox derived from real state (failed runs, unhealthy ",
              "endpoints, offline/draining workers). Rule CRUD has no API.",
            ].join("")
      }
      fetch={() => api.opsAlerts()}
      isEmpty={(data) => data.alerts.length === 0}
    >
      {(data) => (
        <Table
          columns={alertColumns(zh)}
          rows={data.alerts}
          rowKey={(row) => `${row.kind}:${row.subject}`}
          ariaLabel={zh ? "告警" : "Alerts"}
        />
      )}
    </OpsViewPage>
  );
}
