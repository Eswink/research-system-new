import { useState } from "react";

import { draftApi } from "../../../api/draftClient";
import type { ProtocolDraftRevisionDto } from "../../../api/types";
import { Chip } from "../../../components/Chip";
import { Drawer } from "../../../components/Drawer";
import { PanelSection } from "../../../components/PanelSection";
import { ResourceBoundary } from "../../../components/ResourceBoundary";
import { EmptyState } from "../../../components/States";
import { useResource, type ResourceState } from "../../../hooks/useResource";
import { useI18n } from "../../../i18n/useI18n";
import styles from "../../shared/LivePage.module.css";

/** 修订历史（append-only 不可变）：listRevisions + getRevision 只读查看。 */
export function RevisionHistory({ draftId }: { draftId: string | null }) {
  const revisions = useResource(
    draftId === null ? null : `draft-revisions:${draftId}`,
    () => draftApi.listRevisions(draftId ?? ""),
  );
  const [viewing, setViewing] = useState<ProtocolDraftRevisionDto | null>(null);
  if (draftId === null) return null;
  return (
    <RevisionSection
      {...{
        draftId,
        revisions,
        viewing,
        setViewing,
        onReload: revisions.reload,
        loading: revisions.phase === "loading",
      }}
    />
  );
}

interface RevisionSectionProps {
  draftId: string;
  revisions: ResourceState<ProtocolDraftRevisionDto[]>;
  viewing: ProtocolDraftRevisionDto | null;
  setViewing: (value: ProtocolDraftRevisionDto | null) => void;
  onReload: () => void;
  loading: boolean;
}

function RevisionSection(props: RevisionSectionProps) {
  const { draftId, revisions, viewing, setViewing, onReload, loading } = props;
  const { language } = useI18n();
  const zh = language === "zh";
  const rows = revisions.data ?? [];
  return (
    <PanelSection
      title={zh ? "修订历史（不可变）" : "Revision history (immutable)"}
      extra={
        <button className="btn sm ghost" type="button" disabled={loading} onClick={onReload}>
          {zh ? "刷新" : "Refresh"}
        </button>
      }
    >
      <ResourceBoundary state={revisions}>
        {revisions.phase === "ready" && rows.length === 0 && (
          <EmptyState message={zh ? "尚无修订" : "No revisions yet"} />
        )}
        {rows.length > 0 && (
          <ul className={styles.list} data-testid="revision-history">
            {rows.map((revision) => (
              <RevisionRow key={revision.revision} {...{ draftId, revision, setViewing }} />
            ))}
          </ul>
        )}
      </ResourceBoundary>
      <RevisionDrawer
        viewing={viewing}
        zh={zh}
        onClose={() => {
          setViewing(null);
        }}
      />
    </PanelSection>
  );
}

function RevisionRow({
  draftId,
  revision,
  setViewing,
}: {
  draftId: string;
  revision: ProtocolDraftRevisionDto;
  setViewing: (value: ProtocolDraftRevisionDto | null) => void;
}) {
  const open = (): void => {
    void draftApi
      .getRevision(draftId, revision.revision)
      .then((value) => {
        setViewing(value);
      })
      .catch(() => {
        setViewing(null);
      });
  };
  return (
    <li>
      <button type="button" className={styles.listButton} onClick={open}>
        r{String(revision.revision)} · <span className="mono">{revision.source_digest}</span>
        {" "}
        {revision.created_at}
      </button>
    </li>
  );
}

function RevisionDrawer({
  viewing,
  zh,
  onClose,
}: {
  viewing: ProtocolDraftRevisionDto | null;
  zh: boolean;
  onClose: () => void;
}) {
  const label = `r${String(viewing?.revision ?? "")}`;
  const title = zh ? `修订 ${label}（只读）` : `Revision ${label} (read only)`;
  return (
    <Drawer open={viewing !== null} onClose={onClose} title={title}>
      {viewing !== null && (
        <div className={styles.page}>
          <div className={styles.toolbar}>
            <Chip tone="neutral">{viewing.source_digest}</Chip>
            <RevisionImmutabilityNote zh={zh} />
          </div>
          <pre className={styles.code}>{viewing.yaml_text}</pre>
        </div>
      )}
    </Drawer>
  );
}

function RevisionImmutabilityNote({ zh }: { zh: boolean }) {
  return (
    <span>
      {zh
        ? "修订不可改写；保存编辑会产生新修订。"
        : "Revisions are immutable; saving edits creates a new revision."}
    </span>
  );
}
