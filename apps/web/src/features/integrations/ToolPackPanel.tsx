import { api } from "../../api/client";
import type { ToolPackListDto } from "../../api/types";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, UnavailableState } from "../../components/States";
import { Table } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { pendingUpdates, ToolPackPendingBanner } from "./ToolPackPendingBanner";
import { ToolPackInstallForm } from "./ToolPackInstallForm";
import { toolPackColumns } from "./toolPackColumns";

/**
 * ToolPack 供应链面板（G15 / PLAN-065）。
 *
 * 三段呈现："已安装并生效"的表、安装/提交表单、待批准横幅（未生效）。
 * 待批准**不是**已生效：候选 digest 只在横幅里出现，表的 digest 列始终是生效版本。
 */
export function ToolPackPanel({ onChanged }: { onChanged: () => void }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const packs = useResource("tool-packs", () => api.listToolPacks());
  const refresh = (): void => {
    packs.reload();
    onChanged();
  };
  return (
    <PanelSection
      title={zh ? "ToolPack 供应链" : "ToolPack supply chain"}
      count={packs.data?.packs.length}
      extra={
        <button
          className="btn sm ghost"
          type="button"
          disabled={packs.phase === "loading"}
          onClick={refresh}
        >
          {zh ? "刷新" : "Refresh"}
        </button>
      }
    >
      <div data-testid="toolpack-panel">
        <ResourceBoundary state={packs}>
          {packs.data !== null && <ToolPackBody data={packs.data} zh={zh} onChanged={refresh} />}
        </ResourceBoundary>
      </div>
    </PanelSection>
  );
}

function ToolPackBody({
  data,
  zh,
  onChanged,
}: {
  data: ToolPackListDto;
  zh: boolean;
  onChanged: () => void;
}) {
  const available = data.unavailable_reason === null;
  return (
    <>
      {!available && (
        <UnavailableState
          title={zh ? "ToolPack 存储不可用" : "ToolPack store unavailable"}
          reason={data.unavailable_reason ?? ""}
        />
      )}
      {available && <ToolPackInstallForm zh={zh} onInstalled={onChanged} />}
      <ToolPackPendingBanner updates={pendingUpdates(data.packs)} zh={zh} onChanged={onChanged} />
      {data.packs.length === 0 ? (
        <EmptyState
          message={
            zh
              ? "尚未安装任何 ToolPack（空列表是正确状态，不是错误）"
              : "No tool packs installed yet (an empty list is a valid state)"
          }
        />
      ) : (
        <Table
          columns={toolPackColumns(zh, onChanged)}
          rows={data.packs}
          rowKey={(row) => row.id}
          ariaLabel={zh ? "ToolPack 列表" : "Tool pack list"}
        />
      )}
      <p className={styles.notice} data-testid="toolpack-note">
        {data.note}
      </p>
    </>
  );
}
