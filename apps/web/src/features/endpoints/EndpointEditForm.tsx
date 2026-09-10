/** 端点编辑表单组件（PATCH + If-Match）。纯校验模型见 endpointFormModel.ts。 */

import { useState } from "react";

import { api } from "../../api/client";
import { problemText } from "../../api/problemText";
import type { LlmEndpointReadDto } from "../../api/types";
import { Field } from "../../components/Field";
import { ErrorState } from "../../components/States";
import styles from "../shared/LivePage.module.css";
import {
  endpointFormState,
  toUpdatePayload,
  type EndpointFormState,
} from "./endpointFormModel";

interface SaveContext {
  endpoint: LlmEndpointReadDto;
  etag: string;
  zh: boolean;
  onDone: () => void;
}

function useEndpointSave(context: SaveContext) {
  const { endpoint, etag, zh, onDone } = context;
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<string | null>(null);
  const save = async (form: EndpointFormState): Promise<void> => {
    const built = toUpdatePayload(form, zh);
    if (typeof built === "string") {
      setIssue(built);
      return;
    }
    setBusy(true);
    setIssue(null);
    try {
      await api.updateEndpoint(endpoint.id, built, etag);
      onDone();
    } catch (err) {
      setIssue(problemText(err));
    } finally {
      setBusy(false);
    }
  };
  return { busy, issue, save };
}

export function EndpointEditForm({
  endpoint,
  etag,
  zh,
  onCancel,
  onDone,
}: {
  endpoint: LlmEndpointReadDto;
  etag: string;
  zh: boolean;
  onCancel: () => void;
  onDone: () => void;
}) {
  const [form, setForm] = useState<EndpointFormState>(() => endpointFormState(endpoint));
  const set = (patch: Partial<EndpointFormState>): void => {
    setForm((current) => ({ ...current, ...patch }));
  };
  const { busy, issue, save } = useEndpointSave({ endpoint, etag, zh, onDone });
  return (
    <EndpointEditFields
      {...{
        form,
        set,
        busy,
        issue,
        zh,
        onCancel,
        onSave: () => {
          void save(form);
        },
      }}
    />
  );
}

interface EditFieldsProps {
  form: EndpointFormState;
  set: (patch: Partial<EndpointFormState>) => void;
  busy: boolean;
  issue: string | null;
  zh: boolean;
  onCancel: () => void;
  onSave: () => void;
}

function EndpointEditFields({ form, set, busy, issue, zh, onCancel, onSave }: EditFieldsProps) {
  return (
    <div className={styles.page} data-testid="endpoint-edit-form">
      <Field label={zh ? "名称" : "Name"} htmlFor="ep-name">
        <TextValue
          id="ep-name"
          value={form.name}
          busy={busy}
          onChange={(value) => {
            set({ name: value });
          }}
        />
      </Field>
      <Field label="Base URL" htmlFor="ep-base">
        <TextValue
          id="ep-base"
          value={form.baseUrl}
          busy={busy}
          mono
          onChange={(value) => {
            set({ baseUrl: value });
          }}
        />
      </Field>
      <StyleSelect {...{ form, set, busy, zh }} />
      <EndpointEditLimits {...{ form, set, busy, zh }} />
      <ApiKeyField {...{ form, set, busy, zh }} />
      {issue !== null && <ErrorState message={issue} />}
      <div className={styles.toolbar}>
        <button className="btn primary sm" type="button" disabled={busy} onClick={onSave}>
          {busy ? (zh ? "保存中…" : "Saving…") : zh ? "保存" : "Save"}
        </button>
        <button className="btn sm" type="button" disabled={busy} onClick={onCancel}>
          {zh ? "取消" : "Cancel"}
        </button>
      </div>
    </div>
  );
}

function TextValue({
  id,
  value,
  busy,
  mono,
  onChange,
}: {
  id: string;
  value: string;
  busy: boolean;
  mono?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <input
      id={id}
      className={mono === true ? "input mono" : "input"}
      value={value}
      disabled={busy}
      onChange={(event) => {
        onChange(event.target.value);
      }}
    />
  );
}

function StyleSelect({
  form,
  set,
  busy,
  zh,
}: {
  form: EndpointFormState;
  set: (patch: Partial<EndpointFormState>) => void;
  busy: boolean;
  zh: boolean;
}) {
  return (
    <Field label={zh ? "API 风格" : "API style"} htmlFor="ep-style">
      <select
        id="ep-style"
        className="input"
        value={form.apiStyle}
        disabled={busy}
        onChange={(event) => {
          set({ apiStyle: event.target.value as EndpointFormState["apiStyle"] });
        }}
      >
        <option value="chat_completions">chat_completions</option>
        <option value="responses">responses</option>
      </select>
    </Field>
  );
}

function ApiKeyField({
  form,
  set,
  busy,
  zh,
}: {
  form: EndpointFormState;
  set: (patch: Partial<EndpointFormState>) => void;
  busy: boolean;
  zh: boolean;
}) {
  const label = zh ? "API Key（可选，仅写入）" : "API key (optional, write-only)";
  const hint = zh
    ? "留空表示不更换凭据；保存后永不回显。"
    : "Empty keeps the stored key; never echoed.";
  return (
    <Field label={label} htmlFor="ep-key" hint={hint}>
      <input
        id="ep-key"
        className="input mono"
        type="password"
        autoComplete="new-password"
        value={form.apiKey}
        disabled={busy}
        onChange={(event) => {
          set({ apiKey: event.target.value });
        }}
      />
    </Field>
  );
}

const LIMIT_FIELDS = [
  { id: "ep-timeout", key: "timeout", zh: "超时（秒）", en: "Timeout (s)", min: 1 },
  { id: "ep-retries", key: "retries", zh: "重试", en: "Retries", min: 0 },
  { id: "ep-concurrency", key: "concurrency", zh: "并发", en: "Concurrency", min: 1 },
] as const;

function EndpointEditLimits({
  form,
  set,
  busy,
  zh,
}: {
  form: EndpointFormState;
  set: (patch: Partial<EndpointFormState>) => void;
  busy: boolean;
  zh: boolean;
}) {
  return (
    <>
      <label className={styles.notice}>
        <input
          type="checkbox"
          checked={form.enabled}
          disabled={busy}
          onChange={(event) => {
            set({ enabled: event.target.checked });
          }}
        />{" "}
        {zh ? "启用此端点（启用 ≠ 健康）" : "Enabled (enabled ≠ healthy)"}
      </label>
      <div className={styles.toolbar}>
        {LIMIT_FIELDS.map((field) => (
          <NumberField
            key={field.id}
            id={field.id}
            label={zh ? field.zh : field.en}
            min={field.min}
            value={form[field.key]}
            busy={busy}
            onChange={(v) => {
              set({ [field.key]: v });
            }}
          />
        ))}
      </div>
    </>
  );
}

function NumberField({
  id,
  label,
  min,
  value,
  busy,
  onChange,
}: {
  id: string;
  label: string;
  min: number;
  value: string;
  busy: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <Field label={label} htmlFor={id}>
      <input
        id={id}
        className="input"
        type="number"
        min={min}
        value={value}
        disabled={busy}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      />
    </Field>
  );
}
