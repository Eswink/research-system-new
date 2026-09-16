import { api } from "../../api/client";
import { Chip } from "../../components/Chip";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { UnavailableState } from "../../components/States";
import { Table } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { providerColumns } from "./providerColumns";
import { RegistryPanel } from "./RegistryPanel";
import { ToolPackPanel } from "./ToolPackPanel";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/** 集成（EC-02 目录 + PLAN-060 治理写面）：provider 目录 + 注册/批准/吊销。 */
export function IntegrationsPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  const providers = useResource("catalog", () => api.listToolProviders());
  return (
    <section className={styles.page} data-testid="integrations-page">
      <PageHeader
        title={zh ? "集成" : "Integrations"}
        kicker="OPS / INTEGRATIONS"
        description={integrationsDescription(zh)}
        actions={
          providers.data !== null && (
            <Chip tone="accent">{String(providers.data.providers.length)}</Chip>
          )
        }
      />
      <ResourceBoundary state={providers}>
        {providers.data !== null && (
          <>
            <Table
              columns={providerColumns(zh)}
              rows={providers.data.providers}
              rowKey={(row) => row.id}
              ariaLabel={zh ? "Tool Provider 目录" : "Tool provider catalog"}
            />
            {!providers.data.management_available && providers.data.management_reason !== null && (
              <UnavailableState
                title={zh ? "管理面不可用" : "Management unavailable"}
                reason={providers.data.management_reason}
              />
            )}
          </>
        )}
      </ResourceBoundary>
      <RegistryPanel onChanged={providers.reload} />
      <ToolPackPanel onChanged={providers.reload} />
    </section>
  );
}

function integrationsDescription(zh: boolean): string {
  if (zh) {
    return [
      "目录是已批准的来源（examples 契约 + APPROVED 注册），PENDING/REVOKED 不在这里。",
      "注册需 pin：sha256 内容寻址 digest；批准后 preflight/compile 立即可见。",
      "ToolPack 写面：install 由控制面重算 digest 校验，权限扩张须批准后才生效。",
    ].join("");
  }
  return [
    "The catalog lists approved sources only (examples contracts + APPROVED registrations); ",
    "PENDING/REVOKED never appear here. Registration requires a sha256 pin, and approval ",
    "makes it immediately visible to preflight/compile. Tool pack installs are digest-verified ",
    "server-side, and permission expansions stay pending until approved.",
  ].join("");
}
