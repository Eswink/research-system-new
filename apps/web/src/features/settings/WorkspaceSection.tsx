import { api } from "../../api/client";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

/** Read-only current project configuration; no invented profile, credentials or LWW save. */
export function WorkspaceSection() {
  const { language, t } = useI18n();
  const settings = useResource("project-settings", () => api.getProjectSettings());
  const value = settings.data;
  return (
    <PanelSection
      title={t("settings.workspace")}
      extra={
        <button
          className="btn sm"
          type="button"
          disabled={settings.phase === "loading"}
          onClick={settings.reload}
        >
          {language === "zh" ? "刷新" : "Refresh"}
        </button>
      }
    >
      <ResourceBoundary state={settings}>
        {value !== null && (
          <KeyValueList
            fields={[
              { label: "Project", value: value.project_id },
              { label: "Team template", value: value.team_template_id },
              {
                label: "Default model profile",
                value: value.default_model_profile_id ?? "INHERIT",
              },
              { label: "Budget policy", value: value.budget_policy_id },
              { label: "Workspace backend", value: value.workspace_backend },
              { label: "Compute profile", value: value.compute_profile ?? "INHERIT" },
              { label: "Policy", value: value.policy_id },
            ]}
          />
        )}
      </ResourceBoundary>
      <p className={styles.notice}>
        {language === "zh"
          ? "此视图只读。项目设置写接口为 last-write-wins；本页未提供无冲突保障的批量保存按钮。"
          : [
              "Read-only view. The project-settings write API is last-write-wins; this ",
              "page does not offer an unguarded bulk save.",
            ].join("")}
      </p>
    </PanelSection>
  );
}
