import { api } from "../../api/client";
import type { ProjectSettingsDto } from "../../api/types";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { TextFieldRow, TemplateRow } from "./SettingsRows";
import styles from "../shared/LivePage.module.css";

/** 项目设置逐项保存：写接口为 last-write-wins，每行显式保存、仅改该字段。 */
export function WorkspaceSection() {
  const { language, t } = useI18n();
  const zh = language === "zh";
  const settings = useResource("project-settings", () => api.getProjectSettings());
  const templates = useResource("workspace-templates", () => api.listTeamTemplates());
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
          {zh ? "刷新" : "Refresh"}
        </button>
      }
    >
      <ResourceBoundary state={settings}>
        {settings.data !== null && (
          <SettingsRows
            current={settings.data}
            options={templates.data ?? []}
            onSaved={settings.reload}
            zh={zh}
          />
        )}
      </ResourceBoundary>
      <LwwNotice zh={zh} />
    </PanelSection>
  );
}

function SettingsRows({
  current,
  options,
  onSaved,
  zh,
}: {
  current: ProjectSettingsDto;
  options: Parameters<typeof TemplateRow>[0]["options"];
  onSaved: () => void;
  zh: boolean;
}) {
  const wsHint = zh
    ? "必须引用已注册 workspace backend，否则后端以 422 拒绝。"
    : "Must reference a registered workspace backend; others are rejected with 422.";
  const protocolHint = zh
    ? "examples/protocols 内协议文件名；Team 页参考协议预检与未选运行时的运行入口使用它。"
    : "A filename under examples/protocols; drives the team-page preflight and the run entry.";
  return (
    <div className={styles.page} data-testid="workspace-settings-form">
      <TemplateRow current={current} options={options} onSaved={onSaved} />
      <TextFieldRow current={current} field="default_model_profile_id" nullable onSaved={onSaved} />
      <TextFieldRow current={current} field="budget_policy_id" onSaved={onSaved} />
      <TextFieldRow current={current} field="workspace_backend" hint={wsHint} onSaved={onSaved} />
      <TextFieldRow
        current={current}
        field="reference_protocol"
        nullable
        hint={protocolHint}
        onSaved={onSaved}
      />
      <TextFieldRow current={current} field="compute_profile" nullable onSaved={onSaved} />
      <TextFieldRow current={current} field="policy_id" onSaved={onSaved} />
    </div>
  );
}

function LwwNotice({ zh }: { zh: boolean }) {
  return (
    <p className={styles.notice}>
      {zh
        ? "项目设置写接口为 last-write-wins（无 If-Match 冲突检测）；每行仅在显式保存时发送整份载荷，只改一个字段。"
        : [
            "The project-settings API is last-write-wins (no If-Match conflict check); ",
            "each row sends the full payload changing only that field, on explicit save.",
          ].join("")}
    </p>
  );
}
