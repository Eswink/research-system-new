import { useState } from "react";
import type { RoleDefinitionDto, TeamTemplateDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

export function RoleDefinitions({ roles }: { roles: RoleDefinitionDto[] }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [selectedId, setSelectedId] = useState("");
  const selected = roles.find((role) => role.id === selectedId) ?? roles[0];
  return (
    <PanelSection
      title={zh ? "职责定义 · 只读" : "Role definitions · read only"}
      count={roles.length}
    >
      <p className={styles.notice}>
        {zh
          ? "Role 定义职责；Agent 是配置实例；Task 是执行单元。三者不可互换。"
          : [
              "Roles define responsibilities; agents are configured ",
              "instances; tasks are execution units.",
            ].join("")}
      </p>
      <div className={styles.toolbar}>
        {roles.map((role) => (
          <button
            key={role.id}
            className="btn sm"
            type="button"
            aria-pressed={selected?.id === role.id}
            onClick={() => {
              setSelectedId(role.id);
            }}
          >
            {role.id}
          </button>
        ))}
      </div>
      {selected === undefined ? (
        <EmptyState message={zh ? "没有角色定义" : "No role definitions"} />
      ) : (
        <RoleDetail role={selected} />
      )}
    </PanelSection>
  );
}

function RoleDetail({ role }: { role: RoleDefinitionDto }) {
  return (
    <KeyValueList
      fields={[
        { label: "Role", value: role.id },
        { label: "Category", value: role.category },
        { label: "Activation", value: role.activation_default },
        { label: "Workspace policy", value: role.workspace_policy },
        { label: "Review panel", value: role.review_panel_role },
        { label: "Required all", value: role.hard_model_capabilities.all_of.join(", ") || "—" },
        { label: "Required any", value: role.hard_model_capabilities.any_of.join(", ") || "—" },
      ]}
    />
  );
}

export function TeamTemplates({ templates }: { templates: TeamTemplateDto[] }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <PanelSection
      title={zh ? "团队模板 · 只读" : "Team templates · read only"}
      count={templates.length}
    >
      {templates.length === 0 ? (
        <EmptyState message={zh ? "没有团队模板" : "No team templates"} />
      ) : (
        <div className={styles.cards}>
          {templates.map((template) => (
            <article key={template.id} className={styles.card}>
              <h2 className={styles.cardTitle}>{template.display_name}</h2>
              <p className="mono">{template.id}</p>
              {Object.entries(template.roles).map(([role, count]) => (
                <Chip key={role}>
                  {role} · {count.min_instances}–{count.max_instances}
                </Chip>
              ))}
              {template.extends !== null && <p className="muted">extends: {template.extends}</p>}
            </article>
          ))}
        </div>
      )}
    </PanelSection>
  );
}
