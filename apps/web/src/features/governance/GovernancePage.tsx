import type { ExportBundleDto, RunEventDto } from "../../api/types";
import type { TranslationKey } from "../../i18n/zh";
import { useState } from "react";
import { api } from "../../api/client";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { Tabs } from "../../components/Tabs";
import { useResource, type ResourceState } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import type { PageContext } from "../../navigation/pageContext";
import { TimelineView } from "../runs/TimelineView";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { RunQueryBar } from "../shared/RunQueryBar";
import { ExportView } from "./ExportView";
import { MemoryPanel } from "./MemoryPanel";
import { PolicyPanel } from "./PolicyPanel";

type TabId = "audit" | "export" | "memory";

export function GovernancePage({ ctx }: { ctx: PageContext }) {
  const { language, t } = useI18n();
  const [tab, setTab] = useState<TabId>("audit");
  const runId = ctx.selectedRunId;
  const events = useResource(runId === "" || tab !== "audit" ? null : runId, () =>
    api.runEvents(runId),
  );
  const bundle = useResource(runId === "" || tab !== "export" ? null : runId, () =>
    api.runExport(runId),
  );
  return (
    <section className={styles.page} data-testid="governance-page">
      <GovernancePageGovernAudit {...{ t, language, runId, events, bundle, ctx }} />
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
      {runId === "" && tab !== "memory" && <EmptyState message={t("overview.noRun")} />}
      {tab === "audit" && (
        <ResourceBoundary state={events}>
          {events.data !== null && <TimelineView key={runId} events={events.data} />}
        </ResourceBoundary>
      )}
      {tab === "export" && (
        <ResourceBoundary state={bundle}>
          {bundle.data !== null && <ExportView bundle={bundle.data} runId={runId} />}
        </ResourceBoundary>
      )}
      {tab === "memory" && (
        <>
          <PolicyPanel />
          <MemoryPanel />
        </>
      )}
    </section>
  );
}

interface GovernancePageGovernAuditProps {
  t: (key: TranslationKey) => string;
  language: string;
  runId: string;
  events: ResourceState<RunEventDto[]>;
  bundle: ResourceState<ExportBundleDto>;
  ctx: PageContext;
}

function GovernancePageGovernAudit({
  t,
  language,
  runId,
  events,
  bundle,
  ctx,
}: GovernancePageGovernAuditProps) {
  return (
    <PageHeader
      title={t("page.govern.audit")}
      kicker="GOVERNANCE / AUDIT & EXPORT"
      description={
        language === "zh"
          ? "正式运行事件与 JSON 导出。工程会话档案和示例数据不属于产品 Memory 或科研证据。"
          : [
              "Persisted run events and JSON export. Engineering sessions and examples ",
              "are not product memory or research evidence.",
            ].join("")
      }
      actions={
        <RunQueryBar
          runId={runId}
          onSelect={(id) => {
            if (id === runId) {
              events.reload();
              bundle.reload();
            } else ctx.onSelectedRunIdChange(id);
          }}
        />
      }
    />
  );
}
