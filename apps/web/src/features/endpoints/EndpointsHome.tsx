import { useState, type Dispatch, type SetStateAction } from "react";
import type { LlmEndpointReadDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { Drawer } from "../../components/Drawer";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/** Endpoint configuration is not a health check. Credentials are never returned by this view. */
export function EndpointsHome({
  endpoints,
  onAddRelay,
}: {
  endpoints: LlmEndpointReadDto[];
  onAddRelay: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = endpoints.find((endpoint) => endpoint.id === selectedId);
  const needle = query.trim().toLocaleLowerCase();
  const filtered = endpoints.filter((endpoint) =>
    `${endpoint.name} ${endpoint.base_url} ${endpoint.api_style}`
      .toLocaleLowerCase()
      .includes(needle),
  );
  return (
    <EndpointsHomesection
      {...{ zh, onAddRelay, query, setQuery, filtered, endpoints, setSelectedId, selected }}
    />
  );
}

interface EndpointsHomesectionProps {
  zh: boolean;
  onAddRelay: () => void;
  query: string;
  setQuery: Dispatch<SetStateAction<string>>;
  filtered: LlmEndpointReadDto[];
  endpoints: LlmEndpointReadDto[];
  setSelectedId: Dispatch<SetStateAction<string | null>>;
  selected: LlmEndpointReadDto | undefined;
}

function EndpointsHomesection({
  zh,
  onAddRelay,
  query,
  setQuery,
  filtered,
  endpoints,
  setSelectedId,
  selected,
}: EndpointsHomesectionProps) {
  return (
    <section className={styles.page} data-testid="endpoints-home">
      <EndpointsHomePageHeader {...{ zh, onAddRelay }} />
      <div className={styles.toolbar}>
        <input
          className={`input ${styles.search ?? ""}`}
          type="search"
          value={query}
          aria-label={zh ? "搜索端点" : "Search endpoints"}
          placeholder={zh ? "搜索名称、地址或协议…" : "Search name, URL or protocol…"}
          onChange={(event) => {
            setQuery(event.target.value);
          }}
        />
        <Chip>{`${String(filtered.length)} / ${String(endpoints.length)}`}</Chip>
      </div>
      <EndpointCards endpoints={filtered} onSelect={setSelectedId} />
      <Drawer
        open={selected !== undefined}
        onClose={() => {
          setSelectedId(null);
        }}
        title={selected?.name ?? (zh ? "端点详情" : "Endpoint details")}
      >
        {selected !== undefined && <EndpointDetails endpoint={selected} />}
      </Drawer>
    </section>
  );
}

interface EndpointsHomePageHeaderProps {
  zh: boolean;
  onAddRelay: () => void;
}

function EndpointsHomePageHeader({ zh, onAddRelay }: EndpointsHomePageHeaderProps) {
  return (
    <PageHeader
      title={zh ? "模型端点" : "Model endpoints"}
      kicker="LIBRARY / ENDPOINTS"
      description={
        zh
          ? "真实端点配置与凭据状态。启用不等于健康，不显示或导出 API Key。"
          : [
              "Endpoint configuration and credential status. Enabled does not imply ",
              "healthy; no keys are exposed.",
            ].join("")
      }
      actions={
        <button className="btn primary" type="button" onClick={onAddRelay}>
          {zh ? "添加中转站" : "Add Relay"}
        </button>
      }
    />
  );
}

function EndpointCards({
  endpoints,
  onSelect,
}: {
  endpoints: LlmEndpointReadDto[];
  onSelect: (id: string) => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  if (endpoints.length === 0)
    return (
      <div data-testid="endpoints-empty">
        <EmptyState message={zh ? "没有匹配的已配置端点" : "No matching configured endpoints"} />
      </div>
    );
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

function EndpointDetails({ endpoint }: { endpoint: LlmEndpointReadDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <div className={styles.page}>
      <KeyValueList
        fields={[
          { label: "ID", value: endpoint.id },
          { label: "Base URL", value: endpoint.base_url },
          { label: zh ? "协议族" : "Protocol", value: endpoint.protocol },
          { label: "API", value: endpoint.api_style },
          { label: zh ? "凭据" : "Credential", value: endpoint.credential },
          { label: zh ? "超时（秒）" : "Timeout (s)", value: endpoint.request_timeout_seconds },
          { label: zh ? "重试次数" : "Retries", value: endpoint.max_retries },
          { label: zh ? "并发上限" : "Concurrency", value: endpoint.concurrency_limit },
          { label: zh ? "版本" : "Version", value: endpoint.version },
        ]}
      />
      <p className={styles.notice}>
        {zh
          ? "此处只读，不自动发送模型探测请求。连接测试与模型发现位于接入向导。"
          : [
              "Read only. No automatic model probe is sent. Connection ",
              "tests and discovery are in setup.",
            ].join("")}
      </p>
    </div>
  );
}
