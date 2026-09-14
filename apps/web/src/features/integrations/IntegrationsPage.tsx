import { api } from "../../api/client";
import { Chip } from "../../components/Chip";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { UnavailableState } from "../../components/States";
import { Table } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { providerColumns } from "./providerColumns";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/** 集成（EC-02）：Tool Provider 目录只读投影 + 三态健康；管理动作保持 G15 锁定。 */
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
    </section>
  );
}

function integrationsDescription(zh: boolean): string {
  if (zh) {
    return [
      "Tool Provider 目录（Skill→Capability→ToolResolver 的来源配置）+ 三态健康。",
      "安装/批准/吊销属供应链治理面，不提供。",
    ].join("");
  }
  return [
    "Tool Provider catalog (source config for Skill→Capability→ToolResolver) ",
    "with tri-state health. Install/approve/revoke is supply-chain governance, ",
    "not offered here.",
  ].join("");
}
