import type { CostForecastDto, ForecastLineDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { forecastRemainingText } from "./forecastPresentation";

/** 预留-消耗预测表：只覆盖已预留额度；UNKNOWN/NO_DATA 不渲染为 0。 */
export function ForecastTable({ view }: { view: CostForecastDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <PanelSection
      title={zh ? "预留-消耗预测" : "Reserved vs consumed forecast"}
      count={view.lines.length}
      extra={
        <Chip tone="unknown" title={view.scope_note}>
          {`${view.forecast_scope} · ${view.attribution}`}
        </Chip>
      }
    >
      <Table
        columns={forecastColumns(zh)}
        rows={view.lines}
        rowKey={(line) => `${line.resource_type}:${line.unit}`}
        ariaLabel={zh ? "预留-消耗预测" : "Reserved vs consumed forecast"}
        empty={
          <EmptyState message={zh ? "本运行尚无预留或用量记录" : "No reservations or usage"} />
        }
      />
      <p className="muted">{forecastNote(view)}</p>
    </PanelSection>
  );
}

/** 预测口径说明：未归属预留条数 > 0 时显式说明其未计入（不静默丢弃）。 */
function forecastNote(view: CostForecastDto): string {
  if (view.unattributed_reserved === 0) return view.scope_note;
  return [
    view.scope_note,
    `${String(view.unattributed_reserved)} un-attributed reservation(s) excluded`,
  ].join(" · ");
}

function forecastColumns(zh: boolean): Column<ForecastLineDto>[] {
  return [
    { key: "resource", header: zh ? "资源" : "Resource", render: (line) => line.resource_type },
    { key: "unit", header: zh ? "单位" : "Unit", render: (line) => line.unit },
    { key: "reserved", header: zh ? "已预留" : "Reserved", render: (line) => String(line.reserved) },
    {
      key: "consumed",
      header: zh ? "已消耗" : "Consumed",
      render: (line) =>
        line.consumed === null
          ? `— (${line.data_status})`
          : `${String(line.consumed)} ${line.unit}`,
    },
    {
      key: "remaining",
      header: zh ? "剩余" : "Remaining",
      render: (line) => forecastRemainingText(line.remaining, line.unit, zh),
    },
    {
      key: "status",
      header: zh ? "计量状态" : "Metering state",
      render: (line) => (
        <Chip tone={line.data_status === "KNOWN" ? "neutral" : "unknown"}>{line.data_status}</Chip>
      ),
    },
  ];
}
