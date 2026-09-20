import type { ModelReadDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { Table, type Column } from "../../components/Table";

interface ModelCatalogTableProps {
  zh: boolean;
  models: ModelReadDto[];
  selected: ModelReadDto | undefined;
  onSelect: (id: string) => void;
}

export function ModelCatalogTable(props: ModelCatalogTableProps) {
  return (
    <PanelSection title={props.zh ? "已注册模型" : "Registered models"}>
      <Table
        columns={modelColumns(props.zh)}
        rows={props.models}
        rowKey={(model) => model.id}
        selectable
        selectedKey={props.selected?.id ?? ""}
        onSelectRow={(model) => {
          props.onSelect(model.id);
        }}
        ariaLabel={props.zh ? "模型注册表" : "Model registry"}
        empty={
          <EmptyState
            message={
              props.zh
                ? "没有匹配模型，请通过接入向导注册"
                : "No matching models; register through setup"
            }
          />
        }
      />
    </PanelSection>
  );
}

function modelColumns(zh: boolean): Column<ModelReadDto>[] {
  return [
    {
      key: "name",
      header: zh ? "模型" : "Model",
      sortable: true,
      sortValue: (model) => model.model_name,
      render: (model) => (
        <span data-testid="model-row">{model.display_name ?? model.model_name}</span>
      ),
    },
    {
      key: "identifier",
      header: "Model ID",
      render: (model) => <span className="mono">{model.model_name}</span>,
    },
    {
      key: "endpoint",
      header: "Endpoint",
      render: (model) => <span className="mono">{model.endpoint_id}</span>,
    },
    {
      key: "state",
      header: zh ? "配置状态" : "Configuration",
      render: (model) => (
        <Chip tone={model.enabled ? "accent" : "neutral"}>
          {model.enabled ? "ENABLED" : "DISABLED"}
        </Chip>
      ),
    },
    {
      key: "capabilities",
      header: zh ? "能力声明" : "Assertions",
      sortable: true,
      sortValue: (model) => Object.keys(model.capabilities).length,
      render: (model) => Object.keys(model.capabilities).length,
    },
    {
      key: "declared",
      header: zh ? "参数声明" : "Declared",
      render: (model) => <DeclaredParametersCell model={model} />,
    },
    { key: "version", header: zh ? "版本" : "Version", render: (model) => model.version },
  ];
}

/** 参数声明列：未声明渲染 "—"（不推断默认值），见 ModelDetails 的说明文案。 */
function DeclaredParametersCell({ model }: { model: ModelReadDto }) {
  const parts: string[] = [];
  if (model.context_window_tokens !== null) {
    parts.push(`${String(model.context_window_tokens)} tok`);
  }
  if (model.thinking_intensity !== null) parts.push(model.thinking_intensity);
  return (
    <span data-testid="model-row-declared" className="mono">
      {parts.length > 0 ? parts.join(" · ") : "—"}
    </span>
  );
}
