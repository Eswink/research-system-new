import { draftApi } from "../../../api/draftClient";
import type { ProtocolDraftSummaryDto } from "../../../api/types";
import { PanelSection } from "../../../components/PanelSection";
import { ResourceBoundary } from "../../../components/ResourceBoundary";
import { EmptyState } from "../../../components/States";
import { useResource } from "../../../hooks/useResource";
import { useI18n } from "../../../i18n/useI18n";
import styles from "../../shared/LivePage.module.css";

/** 草稿库：GET /projects/{id}/protocol-drafts（draftApi.list）；点击进入编辑器。 */
export function DraftLibrary({
  activeDraftId,
  dirty,
  onOpenDraft,
}: {
  activeDraftId: string | null;
  dirty: boolean;
  onOpenDraft: (draftId: string) => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const drafts = useResource("draft-library", () => draftApi.list());
  const rows = drafts.data ?? [];
  return (
    <PanelSection
      title={zh ? "草稿库" : "Draft library"}
      extra={
        <button
          className="btn sm ghost"
          type="button"
          disabled={drafts.phase === "loading"}
          onClick={drafts.reload}
        >
          {zh ? "刷新" : "Refresh"}
        </button>
      }
    >
      <ResourceBoundary state={drafts}>
        {drafts.phase === "ready" && rows.length === 0 && (
          <EmptyState message={zh ? "还没有保存的草稿" : "No saved drafts yet"} />
        )}
        {rows.length > 0 && (
          <ul className={styles.list} data-testid="draft-library">
            {rows.map((draft) => (
              <DraftRow
                key={draft.draft_id}
                draft={draft}
                active={draft.draft_id === activeDraftId}
                blocked={dirty && draft.draft_id !== activeDraftId}
                zh={zh}
                onOpen={onOpenDraft}
              />
            ))}
          </ul>
        )}
      </ResourceBoundary>
    </PanelSection>
  );
}

function DraftRow({
  draft,
  active,
  blocked,
  zh,
  onOpen,
}: {
  draft: ProtocolDraftSummaryDto;
  active: boolean;
  blocked: boolean;
  zh: boolean;
  onOpen: (draftId: string) => void;
}) {
  return (
    <li>
      <button
        type="button"
        className={styles.listButton}
        aria-pressed={active}
        disabled={blocked}
        title={
          blocked
            ? zh
              ? "存在未保存修改：先保存或放弃后再切换草稿"
              : "Unsaved changes: save or discard before switching drafts"
            : undefined
        }
        onClick={() => {
          onOpen(draft.draft_id);
        }}
      >
        {draft.name} · <span className="mono">{draft.draft_id}</span> · r{String(draft.revision)}
        {" "}
        {zh ? `更新于 ${draft.updated_at}` : `updated ${draft.updated_at}`}
      </button>
    </li>
  );
}
