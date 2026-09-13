import { api } from "../../api/client";
import type { CompatibilityViewDto, ModelReadDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { ErrorState, LoadingState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import { ModelDetails } from "./ModelDetails";
import { ModelDeleteAction } from "./ModelDeleteAction";
import { ModelEditForm } from "./ModelEditForm";

/** 选中模型的详情刷新（GET /models/{id}）、编辑（PATCH + If-Match）、删除与兼容性视图。 */
export function ModelInspector({
  model,
  onChanged,
  onDeleted,
}: {
  model: ModelReadDto;
  onChanged: () => void;
  onDeleted: () => void;
}) {
  const fresh = useResource(`model:${model.id}`, () => api.getModel(model.id));
  const view = fresh.data ?? model;
  return (
    <div className={styles.page} data-testid="model-inspector">
      <ModelDetails model={view} />
      <ModelEditForm
        model={view}
        onSaved={() => {
          onChanged();
          fresh.reload();
        }}
      />
      <ModelDeleteAction
        model={view}
        onDeleted={() => {
          onChanged();
          onDeleted();
        }}
      />
      <CompatibilityPanel modelId={view.id} />
    </div>
  );
}

function hintChip(hint: boolean | null, zh: boolean): {
  tone: "success" | "danger" | "neutral";
  text: string;
} {
  if (hint === true) {
    return { tone: "success", text: zh ? "端点健康提示：可用" : "Endpoint health hint: available" };
  }
  if (hint === false) {
    return { tone: "danger", text: zh ? "端点健康提示：不可用" : "Endpoint health hint: unavailable" };
  }
  return { tone: "neutral", text: zh ? "端点健康：未知（未探测）" : "Endpoint health: unknown" };
}

function CompatibilityPanel({ modelId }: { modelId: string }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const compat = useResource(`compatibility:${modelId}`, () => api.getCompatibility(modelId));
  return (
    <PanelSection
      title={zh ? "兼容性视图" : "Compatibility view"}
      extra={<RefreshButton busy={compat.phase === "loading"} onReload={compat.reload} zh={zh} />}
    >
      <div data-testid="model-compatibility">
        {compat.phase === "loading" && <LoadingState message={zh ? "加载兼容性…" : "Loading…"} />}
        {compat.error !== null && <ErrorState message={compat.error} />}
        {compat.data !== null && <CompatView view={compat.data} zh={zh} />}
      </div>
    </PanelSection>
  );
}

function RefreshButton({
  busy,
  onReload,
  zh,
}: {
  busy: boolean;
  onReload: () => void;
  zh: boolean;
}) {
  return (
    <button className="btn sm ghost" type="button" disabled={busy} onClick={onReload}>
      {zh ? "刷新" : "Refresh"}
    </button>
  );
}

function CompatView({ view, zh }: { view: CompatibilityViewDto; zh: boolean }) {
  const hint = hintChip(view.endpoint_healthy_hint, zh);
  const requirements =
    view.hard_capability_requirements.length > 0
      ? view.hard_capability_requirements.join(", ")
      : zh
        ? "引用本模型的 role/profile 未声明硬要求"
        : "no role/profile referencing this model declares hard requirements";
  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <Chip tone={hint.tone}>{hint.text}</Chip>
        <span className="mono">{view.endpoint_id}</span>
      </div>
      <KeyValueList fields={[{ label: zh ? "硬能力要求" : "Hard requirements", value: requirements }]} />
    </div>
  );
}
