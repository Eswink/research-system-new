import { useEffect, useState } from "react";

import { api } from "../../api/client";
import type { ModelReadDto, ProbeResultDto } from "../../api/types";

function ProbeSummary({ probe }: { probe: ProbeResultDto }) {
  const reproducibility = probe.provider_fingerprint_available
    ? "Configuration reproducible / provider fingerprint available"
    : "Configuration reproducible / provider fingerprint unavailable";
  return (
    <div data-testid="probe-summary">
      <p>
        ok: {String(probe.ok)} · model: {probe.returned_model_name ?? "n/a"} ·{" "}
        {probe.error_category ?? "no error category"}
      </p>
      <p>
        capabilities: {probe.observed_capabilities.join(", ") || "none"} · {reproducibility}
      </p>
      {probe.capability_failures.length > 0 && (
        <ul>
          {probe.capability_failures.map((failure) => (
            <li key={failure.capability}>
              [{failure.capability}] {failure.error_category ?? "unknown"} ·{" "}
              {failure.error_message_redacted ?? "no redacted detail"}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ModelRow({
  model,
  onProbe,
  probing,
}: {
  model: ModelReadDto;
  onProbe: () => void;
  probing: boolean;
}) {
  return (
    <li data-testid="model-row">
      <strong>{model.display_name ?? model.model_name}</strong> · {model.model_name} ·{" "}
      {model.endpoint_id.slice(0, 8)} · {model.enabled ? "enabled" : "disabled"}
      <button type="button" onClick={onProbe} disabled={probing}>
        {probing ? "Probing…" : "Probe"}
      </button>
    </li>
  );
}

function ModelList({
  models,
  probingId,
  onProbe,
}: {
  models: ModelReadDto[];
  probingId: string | null;
  onProbe: (modelId: string) => void;
}) {
  if (models.length === 0) {
    return <p>No models configured — use the wizard or the Models step of another endpoint.</p>;
  }
  return (
    <ul>
      {models.map((model) => (
        <ModelRow
          key={model.id}
          model={model}
          probing={probingId === model.id}
          onProbe={() => {
            onProbe(model.id);
          }}
        />
      ))}
    </ul>
  );
}

/**
 * Models / Probe 页面（WP-S1）：列出全部模型；逐项 probe，结果如实展示
 * （失败态含 error_category / capability failures），
 * 不与 wizard 内嵌步骤共用视觉假成功。
 */
export function ModelsPage() {
  const [models, setModels] = useState<ModelReadDto[]>([]);
  const [probeResult, setProbeResult] = useState<ProbeResultDto | null>(null);
  const [probingId, setProbingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setModels(await api.listModels());
    } catch (err) {
      setError(err instanceof Error ? err.message : "models load failed");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const probe = async (modelId: string) => {
    setProbingId(modelId);
    setError(null);
    try {
      setProbeResult(await api.probeModel(modelId));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "probe failed");
    } finally {
      setProbingId(null);
    }
  };

  return (
    <section data-testid="models-page">
      <h2>Models &amp; Probe</h2>
      {error !== null && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <ModelList models={models} probingId={probingId} onProbe={(id) => void probe(id)} />
      {probeResult !== null && <ProbeSummary probe={probeResult} />}
    </section>
  );
}
