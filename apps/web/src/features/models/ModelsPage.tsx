import { useState, type Dispatch, type SetStateAction } from "react";
import { api } from "../../api/client";
import type { ModelReadDto, ProbeResultDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { ErrorState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { ModelCatalogTable } from "./ModelCatalogTable";
import { ProbeSummary } from "./ModelDetails";
import { ModelInspector } from "./ModelInspector";
import { useModelProbe } from "./useModelProbe";

export function ModelsPage() {
  const { language } = useI18n();
  const models = useResource("model-registry", () => api.listModels());
  const zh = language === "zh";
  return (
    <section data-testid="models-page" className={styles.page}>
      <PageHeader
        title={zh ? "模型注册表" : "Model registry"}
        kicker="LIBRARY / MODELS"
        description={
          zh
            ? "模型身份、版本与能力来源。探测必须显式确认，不把配置状态当成执行结果。"
            : [
                "Model identities, versions and capability provenance. Probes require ",
                "confirmation; configuration is not execution.",
              ].join("")
        }
        actions={
          <button
            className="btn"
            type="button"
            onClick={models.reload}
            disabled={models.phase === "loading"}
          >
            {zh ? "刷新模型" : "Refresh models"}
          </button>
        }
      />
      <ResourceBoundary state={models}>
        {models.data !== null && <ModelCatalog models={models.data} onRefresh={models.reload} />}
      </ResourceBoundary>
    </section>
  );
}

function ModelCatalog({ models, onRefresh }: { models: ModelReadDto[]; onRefresh: () => void }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [selectedId, setSelectedId] = useState("");
  const [query, setQuery] = useState("");
  const [confirm, setConfirm] = useState<ModelReadDto | null>(null);
  const probe = useModelProbe(onRefresh);
  const selected = models.find((model) => model.id === selectedId) ?? models[0];
  const filtered = models.filter((model) =>
    `${model.model_name} ${model.display_name ?? ""} ${model.endpoint_id}`
      .toLocaleLowerCase()
      .includes(query.trim().toLocaleLowerCase()),
  );
  return (
    <ModelsPagePage
      {...{
        query,
        zh,
        setQuery,
        filtered,
        models,
        selected,
        setSelectedId,
        setConfirm,
        probe,
        confirm,
        onRefresh,
      }}
    />
  );
}

interface ModelsPagePageProps {
  query: string;
  zh: boolean;
  setQuery: Dispatch<SetStateAction<string>>;
  filtered: ModelReadDto[];
  models: ModelReadDto[];
  selected: ModelReadDto | undefined;
  setSelectedId: Dispatch<SetStateAction<string>>;
  setConfirm: Dispatch<SetStateAction<ModelReadDto | null>>;
  probe: {
    result: ProbeResultDto | null;
    error: string | null;
    probingId: string | null;
    probe: (modelId: string) => Promise<void>;
  };
  confirm: ModelReadDto | null;
  onRefresh: () => void;
}

function ModelsPagePage({
  query,
  zh,
  setQuery,
  filtered,
  models,
  selected,
  setSelectedId,
  setConfirm,
  probe,
  confirm,
  onRefresh,
}: ModelsPagePageProps) {
  return (
    <div className={styles.page}>
      <ModelsPageToolbar {...{ query, zh, setQuery, filtered, models }} />
      <ModelCatalogBody
        models={filtered}
        selected={selected}
        onSelect={setSelectedId}
        onProbe={setConfirm}
        busy={probe.probingId !== null}
        onChanged={onRefresh}
      />
      {probe.error !== null && <ErrorState message={probe.error} />}
      {probe.result !== null && <ProbeSummary probe={probe.result} />}
      <ProbeConfirmation
        model={confirm}
        busy={probe.probingId !== null}
        onCancel={() => {
          setConfirm(null);
        }}
        onConfirm={() => {
          if (confirm !== null) void probe.probe(confirm.id);
          setConfirm(null);
        }}
      />
    </div>
  );
}

interface ModelsPageToolbarProps {
  query: string;
  zh: boolean;
  setQuery: Dispatch<SetStateAction<string>>;
  filtered: ModelReadDto[];
  models: ModelReadDto[];
}

function ModelsPageToolbar({ query, zh, setQuery, filtered, models }: ModelsPageToolbarProps) {
  return (
    <div className={styles.toolbar}>
      <input
        className={`input ${styles.search ?? ""}`}
        type="search"
        value={query}
        aria-label={zh ? "搜索模型" : "Search models"}
        placeholder={zh ? "搜索模型、端点…" : "Search model or endpoint…"}
        onChange={(event) => {
          setQuery(event.target.value);
        }}
      />
      <Chip>{`${String(filtered.length)} / ${String(models.length)}`}</Chip>
    </div>
  );
}

function ModelCatalogBody({
  models,
  selected,
  onSelect,
  onProbe,
  busy,
  onChanged,
}: {
  models: ModelReadDto[];
  selected: ModelReadDto | undefined;
  onSelect: (id: string) => void;
  onProbe: (model: ModelReadDto) => void;
  busy: boolean;
  onChanged: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  return <ModelsPageContent {...{ zh, models, selected, onSelect, busy, onProbe, onChanged }} />;
}

interface ModelsPageContentProps {
  zh: boolean;
  models: ModelReadDto[];
  selected: ModelReadDto | undefined;
  onSelect: (id: string) => void;
  busy: boolean;
  onProbe: (model: ModelReadDto) => void;
  onChanged: () => void;
}

function ModelsPageContent({
  zh,
  models,
  selected,
  onSelect,
  busy,
  onProbe,
  onChanged,
}: ModelsPageContentProps) {
  return (
    <>
      <ModelCatalogTable {...{ zh, models, selected, onSelect }} />
      {selected !== undefined && (
        <div className={styles.split}>
          <ModelInspector key={selected.id} model={selected} onChanged={onChanged} />
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>{zh ? "能力探测" : "Capability probe"}</h2>
            <p>
              {zh
                ? "对选中模型执行真实请求，可能产生费用。未探测不等于失败。"
                : [
                    "Sends real requests to the selected model and may incur cost. Not probed ",
                    "does not mean failed.",
                  ].join("")}
            </p>
            <p className="mono">{selected.model_name}</p>
            <button
              className="btn"
              type="button"
              disabled={busy || !selected.enabled}
              onClick={() => {
                onProbe(selected);
              }}
            >
              {busy ? "Probing…" : "Probe"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function ProbeConfirmation({
  model,
  busy,
  onConfirm,
  onCancel,
}: {
  model: ModelReadDto | null;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <ConfirmDialog
      open={model !== null}
      title={zh ? "确认执行真实模型探测" : "Confirm real model probe"}
      consequence={
        <p>
          {model?.model_name} ·{" "}
          {zh
            ? "将向此模型的已配置端点发送能力探测请求，可能计入实际费用。离开页面不代表取消后端请求。"
            : [
                "Capability requests will be sent to this model's configured endpoint and ",
                "may incur actual cost. Navigation does not cancel the backend request.",
              ].join("")}
        </p>
      }
      busy={busy}
      confirmLabel={zh ? "执行探测" : "Run probe"}
      cancelLabel={zh ? "取消" : "Cancel"}
      onConfirm={onConfirm}
      onCancel={onCancel}
    />
  );
}
