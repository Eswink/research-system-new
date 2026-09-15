import { useState } from "react";

import { api } from "../../api/client";
import type { IncidentsViewDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, UnavailableState } from "../../components/States";
import { Table } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { DeclareIncidentForm } from "../ops-view/IncidentActions";
import { declaredIncidentColumns, incidentCandidateColumns } from "../ops-view/opsViewColumns";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/**
 * 事故（G7）：已登记事故的处置工作流 + 失败 Run 候选（PLAN-20260915-059）。
 *
 * 两个列表**语义不同**：候选是派生态（失败 Run 不会自动变成事故），
 * 已登记才是 declare/assign/close 的真实对象；已登记（含已关闭）的来源 run
 * 不再出现在候选里，但仍留在已登记列表中可追溯。
 */
export function IncidentsPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  const [nonce, setNonce] = useState(0);
  const incidents = useResource(`ops-incidents-${String(nonce)}`, () => api.opsIncidents());
  const refresh = (): void => {
    setNonce((n) => n + 1);
  };
  return (
    <section className={styles.page} data-testid="incidents-page">
      <PageHeader
        title={zh ? "事故" : "Incidents"}
        kicker="OPS / INCIDENTS"
        description={
          zh
            ? [
                "已登记事故可指派处理人、写处理结论后关闭（关闭后不可再处置）。",
                "失败 Run 只作为候选列出——不自动登记为事故，需要显式声明。",
              ].join("")
            : [
                "Registered incidents can be assigned and closed with a resolution ",
                "(closed incidents reject further transitions). Failed runs are only ",
                "candidates — they are never auto-registered.",
              ].join("")
        }
      />
      <ResourceBoundary state={incidents}>
        {incidents.data !== null && (
          <IncidentBody data={incidents.data} zh={zh} refresh={refresh} />
        )}
      </ResourceBoundary>
    </section>
  );
}

function IncidentBody({
  data,
  zh,
  refresh,
}: {
  data: IncidentsViewDto;
  zh: boolean;
  refresh: () => void;
}) {
  return (
    <div data-testid="incident-board">
      {!data.workflow_available && (
        <UnavailableState
          title={zh ? "事故处置不可用" : "Disposition unavailable"}
          reason={data.workflow_reason ?? ""}
        />
      )}
      {data.workflow_available && <DeclareIncidentForm zh={zh} onDeclared={refresh} />}
      <RegisteredSection data={data} zh={zh} refresh={refresh} />
      <CandidatesSection data={data} zh={zh} refresh={refresh} />
    </div>
  );
}

function RegisteredSection({
  data,
  zh,
  refresh,
}: {
  data: IncidentsViewDto;
  zh: boolean;
  refresh: () => void;
}) {
  return (
    <PanelSection title={zh ? "已登记事故" : "Registered incidents"} count={data.incidents.length}>
      {data.incidents.length === 0 ? (
        <EmptyState
          message={
            zh
              ? "尚无已登记事故（失败 Run 不会自动登记）"
              : "No registered incidents (failed runs are never auto-registered)"
          }
        />
      ) : (
        <Table
          columns={declaredIncidentColumns(zh, refresh)}
          rows={data.incidents}
          rowKey={(row) => row.id}
          ariaLabel={zh ? "已登记事故" : "Registered incidents"}
        />
      )}
    </PanelSection>
  );
}

function CandidatesSection({
  data,
  zh,
  refresh,
}: {
  data: IncidentsViewDto;
  zh: boolean;
  refresh: () => void;
}) {
  return (
    <PanelSection
      title={zh ? "失败 Run 候选" : "Failed run candidates"}
      count={data.candidates.length}
    >
      {data.candidates.length === 0 ? (
        <EmptyState message={zh ? "无候选" : "No candidates"} />
      ) : (
        <Table
          columns={incidentCandidateColumns(zh, refresh)}
          rows={data.candidates}
          rowKey={(row) => row.run_id}
          ariaLabel={zh ? "事故候选" : "Incident candidates"}
        />
      )}
    </PanelSection>
  );
}

/** 写面不可用的原因 chip（保留导出以免调用方重复实现）。 */
export function WorkflowStateChip({ available, zh }: { available: boolean; zh: boolean }) {
  return (
    <Chip tone={available ? "accent" : "warn"}>
      {available ? (zh ? "可处置" : "writable") : zh ? "只读" : "read-only"}
    </Chip>
  );
}
