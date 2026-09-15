import { api } from "../../api/client";
import type { ToolProviderRegistrationListDto } from "../../api/types";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, UnavailableState } from "../../components/States";
import { Table } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { registrationColumns } from "./registrationColumns";
import { RegistryForm } from "./RegistryForm";

/**
 * Provider 注册表（G15 / PLAN-060）。
 *
 * PENDING 只是"已登记"：不进入上面的目录，也不参与 preflight/compile；
 * 批准（ACTIVE）后以 USER_APPROVED 出现在目录里，吊销（REVOKED）是终态退出。
 * 表里同时给出"是否已进入目录"，让两面的差异一眼可见。
 */
export function RegistryPanel({ onChanged }: { onChanged: () => void }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const registry = useResource("tool-provider-registrations", () =>
    api.toolProviderRegistrations(),
  );
  const refresh = (): void => {
    registry.reload();
    onChanged();
  };
  return (
    <PanelSection
      title={zh ? "Provider 注册表" : "Provider registry"}
      count={registry.data?.registrations.length}
      extra={
        <button
          className="btn sm ghost"
          type="button"
          disabled={registry.phase === "loading"}
          onClick={refresh}
        >
          {zh ? "刷新" : "Refresh"}
        </button>
      }
    >
      <div data-testid="registry-panel">
        <ResourceBoundary state={registry}>
          {registry.data !== null && (
            <RegistryBody data={registry.data} zh={zh} onChanged={refresh} />
          )}
        </ResourceBoundary>
      </div>
    </PanelSection>
  );
}

function RegistryBody({
  data,
  zh,
  onChanged,
}: {
  data: ToolProviderRegistrationListDto;
  zh: boolean;
  onChanged: () => void;
}) {
  return (
    <>
      {!data.management_available && (
        <UnavailableState
          title={zh ? "注册表不可用" : "Registry unavailable"}
          reason={data.management_reason ?? ""}
        />
      )}
      {data.management_available && <RegistryForm zh={zh} onRegistered={onChanged} />}
      {data.registrations.length === 0 ? (
        <EmptyState message={zh ? "尚无注册项" : "No registrations yet"} />
      ) : (
        <Table
          columns={registrationColumns(zh, onChanged)}
          rows={data.registrations}
          rowKey={(row) => row.id}
          ariaLabel={zh ? "Tool Provider 注册表" : "Tool provider registry"}
        />
      )}
    </>
  );
}
