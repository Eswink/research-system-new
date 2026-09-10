import { api } from "../../api/client";
import type {
  CostAmountStatus,
  CostDailyViewDto,
  CostDayPointDto,
} from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { LineSeries } from "../../components/charts/LineSeries";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

const MEASURED: CostAmountStatus[] = ["ACTUAL", "ESTIMATED"];

/** 跨 run 成本日序列（GET /cost/daily；只画有数据的日子，绝不插值/预测）。 */
export function DailyCostPanel() {
  const { language } = useI18n();
  const zh = language === "zh";
  const series = useResource("cost-daily", () => api.dailyCost());
  return (
    <PanelSection
      title={zh ? "成本日序列" : "Daily cost series"}
      extra={
        <button
          className="btn sm ghost"
          type="button"
          disabled={series.phase === "loading"}
          onClick={series.reload}
        >
          {zh ? "刷新" : "Refresh"}
        </button>
      }
    >
      <ResourceBoundary state={series}>
        {series.data !== null && <DailySeriesBody data={series.data} zh={zh} />}
      </ResourceBoundary>
    </PanelSection>
  );
}

function DailySeriesBody({ data, zh }: { data: CostDailyViewDto; zh: boolean }) {
  if (data.days.length === 0) {
    return <EmptyState message={zh ? "账本暂无可归属的成本数据" : "No ledger entries yet"} />;
  }
  const measured = data.days.filter((day) => MEASURED.includes(day.total.status));
  const unmeasured = data.days.filter((day) => !MEASURED.includes(day.total.status));
  return (
    <div className={styles.page} data-testid="daily-cost-series">
      {measured.length > 0 && (
        <LineSeries
          data={[
            {
              label: zh ? "成本（最小货币单位）" : "cost (minor units)",
              values: measured.map((day) => day.total.minor_units ?? 0),
            },
          ]}
          xLabels={measured.map((day) => day.date.slice(5))}
        />
      )}
      {unmeasured.length > 0 && <UnmeasuredDays days={unmeasured} zh={zh} />}
      {data.truncated && (
        <p className={styles.notice}>
          {zh ? "序列已截断（仅显示最早 400 天）。" : "Series truncated to the earliest 400 days."}
        </p>
      )}
      {data.attribution_note !== null && <p className={styles.notice}>{data.attribution_note}</p>}
    </div>
  );
}

function UnmeasuredDays({ days, zh }: { days: CostDayPointDto[]; zh: boolean }) {
  return (
    <ul className={styles.list}>
      {days.map((day) => (
        <li key={day.date} className={styles.notice}>
          <span className="mono">{day.date}</span>{" "}
          <Chip tone={day.total.status === "ZERO" ? "neutral" : "warn"}>
            {day.total.status}
          </Chip>
          {day.mixed_pricing && (
            <span>{zh ? "跨定价表（未求和）" : "mixed pricing tables (not summed)"}</span>
          )}
          {day.groups.map((group) => (
            <span key={group.pricing_digest} className="mono">
              {" "}
              · {group.pricing_version}
              {group.pricing_frozen ? "" : zh ? "（未冻结）" : " (unfrozen)"}
            </span>
          ))}
        </li>
      ))}
    </ul>
  );
}
