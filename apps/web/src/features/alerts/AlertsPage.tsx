import { useState } from "react";

import { api } from "../../api/client";
import { Chip } from "../../components/Chip";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { Table } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { OpsAlertRulesPanel } from "../ops-view/OpsAlertRulesPanel";
import { alertColumns } from "../ops-view/opsViewColumns";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/**
 * 告警（G7）：派生收件箱 + 静音规则写面（PLAN-20260915-059）。
 *
 * 收件箱本身仍是派生投影（失败 Run/非健康端点/离线 worker），规则只做标记；
 * 规则不可用时如实给出原因，不把"没有 store"显示成"没有规则"。
 */
export function AlertsPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  const [nonce, setNonce] = useState(0);
  const alerts = useResource(`ops-alerts-${String(nonce)}`, () => api.opsAlerts());
  const refresh = (): void => {
    setNonce((n) => n + 1);
  };
  return (
    <section className={styles.page} data-testid="alerts-page">
      <PageHeader
        title={zh ? "告警" : "Alerts"}
        kicker="OPS / ALERTS"
        description={
          zh
            ? [
                "由真实状态派生的告警收件箱（失败 Run、非健康端点、离线/排水 worker）。",
                "规则只做静音标记（命中项带 muted/muted_by 但仍在列表里），不隐藏告警。",
              ].join("")
            : [
                "Alert inbox derived from real state (failed runs, unhealthy endpoints, ",
                "offline/draining workers). Rules only mark matches as muted — muted items ",
                "stay in the list.",
              ].join("")
        }
        actions={
          alerts.data !== null && (
            <Chip tone={alerts.data.muted_count > 0 ? "warn" : "accent"}>
              {`${String(alerts.data.alerts.length)} / ${String(alerts.data.muted_count)}`}
            </Chip>
          )
        }
      />
      <ResourceBoundary state={alerts}>
        {alerts.data !== null &&
          (alerts.data.alerts.length === 0 ? (
            <EmptyState message={zh ? "无告警" : "No alerts"} />
          ) : (
            <Table
              columns={alertColumns(zh)}
              rows={alerts.data.alerts}
              rowKey={(row) => `${row.kind}:${row.subject}`}
              ariaLabel={zh ? "告警" : "Alerts"}
            />
          ))}
      </ResourceBoundary>
      <OpsAlertRulesPanel onChanged={refresh} />
    </section>
  );
}
