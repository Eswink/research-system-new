import { useState } from "react";

import { api } from "../../api/client";
import type { ArtifactDiffDto, ArtifactDiffLineDto, ArtifactDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState, LoadingState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import styles from "../shared/LivePage.module.css";

/** 制品内容 diff（PLAN-047）：两侧都是 persisted 制品；不可比时如实标注原因。 */
export function ArtifactDiffPanel({ artifacts, zh }: { artifacts: ArtifactDto[]; zh: boolean }) {
  const [left, setLeft] = useState("");
  const [right, setRight] = useState("");
  const ready = left !== "" && right !== "";
  const diff = useResource(ready ? `artifact-diff:${left}:${right}` : null, () =>
    api.artifactDiff(left, right),
  );
  return (
    <PanelSection
      title={zh ? "制品内容 Diff" : "Artifact content diff"}
      extra={<Chip tone="neutral">{zh ? "按内容寻址版本" : "content-addressed"}</Chip>}
    >
      <DiffPicker
        artifacts={artifacts}
        left={left}
        right={right}
        zh={zh}
        onSelect={(side, id) => {
          if (side === "left") setLeft(id);
          else setRight(id);
        }}
      />
      {!ready && (
        <EmptyState message={zh ? "选择两个制品进行比较" : "Pick two artifacts to compare"} />
      )}
      {ready && diff.phase === "loading" && (
        <LoadingState message={zh ? "计算差异…" : "Computing diff…"} />
      )}
      {ready && diff.error !== null && <EmptyState message={diff.error} />}
      {ready && diff.data !== null && <DiffBody view={diff.data} zh={zh} />}
    </PanelSection>
  );
}

interface DiffPickerProps {
  artifacts: ArtifactDto[];
  left: string;
  right: string;
  zh: boolean;
  onSelect: (side: "left" | "right", id: string) => void;
}

function DiffPicker({ artifacts, left, right, zh, onSelect }: DiffPickerProps) {
  const sides = [
    { side: "left" as const, value: left, label: zh ? "左侧…" : "Left…" },
    { side: "right" as const, value: right, label: zh ? "右侧…" : "Right…" },
  ].map((item) => ({
    ...item,
    ariaLabel:
      item.side === "left"
        ? zh
          ? "左侧制品"
          : "Left artifact"
        : zh
          ? "右侧制品"
          : "Right artifact",
  }));
  return (
    <div className={styles.toolbar}>
      {sides.map((item) => (
        <select
          key={item.side}
          className="input"
          value={item.value}
          aria-label={item.ariaLabel}
          onChange={(event) => {
            onSelect(item.side, event.target.value);
          }}
        >
          <option value="">{item.label}</option>
          {artifacts.map((artifact) => (
            <option key={artifact.id} value={artifact.id}>
              {artifact.id}
            </option>
          ))}
        </select>
      ))}
    </div>
  );
}

function DiffBody({ view, zh }: { view: ArtifactDiffDto; zh: boolean }) {
  if (!view.available) {
    return (
      <EmptyState
        message={
          zh
            ? `不可比较：${diffReason(view, zh)}`
            : `Not comparable: ${diffReason(view, zh)}`
        }
      />
    );
  }
  if (view.identical) {
    return <EmptyState message={zh ? "两侧内容相同（digest 一致）" : "Identical content"} />;
  }
  return (
    <div data-testid="artifact-diff">
      <div className={styles.toolbar}>
        <Chip tone="success">{`+${String(view.stats.added)}`}</Chip>
        <Chip tone="danger">{`-${String(view.stats.removed)}`}</Chip>
        <Chip tone="neutral">{`context ${String(view.stats.context)}`}</Chip>
        {view.truncated && <Chip tone="warn">{zh ? "已截断" : "truncated"}</Chip>}
      </div>
      <pre className={styles.diff} aria-label={zh ? "制品差异" : "Artifact diff"}>
        {view.lines.map((line, index) => (
          <DiffLineRow key={`${String(index)}:${line.kind}`} line={line} />
        ))}
      </pre>
      <p className={styles.notice}>{view.note}</p>
    </div>
  );
}

function DiffLineRow({ line }: { line: ArtifactDiffLineDto }) {
  const className =
    line.kind === "ADDED"
      ? styles.diffAdded
      : line.kind === "REMOVED"
        ? styles.diffRemoved
        : styles.diffHunk;
  return <span className={className}>{line.text}</span>;
}

function diffReason(view: ArtifactDiffDto, zh: boolean): string {
  if (view.reason === "TOO_LARGE") {
    return zh ? "内容超过 diff 上限（不截断冒充全量）" : "content exceeds the diff size limit";
  }
  return zh
    ? "二进制或非 UTF-8 内容不解码（不做“看起来一样”的判定）"
    : "binary or non-UTF-8 content is not decoded";
}
