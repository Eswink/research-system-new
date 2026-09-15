import { useState } from "react";

import { api } from "../../api/client";
import type {
  RunWorkspaceSnapshotDto,
  WorkspaceSnapshotDiffDto,
  WorkspaceSnapshotFileDto,
  WorkspaceSnapshotTreeDto,
} from "../../api/types";
import { Chip } from "../../components/Chip";
import { Table } from "../../components/Table";
import { EmptyState, LoadingState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { snapshotChangeColumns, snapshotFileColumns } from "./workspaceSnapshotColumns";
import { shortDigest } from "./workspaceSnapshotColumns";
import styles from "../shared/LivePage.module.css";

/**
 * 工作区快照（G8 / PLAN-20260915-058）：run 记录过的快照 digest、文件树与文件级 diff。
 *
 * 只呈现控制面能证明的事：digest 来自 run 的 evidence 记录，`retained` = 该 digest 是否
 * 仍在配置的快照存储里；控制面不持久化 run→工作区绑定，因此页面**不**声称"这就是该 run
 * 执行时的工作区"。文件级 diff 只比路径/大小/sha256（内容行级 diff 在制品面板）。
 */
export function WorkspaceSnapshotPanel({ runId, zh }: { runId: string; zh: boolean }) {
  const snapshots = useResource(`run-workspace-snapshots:${runId}`, () =>
    api.runWorkspaceSnapshots(runId),
  );
  return (
    <div className={styles.stack} data-testid="workspace-snapshot-panel">
      <SnapshotRecordCard state={snapshots} zh={zh} />
      {snapshots.data !== null && <SnapshotExplorer recorded={snapshots.data.snapshots} zh={zh} />}
    </div>
  );
}

interface SnapshotRecordCardProps {
  state: {
    phase: string;
    data: { snapshots: RunWorkspaceSnapshotDto[]; note: string } | null;
    error: string | null;
  };
  zh: boolean;
}

function SnapshotRecordCard({ state, zh }: SnapshotRecordCardProps) {
  if (state.phase === "loading") {
    return <LoadingState message={zh ? "读取快照记录…" : "Loading snapshot records…"} />;
  }
  if (state.error !== null) return <EmptyState message={state.error} />;
  if (state.data === null) return null;
  const retained = state.data.snapshots.filter((item) => item.retained).length;
  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>
        {zh ? "运行记录的快照" : "Snapshots recorded by this run"}{" "}
        <span className={styles.metadata}>
          (
          {zh
            ? `保留 ${String(retained)} / 记录 ${String(state.data.snapshots.length)}`
            : `${String(retained)} retained / ${String(state.data.snapshots.length)} recorded`}
          )
        </span>
      </h3>
      {state.data.snapshots.length === 0 ? (
        <p className={styles.metadata}>
          {zh ? "该运行没有记录工作区快照 digest" : "This run recorded no workspace snapshot digests"}
        </p>
      ) : (
        <ul className={styles.list}>
          {state.data.snapshots.map((item) => (
            <li key={item.digest} data-testid="snapshot-record-row">
              <span className="mono">{shortDigest(item.digest)}</span>{" "}
              <Chip tone={item.retained ? "success" : "warn"}>
                {item.retained ? (zh ? "保留中" : "retained") : zh ? "未保留" : "not retained"}
              </Chip>{" "}
              <Chip tone="neutral">{item.recorded_as.join(" + ")}</Chip>
            </li>
          ))}
        </ul>
      )}
      <p className={styles.notice}>{state.data.note}</p>
    </div>
  );
}

function SnapshotExplorer({
  recorded,
  zh,
}: {
  recorded: RunWorkspaceSnapshotDto[];
  zh: boolean;
}) {
  const [treeDigest, setTreeDigest] = useState("");
  const [left, setLeft] = useState("");
  const [right, setRight] = useState("");
  return (
    <>
      <SnapshotTreeCard
        recorded={recorded}
        digest={treeDigest}
        onSelect={setTreeDigest}
        zh={zh}
      />
      <SnapshotDiffCard
        recorded={recorded}
        left={left}
        right={right}
        onSelect={(side, value) => {
          if (side === "left") setLeft(value);
          else setRight(value);
        }}
        zh={zh}
      />
    </>
  );
}

