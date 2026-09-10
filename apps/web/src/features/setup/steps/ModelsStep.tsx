import { useState } from "react";

import { api } from "../../../api/client";
import { cx } from "../../../components/cx";
import { Button } from "../../../components/Button";
import { Field } from "../../../components/Field";
import { useI18n } from "../../../i18n/useI18n";
import type { LlmEndpointReadDto } from "../../../api/types";
import { discoverOrFallback } from "../wizardApi";
import { ErrorRow } from "./ErrorRow";
import styles from "./steps.module.css";

interface Issue {
  message: string;
  detail: string | null;
}

function IssueRow({ issue }: { issue: Issue }) {
  return issue.detail === null ? (
    <ErrorRow message={issue.message} />
  ) : (
    <ErrorRow message={issue.message} detail={issue.detail} />
  );
}

async function addModels(endpointId: string, modelIds: string[]) {
  for (const modelId of modelIds) {
    await api.createModel({ endpoint_id: endpointId, model_name: modelId, enabled: true });
  }
}

function DiscoveredList({
  models,
  selected,
  onToggle,
}: {
  models: string[];
  selected: string[];
  onToggle: (modelId: string) => void;
}) {
  return (
    <div className={styles.list}>
      {models.map((modelId) => (
        <label key={modelId} className={styles.item}>
          <input
            type="checkbox"
            checked={selected.includes(modelId)}
            onChange={() => {
              onToggle(modelId);
            }}
          />
          <span className="mono">{modelId}</span>
        </label>
      ))}
    </div>
  );
}

function useDiscovery(endpointId: string) {
  const { t } = useI18n();
  const [discovered, setDiscovered] = useState<string[] | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<Issue | null>(null);

  const discover = async () => {
    setIssue(null);
    const outcome = await discoverOrFallback(endpointId);
    setDiscovered(outcome.ids);
    if (outcome.error !== null) {
      setIssue({ message: t("setup.err.discover"), detail: outcome.error });
    }
  };

  const toggle = (modelId: string) => {
    setSelected((current) =>
      current.includes(modelId)
        ? current.filter((item) => item !== modelId)
        : [...current, modelId],
    );
  };

  const addSelected = async () => {
    setBusy(true);
    setIssue(null);
    try {
      await addModels(endpointId, selected);
      setSelected([]);
      setDiscovered(null);
    } catch (err) {
      setIssue({
        message: t("setup.err.add"),
        detail: err instanceof Error ? err.message : null,
      });
    } finally {
      setBusy(false);
    }
  };

  return { discovered, selected, busy, issue, discover, toggle, addSelected };
}

function DiscoveryControls({ endpointId, disabled }: { endpointId: string; disabled: boolean }) {
  const { t } = useI18n();
  const state = useDiscovery(endpointId);
  return (
    <div className={styles.subgroup}>
      <div className={styles.actions}>
        <Button icon="search" onClick={() => void state.discover()} disabled={disabled}>
          {t("setup.models.discover")}
        </Button>
      </div>
      {state.discovered !== null && state.discovered.length > 0 && (
        <>
          <DiscoveredList
            models={state.discovered}
            selected={state.selected}
            onToggle={state.toggle}
          />
          <div className={styles.actions}>
            <Button
              variant="primary"
              onClick={() => void state.addSelected()}
              disabled={disabled || state.busy || state.selected.length === 0}
            >
              {state.busy ? t("setup.adding") : t("setup.models.addSelected")}
            </Button>
          </div>
        </>
      )}
      {state.issue !== null && <IssueRow issue={state.issue} />}
    </div>
  );
}

function useManualAdd(endpointId: string) {
  const { t } = useI18n();
  const [modelId, setModelId] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<Issue | null>(null);

  const add = async () => {
    const trimmed = modelId.trim();
    if (trimmed.length === 0) {
      setIssue({ message: t("setup.err.emptyModelId"), detail: null });
      return;
    }
    setBusy(true);
    setIssue(null);
    try {
      await api.createModel({ endpoint_id: endpointId, model_name: trimmed, enabled: true });
      setModelId("");
    } catch (err) {
      setIssue({
        message: t("setup.err.add"),
        detail: err instanceof Error ? err.message : null,
      });
    } finally {
      setBusy(false);
    }
  };

  return { modelId, setModelId, busy, issue, add };
}

function ManualAdd({ endpointId, disabled }: { endpointId: string; disabled: boolean }) {
  const { t } = useI18n();
  const state = useManualAdd(endpointId);
  const id = "manual-model-id";
  return (
    <div className={styles.subgroup}>
      <Field label={t("setup.models.manual")} htmlFor={id}>
        <input
          id={id}
          className="input mono"
          value={state.modelId}
          onChange={(event) => {
            state.setModelId(event.target.value);
          }}
          placeholder="gpt-4o-mini"
        />
      </Field>
      <div className={styles.actions}>
        <Button onClick={() => void state.add()} disabled={disabled || state.busy}>
          {state.busy ? t("setup.adding") : t("setup.models.add")}
        </Button>
      </div>
      {state.issue !== null && <IssueRow issue={state.issue} />}
    </div>
  );
}

/**
 * Models 步骤（M13-R1 WP-B2）：真实 discovery / 手动 Model ID 添加 /
 * probe 入口。discovery 失败降级为手动输入（不抛未捕获异常）。
 */
export function ModelsStep({
  endpoint,
  busy,
  error,
  onProbe,
}: {
  endpoint: LlmEndpointReadDto;
  busy: boolean;
  error: string | null;
  onProbe: () => void;
}) {
  const { t } = useI18n();
  return (
    <div className={cx("panel", styles.panel)} data-testid="wizard-models-step">
      <div className={styles.head}>
        <div className={styles.title}>{t("setup.models.title")}</div>
        <div className={styles.desc}>
          {t("setup.models.desc")} <span className="mono">{endpoint.name}</span>
        </div>
      </div>
      <DiscoveryControls endpointId={endpoint.id} disabled={busy} />
      <hr className="hr" />
      <ManualAdd endpointId={endpoint.id} disabled={busy} />
      {error !== null && <ErrorRow message={error} />}
      <div className={styles.actions}>
        <Button variant="primary" icon="flask" onClick={onProbe} disabled={busy}>
          {busy ? t("setup.probing") : t("setup.test.probe")}
        </Button>
      </div>
    </div>
  );
}
