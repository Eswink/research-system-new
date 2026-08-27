import { useState } from "react";

import { api } from "../../../api/client";
import type { LlmEndpointReadDto } from "../../../api/types";
import { discoverOrFallback } from "../wizardApi";

async function addModels(endpointId: string, modelIds: string[]) {
  for (const modelId of modelIds) {
    await api.createModel({ endpoint_id: endpointId, model_name: modelId, enabled: true });
  }
}

function DiscoveredList({
  models,
  selected,
  onToggle,
  onAdd,
  busy,
}: {
  models: string[];
  selected: string[];
  onToggle: (modelId: string) => void;
  onAdd: () => void;
  busy: boolean;
}) {
  return (
    <div>
      {models.map((modelId) => (
        <label key={modelId}>
          <input
            type="checkbox"
            checked={selected.includes(modelId)}
            onChange={() => {
              onToggle(modelId);
            }}
          />
          {modelId}
        </label>
      ))}
      <button type="button" onClick={onAdd} disabled={busy || selected.length === 0}>
        {busy ? "Adding…" : "Add Selected"}
      </button>
    </div>
  );
}

function useDiscovery(endpointId: string, onAdded: () => void) {
  const [discovered, setDiscovered] = useState<string[] | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const discover = async () => {
    setMessage(null);
    const outcome = await discoverOrFallback(endpointId);
    setDiscovered(outcome.ids);
    if (outcome.error !== null) {
      setMessage(outcome.error);
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
    setMessage(null);
    try {
      await addModels(endpointId, selected);
      setSelected([]);
      setDiscovered(null);
      onAdded();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "add failed");
    } finally {
      setBusy(false);
    }
  };

  return { discovered, selected, busy, message, discover, toggle, addSelected };
}

function DiscoveryControls({
  endpointId,
  disabled,
  onAdded,
}: {
  endpointId: string;
  disabled: boolean;
  onAdded: () => void;
}) {
  const state = useDiscovery(endpointId, onAdded);
  return (
    <fieldset>
      <legend>Discover from relay</legend>
      <button type="button" onClick={() => void state.discover()} disabled={disabled || state.busy}>
        Discover Models
      </button>
      {state.discovered !== null && state.discovered.length > 0 && (
        <DiscoveredList
          models={state.discovered}
          selected={state.selected}
          onToggle={state.toggle}
          onAdd={() => void state.addSelected()}
          busy={state.busy}
        />
      )}
      {state.message !== null && (
        <p className="error" role="alert">
          {state.message}
        </p>
      )}
    </fieldset>
  );
}

async function addManualModel(endpointId: string, modelId: string) {
  await api.createModel({ endpoint_id: endpointId, model_name: modelId, enabled: true });
}

function useManualAdd(endpointId: string, onAdded: () => void) {
  const [modelId, setModelId] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const add = async () => {
    const trimmed = modelId.trim();
    if (trimmed.length === 0) {
      setMessage("model id must not be empty");
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await addManualModel(endpointId, trimmed);
      setModelId("");
      onAdded();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "add failed");
    } finally {
      setBusy(false);
    }
  };

  return { modelId, setModelId, busy, message, add };
}

function ManualAdd({
  endpointId,
  disabled,
  onAdded,
}: {
  endpointId: string;
  disabled: boolean;
  onAdded: () => void;
}) {
  const state = useManualAdd(endpointId, onAdded);
  return (
    <div>
      <label>
        Manual Model ID
        <input
          value={state.modelId}
          onChange={(event) => {
            state.setModelId(event.target.value);
          }}
          placeholder="e.g. gpt-4o-mini"
        />
      </label>
      <button type="button" onClick={() => void state.add()} disabled={disabled || state.busy}>
        {state.busy ? "Adding…" : "Add Model"}
      </button>
      {state.message !== null && (
        <p className="error" role="alert">
          {state.message}
        </p>
      )}
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
  const onAdded = () => undefined;
  return (
    <div data-testid="wizard-models-step">
      <p>
        Configure models on endpoint <strong>{endpoint.name}</strong> — discover from the
        relay or enter a model id manually.
      </p>
      <DiscoveryControls endpointId={endpoint.id} disabled={busy} onAdded={onAdded} />
      <ManualAdd endpointId={endpoint.id} disabled={busy} onAdded={onAdded} />
      {error !== null && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <button type="button" onClick={onProbe} disabled={busy}>
        {busy ? "Probing…" : "Probe First Model"}
      </button>
    </div>
  );
}
