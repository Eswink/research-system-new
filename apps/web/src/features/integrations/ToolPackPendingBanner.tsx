import { api } from "../../api/client";
import type { ToolPackDto, ToolPackPendingDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { ErrorState } from "../../components/States";
import { useAsyncAction } from "../../hooks/useAsyncAction";
import styles from "../shared/LivePage.module.css";
import { diffLines } from "./toolPackCopy";

/** 一条待批准更新：pack 的**生效**版本 + 候选版本（未生效）。 */
export interface PendingUpdate {
  pack: ToolPackDto;
  pending: ToolPackPendingDto;
}

/** 从列表投影出待批准项（`pending` 为空的 pack 不出现）。 */
export function pendingUpdates(packs: ToolPackDto[]): PendingUpdate[] {
  return packs.flatMap((pack) =>
    pack.pending === null ? [] : [{ pack, pending: pack.pending }],
  );
}

/**
 * 待批准横幅（PLAN-065 / AC-03）。
 *
 * 这里是"未生效"的唯一入口：候选 digest 与 diff 明细都显示在这里，
 * 而表里的 digest 列始终是生效版本——两处混用就等于界面在撒谎。
 */
export function ToolPackPendingBanner({
  updates,
  zh,
  onChanged,
}: {
  updates: PendingUpdate[];
  zh: boolean;
  onChanged: () => void;
}) {
  if (updates.length === 0) {
    return null;
  }
  return (
    <div className={styles.card} data-testid="toolpack-pending-banner">
      <div className={styles.cardHead}>
        <h3 className={styles.cardTitle}>
          {zh ? "待批准的更新（未生效）" : "Pending updates (not effective)"}
        </h3>
        <Chip tone="warn">{String(updates.length)}</Chip>
      </div>
      <p className={styles.notice}>
        {zh
          ? "下表 digest 列仍是当前生效版本；批准后候选版本才替换生效版本并进入目录。"
          : "The table below still shows the effective version; approving replaces it " +
            "and updates the catalog."}
      </p>
      {updates.map((update) => (
        <PendingUpdateCard
          key={update.pack.id}
          update={update}
          zh={zh}
          onChanged={onChanged}
        />
      ))}
    </div>
  );
}

function PendingUpdateCard({
  update,
  zh,
  onChanged,
}: {
  update: PendingUpdate;
  zh: boolean;
  onChanged: () => void;
}) {
  const { pack, pending } = update;
  const action = useAsyncAction(onChanged);
  return (
    <div data-testid={`toolpack-pending-${pack.id}`}>
      <div className={styles.cardHead}>
        <span className="mono">{pack.id}</span>
        <Chip tone="warn">{zh ? "待批准" : "pending"}</Chip>
        <button
          className="btn sm"
          type="button"
          data-testid={`toolpack-approve-${pack.id}`}
          disabled={action.busy}
          onClick={() => {
            action.run(() => api.approveToolPackUpdate(pack.id));
          }}
        >
          {zh ? "批准扩张" : "Approve expansion"}
        </button>
      </div>
      <p className={styles.notice}>
        <CandidateDigests pack={pack} pending={pending} zh={zh} />
      </p>
      <ul className={styles.list} data-testid={`toolpack-diff-${pack.id}`}>
        {diffLines(pending.diff, zh).map((line) => (
          <li key={line} className="mono">
            {line}
          </li>
        ))}
      </ul>
      {pending.note !== "" && <p className={styles.notice}>{pending.note}</p>}
      {action.error !== null && (
        <div data-testid={`toolpack-approve-error-${pack.id}`}>
          <ErrorState message={action.error} />
        </div>
      )}
    </div>
  );
}

/** 生效 digest → 候选 digest（候选的完整值只在 title 里，列表列不受影响）。 */
function CandidateDigests({
  pack,
  pending,
  zh,
}: {
  pack: ToolPackDto;
  pending: ToolPackPendingDto;
  zh: boolean;
}) {
  return (
    <>
      {zh ? "生效版本 " : "effective "}
      <span className="mono">{shortDigest(pack.digest)}</span>
      {zh ? " → 候选版本 " : " → candidate "}
      <span className="mono" title={pending.digest}>
        {shortDigest(pending.digest)}
      </span>
      {` (v${pending.version})`}
    </>
  );
}

/** digest 在界面上截断显示；完整值始终在 title（与注册表 pin 的既有风格一致）。 */
export function shortDigest(digest: string): string {
  return digest.length > 24 ? `${digest.slice(0, 24)}…` : digest;
}
