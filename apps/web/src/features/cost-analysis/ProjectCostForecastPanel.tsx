import { api } from "../../api/client";
import type { ProjectCostDayDto, ProjectCostForecastDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { EmptyState } from "../../components/States";
import { Table } from "../../components/Table";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

/**
 * 项目级成本预测（G12 / GET /projects/{id}/cost-forecast）。
 *
 * 页面只 render 后端口径：外推方法、样本量、排除项与原因、归属注记全部来自响应；
 * 样本为空或跨币种时后端不给金额，这里如实显示原因而不是画一条 0 值曲线。
 */
export function ProjectCostForecastPanel() {
  const { language } = useI18n();
  const zh = language === "zh";
  const forecast = useResource("project-cost-forecast", () => api.projectCostForecast(undefined));
  return (
    <PanelSection
      title={zh ? "项目级成本预测" : "Project cost forecast"}
      extra={
        <button
          className="btn sm ghost"
          type="button"
          disabled={forecast.phase === "loading"}
          onClick={forecast.reload}
        >
          {zh ? "刷新" : "Refresh"}
        </button>
      }
    >
      <ResourceBoundary state={forecast}>
        {forecast.data !== null && <ForecastBody data={forecast.data} zh={zh} />}
      </ResourceBoundary>
    </PanelSection>
  );
}

function ForecastBody({ data, zh }: { data: ProjectCostForecastDto; zh: boolean }) {
  return (
    <div className={styles.cards} data-testid="project-cost-forecast">
      <Summary data={data} zh={zh} />
      {data.days.length === 0 ? (
        <div className={styles.card}>
          <EmptyState
            message={zh ? "项目内暂无可归属的成本数据" : "No attributable ledger entries yet"}
          />
        </div>
      ) : (
        <div className={styles.card}>
          <Table
            columns={dayColumns(zh)}
            rows={data.days}
            rowKey={(row) => row.date}
            ariaLabel={zh ? "项目成本日序列" : "Project cost days"}
          />
        </div>
      )}
    </div>
  );
}

function Summary({ data, zh }: { data: ProjectCostForecastDto; zh: boolean }) {
  const projection = data.projection;
  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>{zh ? "外推口径" : "Projection"}</h3>
      <p className={styles.metadata}>{sampleLine(data, zh)}</p>
      <p className={styles.metadata} data-testid="project-cost-forecast-amount">
        {amountLine(data, zh)}
      </p>
      <p className={styles.metadata}>{projection.note}</p>
      {data.attribution_note !== null && <p className={styles.notice}>{data.attribution_note}</p>}
      {data.truncated && (
        <p className={styles.notice}>
          {zh ? "序列已截断（仅显示最早 400 天）。" : "Series truncated to the earliest 400 days."}
        </p>
      )}
      <p className={styles.metadata}>{data.scope_note}</p>
    </div>
  );
}

function sampleLine(data: ProjectCostForecastDto, zh: boolean): string {
  const { method, horizon_days: horizon, valued_days: valued, excluded_days: excluded } =
    data.projection;
  const parts = [
    method,
    zh ? `视野 ${String(horizon)} 天` : `horizon ${String(horizon)} days`,
    zh ? `样本天数 ${String(valued)}` : `valued ${String(valued)}`,
    zh ? `排除 ${String(excluded)}` : `excluded ${String(excluded)}`,
  ];
  return parts.join(" · ");
}

/** 后端不给金额时如实显示原因（样本为空 / 跨币种），绝不画成 0。 */
function amountLine(data: ProjectCostForecastDto, zh: boolean): string {
  const projection = data.projection;
  if (projection.projected_minor === null) {
    const reason = projection.unavailable_reason ?? (zh ? "样本不足" : "insufficient sample");
    return `${zh ? "不给金额" : "no amount"}：${reason}`;
  }
  const observed = String(projection.observed_minor ?? 0);
  const currency = projection.currency ?? "";
  const projected = String(projection.projected_minor);
  if (zh) {
    return `已计价合计 ${observed} ${currency}（${projection.observed_status}）→ 外推 ${projected}`;
  }
  return `valued ${observed} ${currency} (${projection.observed_status}) → projected ${projected}`;
}

function dayColumns(zh: boolean) {
  return [
    {
      key: "date",
      header: zh ? "日期" : "Date",
      width: "120px",
      render: (row: ProjectCostDayDto) => row.date,
    },
    {
      key: "amount",
      header: zh ? "金额（最小单位）" : "Amount (minor)",
      width: "150px",
      render: (row: ProjectCostDayDto) =>
        row.amount.minor_units === null ? "—" : String(row.amount.minor_units),
    },
    {
      key: "status",
      header: zh ? "状态" : "Status",
      width: "160px",
      render: (row: ProjectCostDayDto) => (
        <Chip tone={row.included_in_projection ? "accent" : "warn"}>{row.amount.status}</Chip>
      ),
    },
    {
      key: "included",
      header: zh ? "是否进样本" : "In sample",
      width: "200px",
      render: (row: ProjectCostDayDto) =>
        row.included_in_projection
          ? zh
            ? "是"
            : "yes"
          : (row.exclusion_reason ?? (zh ? "排除" : "excluded")),
    },
  ];
}
