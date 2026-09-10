import { useState } from "react";

import { api } from "../../api/client";
import { problemText } from "../../api/problemText";
import type { ModelReadDto } from "../../api/types";
import { Field } from "../../components/Field";
import { PanelSection } from "../../components/PanelSection";
import { ErrorState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

/** 编辑模型配置：PATCH + If-Match（version 即 ETag 值）。 */
export function ModelEditForm({ model, onSaved }: { model: ModelReadDto; onSaved: () => void }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [displayName, setDisplayName] = useState(model.display_name ?? "");
  const [enabled, setEnabled] = useState(model.enabled);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<string | null>(null);
  const dirty = displayName !== (model.display_name ?? "") || enabled !== model.enabled;
  const save = async (): Promise<void> => {
    setBusy(true);
    setIssue(null);
    try {
      const trimmed = displayName.trim();
      const payload = { display_name: trimmed.length > 0 ? trimmed : null, enabled };
      await api.updateModel(model.id, payload, model.version);
      onSaved();
    } catch (err) {
      setIssue(problemText(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <PanelSection title={zh ? "编辑模型配置" : "Edit model configuration"}>
      <ModelEditFields
        {...{
          model,
          displayName,
          setDisplayName,
          enabled,
          setEnabled,
          busy,
          dirty,
          issue,
          zh,
          onSave: () => {
            void save();
          },
        }}
      />
    </PanelSection>
  );
}

interface ModelEditFieldsProps {
  model: ModelReadDto;
  displayName: string;
  setDisplayName: (value: string) => void;
  enabled: boolean;
  setEnabled: (value: boolean) => void;
  busy: boolean;
  dirty: boolean;
  issue: string | null;
  zh: boolean;
  onSave: () => void;
}

function ModelEditFields(props: ModelEditFieldsProps): React.JSX.Element {
  const { model, displayName, setDisplayName, enabled, setEnabled, busy, dirty, issue, zh } = props;
  const hint = zh
    ? "仅展示用途；模型 ID 与探测结果不可在此改写。"
    : "Presentation only; model id and probe results are never editable here.";
  return (
    <div className={styles.page} data-testid="model-edit-form">
      <Field label={zh ? "显示名" : "Display name"} htmlFor={`model-display-${model.id}`} hint={hint}>
        <input
          id={`model-display-${model.id}`}
          className="input"
          value={displayName}
          disabled={busy}
          onChange={(event) => {
            setDisplayName(event.target.value);
          }}
        />
      </Field>
      <label className={styles.notice}>
        <input
          type="checkbox"
          checked={enabled}
          disabled={busy}
          onChange={(event) => {
            setEnabled(event.target.checked);
          }}
        />{" "}
        {zh ? "启用此模型" : "Enabled"}
      </label>
      <div className={styles.toolbar}>
        <button
          className="btn primary sm"
          type="button"
          disabled={busy || !dirty}
          onClick={props.onSave}
        >
          {busy ? (zh ? "保存中…" : "Saving…") : zh ? "保存" : "Save"}
        </button>
      </div>
      {issue !== null && <ErrorState message={issue} />}
    </div>
  );
}
