import { GapLayout } from "../shared/GapLayout";
import { pageSupport } from "../../navigation/pageSupport";
import { useI18n } from "../../i18n/useI18n";

/** 集成（T26）：集成目录 + 配置结构；无 Tool Provider 管理 API。 */
export function IntegrationsPage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "ops", page: "integrations" });
  return (
    <div data-testid="gap-page-ops-integrations">
      <GapLayout
        title={t("page.ops.integrations")}
        support={support}
        columns={[
          t("integrations.provider"),
          t("integrations.capabilities"),
          t("gap.column.status"),
        ]}
        actions={[{ label: t("integrations.connect") }]}
        detailTitle={t("integrations.config")}
      />
    </div>
  );
}
