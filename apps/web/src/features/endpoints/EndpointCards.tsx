import type { LlmEndpointReadDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

/** 端点卡片网格（详情入口）。空结果只表达当前过滤，不伪造总数。 */
export function EndpointCards({
  endpoints,
  onSelect,
}: {
  endpoints: LlmEndpointReadDto[];
  onSelect: (id: string) => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  if (endpoints.length === 0) {
    return (
      <div data-testid="endpoints-empty">
        <EmptyState message={zh ? "没有匹配的已配置端点" : "No matching configured endpoints"} />
      </div>
    );
  }
  return (
    <div className={styles.cards}>
      {endpoints.map((endpoint) => (
        <article key={endpoint.id} className={styles.card} data-testid="endpoint-card">
          <div className={styles.cardHead}>
            <h2 className={styles.cardTitle}>{endpoint.name}</h2>
            <Chip tone={endpoint.enabled ? "accent" : "neutral"}>
              {endpoint.enabled ? (zh ? "已启用" : "Enabled") : zh ? "已停用" : "Disabled"}
            </Chip>
          </div>
          <KeyValueList
            fields={[
              { label: "Base URL", value: endpoint.base_url },
              { label: zh ? "协议" : "Protocol", value: endpoint.api_style },
              { label: zh ? "凭据状态" : "Credential", value: endpoint.credential },
            ]}
          />
          <button
            type="button"
            className="btn sm"
            onClick={() => {
              onSelect(endpoint.id);
            }}
          >
            {zh ? "查看配置" : "View configuration"}
          </button>
        </article>
      ))}
    </div>
  );
}
