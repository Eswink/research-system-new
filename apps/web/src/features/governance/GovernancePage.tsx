import { useState } from "react";

import { api } from "../../api/client";
import { Button } from "../../components/Button";
import { EmptyState, ErrorState, LoadingState, UnavailableState } from "../../components/States";
import { Tabs } from "../../components/Tabs";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { GAPS } from "../../navigation/pageSupport";
import styles from "../shared/FeaturePage.module.css";

type TabId = "audit" | "export" | "memory";

/** 治理（T27）：运行事件 / 真实导出 / Memory（禁用）三分区。 */
export function GovernancePage({ ctx }: { ctx: PageContext }) {
  const { t } = useI18n();
  const [tab, setTab] = useState<TabId>("audit");
  const runId = ctx.selectedRunId;
  const events = useResource(runId === "" ? null : runId, () => api.runEvents(runId));
  const exportKey = runId === "" ? null : `export:${runId}`;
  const exportBundle = useResource(exportKey, () => api.runExport(runId));

  return (
    <div className={styles.page} data-testid="governance-page">
      <h2 className={styles.heading}>{t("page.govern.audit")}</h2>
      <Tabs
        ariaLabel={t("page.govern.audit")}
        value={tab}
        onChange={setTab}
        items={[
          { id: "audit", label: "Audit" },
          { id: "export", label: "Export" },
          { id: "memory", label: "Memory" },
        ]}
      />
      {runId === "" && <EmptyState message={t("overview.noRun")} />}
      {runId !== "" && tab === "audit" && <AuditTab events={events} />}
      {runId !== "" && tab === "export" && <ExportTab bundle={exportBundle} runId={runId} />}
      {tab === "memory" && <UnavailableState title="Memory" reason={GAPS.memory} />}
    </div>
  );
}

function AuditTab({ events }: { events: ReturnType<typeof useResource<unknown[]>> }) {
  const { t } = useI18n();
  if (events.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (events.phase === "error") {
    return <ErrorState message={events.error ?? t("state.error")} />;
  }
  const list = (events.data ?? []) as { event_id: string; type: string; occurred_at: string }[];
  return (
    <div className={styles.panel}>
      <div className={styles.panelTitle}>{t("audit.runEvents")}</div>
      {list.length === 0 ? (
        <EmptyState message={t("state.empty")} />
      ) : (
        list.map((e) => (
          <div key={e.event_id} className="row">
            <span className="mono">{e.type}</span>
            <span className="mono" style={{ color: "var(--fg-faint)" }}>
              {e.occurred_at.slice(0, 19)}
            </span>
          </div>
        ))
      )}
    </div>
  );
}

interface ExportTabProps {
  bundle: ReturnType<typeof useResource<unknown>>;
  runId: string;
}

function ExportTab({ bundle, runId }: ExportTabProps) {
  const { t } = useI18n();
  if (bundle.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (bundle.phase === "error") {
    return <ErrorState message={bundle.error ?? t("state.error")} />;
  }
  const download = (): void => {
    const blob = new Blob([JSON.stringify(bundle.data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${runId}-export.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className={styles.panel}>
      <div className={styles.panelTitle}>{t("audit.export")}</div>
      <p style={{ margin: "0 0 10px", fontSize: "var(--fs-caption)", color: "var(--fg-muted)" }}>
        {t("audit.exportNote")}
      </p>
      <Button variant="primary" icon="external" onClick={download}>{t("audit.download")}</Button>
    </div>
  );
}
