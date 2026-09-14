import { api } from "../../api/client";
import { Table } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { OpsViewPage } from "../ops-view/OpsViewPage";
import { dataHealthColumns } from "../ops-view/opsViewColumns";

/** 数据健康（EC-03 第二批）：既有状态的可观测计数/校验；无聚合质量报告 API。 */
export function DataHealthPage() {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <OpsViewPage
      testid="data-health-page"
      title={zh ? "数据健康" : "Data health"}
      kicker="OPS / DATA HEALTH"
      description={
        zh
          ? "由既有状态聚合的可观测指标（端点健康计数、数据集目录计数、artifact 抽样校验）。无聚合质量报告 API。"
          : [
              "Observable metrics aggregated from existing state (endpoint health counts, ",
              "dataset catalog counts, sampled artifact verification). No aggregate report API.",
            ].join("")
      }
      fetch={() => api.opsDataHealth()}
      isEmpty={(data) => data.metrics.length === 0}
    >
      {(data) => (
        <Table
          columns={dataHealthColumns(zh)}
          rows={data.metrics}
          rowKey={(row) => row.metric}
          ariaLabel={zh ? "数据健康指标" : "Data health metrics"}
        />
      )}
    </OpsViewPage>
  );
}
