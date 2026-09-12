/** 项目设置逐行编辑控件（每行一个字段，显式保存；PUT last-write-wins 已明示）。 */

import { useState } from "react";

import type { ProjectSettingsDto, TeamTemplateDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { ErrorState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { useSettingsSave } from "./useSettingsSave";

const FIELD_LABEL: Record<string, { zh: string; en: string }> = {
  default_model_profile_id: { zh: "默认模型 Profile", en: "Default model profile" },
  budget_policy_id: { zh: "预算策略", en: "Budget policy" },
  workspace_backend: { zh: "Workspace 后端", en: "Workspace backend" },
  compute_profile: { zh: "计算 Profile", en: "Compute profile" },
  policy_id: { zh: "策略", en: "Policy" },
  reference_protocol: { zh: "参考协议", en: "Reference protocol" },
  team_template_id: { zh: "团队模板", en: "Team template" },
};

function fieldLabel(field: string, zh: boolean): string {
  const entry = FIELD_LABEL[field];
  return entry === undefined ? field : zh ? entry.zh : entry.en;
}

interface SaveRowProps {
  dirty: boolean;
  busy: boolean;
  issue: string | null;
  zh: boolean;
  onSave: () => void;
}

function SaveRow({ dirty, busy, issue, zh, onSave }: SaveRowProps) {
  return (
    <>
      <div className={styles.toolbar}>
        <button className="btn sm primary" type="button" disabled={busy || !dirty} onClick={onSave}>
          {busy ? (zh ? "保存中…" : "Saving…") : zh ? "保存此项" : "Save field"}
        </button>
        <Chip tone={dirty ? "accent" : "neutral"}>
          {dirty ? (zh ? "有未保存修改" : "Unsaved change") : zh ? "与服务器一致" : "In sync"}
        </Chip>
      </div>
      {issue !== null && <ErrorState message={issue} />}
    </>
  );
}

export type TextFieldKey =
  | "default_model_profile_id"
  | "budget_policy_id"
  | "workspace_backend"
  | "compute_profile"
  | "policy_id"
  | "reference_protocol";

export function TextFieldRow({
  current,
  field,
  nullable,
  hint,
  onSaved,
}: {
  current: ProjectSettingsDto;
  field: TextFieldKey;
  nullable?: boolean;
  hint?: string;
  onSaved: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const original = current[field];
  const [text, setText] = useState(original ?? "");
  const { busy, issue, save } = useSettingsSave(onSaved);
  const trimmed = text.trim();
  const dirty = trimmed !== (original ?? "");
  const blocked = nullable !== true && trimmed.length === 0;
  const shown = blocked ? (zh ? "此字段不可为空" : "Field must not be empty") : issue;
  return (
    <div className={styles.toolbar}>
      <label className={styles.queryLabel}>
        {fieldLabel(field, zh)}
        <input
          className="input mono"
          value={text}
          disabled={busy}
          placeholder={nullable === true ? "INHERIT (empty)" : ""}
          onChange={(event) => {
            setText(event.target.value);
          }}
        />
        {hint !== undefined && <span>{hint}</span>}
      </label>
      <SaveRow
        dirty={dirty && !blocked}
        busy={busy}
        issue={shown}
        zh={zh}
        onSave={() => {
          void save({ ...current, [field]: trimmed.length === 0 ? null : trimmed });
        }}
      />
    </div>
  );
}

export function TemplateRow({
  current,
  options,
  onSaved,
}: {
  current: ProjectSettingsDto;
  options: TeamTemplateDto[];
  onSaved: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [templateId, setTemplateId] = useState(current.team_template_id);
  const { busy, issue, save } = useSettingsSave(onSaved);
  return (
    <div className={styles.toolbar}>
      <TemplateSelect {...{ current, options, templateId, setTemplateId, busy, zh }} />
      <SaveRow
        dirty={templateId !== current.team_template_id}
        busy={busy}
        issue={issue}
        zh={zh}
        onSave={() => {
          void save({ ...current, team_template_id: templateId });
        }}
      />
    </div>
  );
}

function TemplateSelect({
  current,
  options,
  templateId,
  setTemplateId,
  busy,
  zh,
}: {
  current: ProjectSettingsDto;
  options: TeamTemplateDto[];
  templateId: string;
  setTemplateId: (value: string) => void;
  busy: boolean;
  zh: boolean;
}) {
  return (
    <label className={styles.queryLabel}>
      {fieldLabel("team_template_id", zh)}
      <select
        className="input"
        value={templateId}
        disabled={busy || options.length === 0}
        onChange={(event) => {
          setTemplateId(event.target.value);
        }}
      >
        <TemplateOptions current={current} options={options} />
      </select>
    </label>
  );
}

function TemplateOptions({
  current,
  options,
}: {
  current: ProjectSettingsDto;
  options: TeamTemplateDto[];
}) {
  if (options.length === 0) {
    return <option value={current.team_template_id}>{current.team_template_id}</option>;
  }
  return (
    <>
      {options.map((template) => (
        <option key={template.id} value={template.id}>
          {template.display_name} · {template.id}
        </option>
      ))}
    </>
  );
}
