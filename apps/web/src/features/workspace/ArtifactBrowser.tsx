import { useState } from "react";

import { api } from "../../api/client";
import type { ArtifactDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, LoadingState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

const PREVIEWABLE = [
  "text/plain",
  "text/csv",
  "text/markdown",
  "application/json",
  "image/png",
  "image/jpeg",
];

export function isPreviewable(artifact: ArtifactDto): boolean {
  return PREVIEWABLE.includes(artifact.media_type);
}

/** 运行产物浏览器（WP-C）：列表来自 GET /runs/{id}/artifacts；详情含下载与白名单预览。 */
export function ArtifactBrowser({ runId }: { runId: string }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const list = useResource(runId === "" ? null : `run-artifacts:${runId}`, () =>
    api.listRunArtifacts(runId),
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  return (
    <PanelSection
      title={zh ? "运行产物" : "Run artifacts"}
      extra={
        <button
          className="btn sm ghost"
          type="button"
          disabled={list.phase === "loading"}
          onClick={list.reload}
        >
          {zh ? "刷新" : "Refresh"}
        </button>
      }
    >
      <ResourceBoundary state={list}>
        {list.phase === "ready" && (list.data ?? []).length === 0 && (
          <EmptyState message={zh ? "此运行没有已登记的产物" : "No artifacts for this run"} />
        )}
        {(list.data ?? []).length > 0 && (
          <div className={styles.split}>
            <ArtifactRows
              artifacts={list.data ?? []}
              selectedId={selectedId}
              zh={zh}
              onSelect={setSelectedId}
            />
            <ArtifactDetail
              artifact={list.data?.find((item) => item.id === selectedId) ?? null}
              zh={zh}
            />
          </div>
        )}
      </ResourceBoundary>
    </PanelSection>
  );
}

function ArtifactRows({
  artifacts,
  selectedId,
  zh,
  onSelect,
}: {
  artifacts: ArtifactDto[];
  selectedId: string | null;
  zh: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <ul className={styles.list} data-testid="artifact-rows">
      {artifacts.map((artifact) => (
        <li key={artifact.id}>
          <button
            type="button"
            className={styles.listButton}
            aria-pressed={artifact.id === selectedId}
            onClick={() => {
              onSelect(artifact.id);
            }}
          >
            <span className="mono">{artifact.id}</span> · {formatBytes(artifact.size_bytes)} ·{" "}
            {artifact.media_type}
            <Chip tone={artifact.state === "DELETED_TOMBSTONE" ? "danger" : "neutral"}>
              {zh ? "状态" : "state"} {artifact.state}
            </Chip>
          </button>
        </li>
      ))}
    </ul>
  );
}

function formatBytes(size: number): string {
  if (size < 1024) return `${String(size)} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KiB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MiB`;
}

function ArtifactDetail({ artifact, zh }: { artifact: ArtifactDto | null; zh: boolean }) {
  const meta = useResource(
    artifact === null ? null : `artifact-meta:${artifact.id}`,
    () => api.getArtifact(artifact?.id ?? ""),
  );
  if (artifact === null) {
    return <EmptyState message={zh ? "选择产物查看元数据" : "Select an artifact to inspect"} />;
  }
  const view = meta.data ?? artifact;
  return (
    <div className={styles.page} data-testid="artifact-detail">
      <KeyValueList
        fields={[
          { label: "ID", value: view.id },
          { label: "Digest", value: view.digest },
          { label: zh ? "大小" : "Size", value: formatBytes(view.size_bytes) },
          { label: "Media", value: view.media_type },
          { label: zh ? "状态" : "State", value: view.state },
          { label: zh ? "内容校验" : "Content verified", value: verifyText(view.verified, zh) },
        ]}
      />
      <div className={styles.toolbar}>
        <a className="btn sm" href={api.artifactContentUrl(artifact.id)} download={artifact.id}>
          {zh ? "下载内容" : "Download"}
        </a>
      </div>
      {isPreviewable(view) && view.state !== "DELETED_TOMBSTONE" && (
        <ArtifactPreview artifactId={artifact.id} zh={zh} />
      )}
    </div>
  );
}

function verifyText(verified: boolean | null, zh: boolean): string {
  if (verified === true) return zh ? "已校验（digest 匹配）" : "verified (digest matches)";
  if (verified === false) return zh ? "校验失败" : "verification FAILED";
  return zh ? "未校验（tombstone 或不可读）" : "not verifiable";
}

function ArtifactPreview({ artifactId, zh }: { artifactId: string; zh: boolean }) {
  const text = useResource(`artifact-preview:${artifactId}`, () =>
    api.artifactPreviewText(artifactId),
  );
  return (
    <div>
      <div className={styles.cardTitle}>{zh ? "内联预览" : "Inline preview"}</div>
      {text.phase === "loading" && <LoadingState message={zh ? "加载内容…" : "Loading…"} />}
      {text.error !== null && <EmptyState message={text.error} />}
      {text.data !== null && <pre className={styles.code}>{text.data}</pre>}
    </div>
  );
}
