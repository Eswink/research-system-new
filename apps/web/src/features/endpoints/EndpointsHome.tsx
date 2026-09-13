import { useState, type Dispatch, type SetStateAction } from "react";

import { api } from "../../api/client";
import type { LlmEndpointReadDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { Drawer } from "../../components/Drawer";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { EndpointCards } from "./EndpointCards";
import { EndpointDeleteAction } from "./EndpointDeleteAction";
import { EndpointEditForm } from "./EndpointEditForm";
import { ConnectionTest } from "./ConnectionTest";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/** Endpoint configuration and credential status live here; keys are never returned or echoed. */
export function EndpointsHome({
  endpoints,
  onAddRelay,
  onChanged,
}: {
  endpoints: LlmEndpointReadDto[];
  onAddRelay: () => void;
  onChanged: () => void;
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
      {...{
        zh,
        onAddRelay,
        query,
        setQuery,
        filtered,
        endpoints,
        setSelectedId,
        selected,
        onChanged,
      }}
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
  onChanged: () => void;
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
  onChanged,
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
      <EndpointDetailDrawer
        selected={selected}
        onChanged={onChanged}
        zh={zh}
        onClose={() => {
          setSelectedId(null);
        }}
      />
    </section>
  );
}

function EndpointDetailDrawer({
  selected,
  onChanged,
  zh,
  onClose,
}: {
  selected: LlmEndpointReadDto | undefined;
  onChanged: () => void;
  zh: boolean;
  onClose: () => void;
}) {
  return (
    <Drawer open={selected !== undefined} onClose={onClose}
      title={selected?.name ?? (zh ? "端点详情" : "Endpoint details")}
    >
      {selected !== undefined && (
        <EndpointDetails
          key={selected.id}
          endpoint={selected}
          onChanged={onChanged}
          onDeleted={onClose}
        />
      )}
    </Drawer>
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

/** 详情抽屉：GET /llm-endpoints/{id} 取最新视图与 ETag；失败回退列表快照。 */
function EndpointDetails({
  endpoint,
  onChanged,
  onDeleted,
}: {
  endpoint: LlmEndpointReadDto;
  onChanged: () => void;
  onDeleted: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const fresh = useResource(`llm-endpoint:${endpoint.id}`, () => api.getEndpoint(endpoint.id));
  const [editing, setEditing] = useState(false);
  const view = fresh.data?.dto ?? endpoint;
  const etag = fresh.data !== null && fresh.data.etag.length > 0 ? fresh.data.etag : view.version;
  return (
    <div className={styles.page}>
      {fresh.error !== null && <FetchFallbackNotice zh={zh} />}
      {editing ? (
        <EndpointEditForm
          endpoint={view}
          etag={etag}
          zh={zh}
          onCancel={() => {
            setEditing(false);
          }}
          onDone={() => {
            setEditing(false);
            onChanged();
            fresh.reload();
          }}
        />
      ) : (
        <EndpointReadOnly
          view={view}
          zh={zh}
          onEdit={() => {
            setEditing(true);
          }}
          onDelete={() => {
            onChanged();
            onDeleted();
          }}
        />
      )}
      <hr className="hr" />
      <ConnectionTest endpoint={view} zh={zh} />
    </div>
  );
}

function FetchFallbackNotice({ zh }: { zh: boolean }) {
  return (
    <p className={styles.notice}>
      {zh
        ? "最新详情获取失败，显示列表快照；保存时以版本冲突检查兜底。"
        : [
            "Latest detail fetch failed; showing list snapshot. ",
            "Version conflicts are caught on save.",
          ].join("")}
    </p>
  );
}

function EndpointReadOnly({
  view,
  zh,
  onEdit,
  onDelete,
}: {
  view: LlmEndpointReadDto;
  zh: boolean;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <>
      <EndpointReadOnlyFields view={view} zh={zh} />
      <div className={styles.toolbar}>
        <button className="btn sm" type="button" onClick={onEdit} data-testid="endpoint-edit">
          {zh ? "编辑配置" : "Edit configuration"}
        </button>
        <EndpointDeleteAction endpoint={view} zh={zh} onDeleted={onDelete} />
      </div>
      <p className={styles.notice}>
        {zh
          ? "编辑仅改变配置，不自动发送模型探测请求；连接测试需显式点击。"
          : [
              "Editing changes configuration only; no automatic model probe is sent. ",
              "Connection tests require an explicit click.",
            ].join("")}
      </p>
    </>
  );
}

function EndpointReadOnlyFields({ view, zh }: { view: LlmEndpointReadDto; zh: boolean }) {
  return (
    <KeyValueList
      fields={[
        { label: "ID", value: view.id },
        { label: "Base URL", value: view.base_url },
        { label: zh ? "协议族" : "Protocol", value: view.protocol },
        { label: "API", value: view.api_style },
        { label: zh ? "凭据" : "Credential", value: view.credential },
        { label: zh ? "超时（秒）" : "Timeout (s)", value: view.request_timeout_seconds },
        { label: zh ? "重试次数" : "Retries", value: view.max_retries },
        { label: zh ? "并发上限" : "Concurrency", value: view.concurrency_limit },
        { label: zh ? "版本" : "Version", value: view.version },
      ]}
    />
  );
}