function SnapshotTreeCard({
  recorded,
  digest,
  onSelect,
  zh,
}: {
  recorded: RunWorkspaceSnapshotDto[];
  digest: string;
  onSelect: (digest: string) => void;
  zh: boolean;
}) {
  const tree = useResource(digest === "" ? null : `workspace-snapshot-files:${digest}`, () =>
    api.workspaceSnapshotFiles(digest),
  );
  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>{zh ? "快照文件树" : "Snapshot file tree"}</h3>
      <div className={styles.toolbar}>
        <select
          className="input"
          value={digest}
          aria-label={zh ? "选择快照" : "Select snapshot"}
          onChange={(event) => {
            onSelect(event.target.value);
          }}
        >
          <option value="">{zh ? "选择一个快照…" : "Select a snapshot…"}</option>
          {recorded.map((item) => (
            <option key={item.digest} value={item.digest}>
              {shortDigest(item.digest)}
            </option>
          ))}
        </select>
      </div>
      {digest === "" && (
        <p className={styles.metadata}>
          {zh ? "选择快照以查看文件树（只读）" : "Pick a snapshot to list its files"}
        </p>
      )}
      {digest !== "" && tree.phase === "loading" && (
        <LoadingState message={zh ? "读取文件树…" : "Loading file tree…"} />
      )}
      {digest !== "" && tree.error !== null && <EmptyState message={tree.error} />}
      {digest !== "" && tree.data !== null && <TreeBody view={tree.data} zh={zh} />}
    </div>
  );
}

function TreeBody({ view, zh }: { view: WorkspaceSnapshotTreeDto; zh: boolean }) {
  return (
    <div data-testid="snapshot-file-tree">
      <div className={styles.toolbar}>
        <Chip tone="neutral">{`${String(view.file_count)} files`}</Chip>
        <Chip tone="neutral">{`${String(view.total_bytes)} B`}</Chip>
        {view.truncated && <Chip tone="warn">{zh ? "已截断" : "truncated"}</Chip>}
      </div>
      <Table
        columns={snapshotFileColumns(zh)}
        rows={view.files}
        rowKey={(row: WorkspaceSnapshotFileDto) => row.path}
        ariaLabel={zh ? "快照文件树" : "Snapshot file tree"}
      />
    </div>
  );
}

interface SnapshotDiffCardProps {
  recorded: RunWorkspaceSnapshotDto[];
  left: string;
  right: string;
  zh: boolean;
  onSelect: (side: "left" | "right", digest: string) => void;
}

function SnapshotDiffCard({ recorded, left, right, zh, onSelect }: SnapshotDiffCardProps) {
  const ready = left !== "" && right !== "";
  const diff = useResource(ready ? `workspace-snapshot-diff:${left}:${right}` : null, () =>
    api.workspaceSnapshotDiff(left, right),
  );
  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>
        {zh ? "快照文件级 Diff" : "Snapshot file-level diff"}{" "}
        <span className={styles.metadata}>({zh ? "只比元数据" : "metadata only"})</span>
      </h3>
      <div className={styles.toolbar}>
        {(["left", "right"] as const).map((side) => (
          <select
            key={side}
            className="input"
            value={side === "left" ? left : right}
            aria-label={side === "left" ? "左侧快照" : "右侧快照"}
            onChange={(event) => {
              onSelect(side, event.target.value);
            }}
          >
            <option value="">{side === "left" ? "左侧…" : "右侧…"}</option>
            {recorded.map((item) => (
              <option key={item.digest} value={item.digest}>
                {shortDigest(item.digest)}
              </option>
            ))}
          </select>
        ))}
      </div>
      {!ready && (
        <p className={styles.metadata}>
          {zh ? "选择两个快照比较文件级差异" : "Pick two snapshots to compare"}
        </p>
      )}
      {ready && diff.phase === "loading" && (
        <LoadingState message={zh ? "计算差异…" : "Computing diff…"} />
      )}
      {ready && diff.error !== null && <EmptyState message={diff.error} />}
      {ready && diff.data !== null && <DiffBody view={diff.data} zh={zh} />}
    </div>
  );
}

function DiffBody({ view, zh }: { view: WorkspaceSnapshotDiffDto; zh: boolean }) {
  if (view.identical) {
    return (
      <EmptyState
        message={zh ? "两侧快照相同（同一 digest 或内容一致）" : "Identical snapshots"}
      />
    );
  }
  return (
    <div data-testid="snapshot-diff">
      <div className={styles.toolbar}>
        <Chip tone="success">{`+${String(view.added)}`}</Chip>
        <Chip tone="danger">{`-${String(view.removed)}`}</Chip>
        <Chip tone="warn">{`~${String(view.changed)}`}</Chip>
        <Chip tone="neutral">{`unchanged ${String(view.unchanged)}`}</Chip>
        {view.truncated && <Chip tone="warn">{zh ? "已截断" : "truncated"}</Chip>}
      </div>
      <Table
        columns={snapshotChangeColumns(zh)}
        rows={view.changes}
        rowKey={(row) => row.path}
        ariaLabel={zh ? "快照文件级差异" : "Snapshot file-level changes"}
      />
      <p className={styles.notice}>{view.note}</p>
    </div>
  );
}
