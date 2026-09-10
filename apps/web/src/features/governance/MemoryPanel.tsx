import { useState } from "react";

import { api } from "../../api/client";
import { problemText } from "../../api/problemText";
import type { MemoryRecordDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { Field } from "../../components/Field";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { ErrorState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

/** 产品 Memory 视图（WP-F；committed records + 提案直提交 + 物理删除）。 */
export function MemoryPanel() {
  const { language } = useI18n();
  const zh = language === "zh";
  const view = useResource("project-memory", () => api.projectMemory());
  return (
    <div className={styles.page} data-testid="memory-panel">
      <ResourceBoundary state={view}>
        {view.data !== null && (
          <MemoryRecords records={view.data.records} zh={zh} onChanged={view.reload} />
        )}
      </ResourceBoundary>
      {view.data !== null && <p className={styles.notice}>{view.data.scope_note}</p>}
      <MemoryProposeForm zh={zh} onCommitted={view.reload} />
    </div>
  );
}

function MemoryRecords({
  records,
  zh,
  onChanged,
}: {
  records: MemoryRecordDto[];
  zh: boolean;
  onChanged: () => void;
}) {
  const [issue, setIssue] = useState<string | null>(null);
  const remove = async (id: string): Promise<void> => {
    setIssue(null);
    try {
      await api.deleteMemory(id);
      onChanged();
    } catch (err) {
      setIssue(problemText(err));
    }
  };
  if (records.length === 0) {
    return (
      <p className={styles.notice}>
        {zh ? "尚无已提交的产品 Memory（提案需已登记 provenance）。" : "No committed product memory yet."}
      </p>
    );
  }
  return (
    <>
      {records.map((record) => (
        <MemoryRecordCard key={record.id} record={record} zh={zh} onRemove={remove} />
      ))}
      {issue !== null && <ErrorState message={issue} />}
    </>
  );
}

function MemoryRecordCard({
  record,
  zh,
  onRemove,
}: {
  record: MemoryRecordDto;
  zh: boolean;
  onRemove: (id: string) => Promise<void>;
}) {
  return (
    <div className={styles.card}>
      <div className={styles.cardHead}>
        <span className="mono">{record.id}</span>
        <span>
          <Chip tone={record.active ? "accent" : "neutral"}>{record.tier}</Chip>{" "}
          <Chip tone="neutral">{record.kind}</Chip>
          {record.active ? null : <Chip tone="warn">TOMBSTONE</Chip>}
        </span>
      </div>
      <p>{record.content}</p>
      <KeyValueList
        fields={[
          { label: zh ? "来源" : "Provenance", value: record.provenance },
          { label: zh ? "置信度" : "Confidence", value: record.confidence },
          { label: zh ? "复核" : "Review after", value: record.review_after ?? "—" },
          { label: zh ? "过期" : "Expires", value: record.expires_at ?? "—" },
        ]}
      />
      {record.active && (
        <button
          className="btn sm"
          type="button"
          onClick={() => {
            void onRemove(record.id);
          }}
        >
          {zh ? "删除记录" : "Delete record"}
        </button>
      )}
    </div>
  );
}

function useMemoryProposal(onCommitted: () => void) {
  const [content, setContent] = useState("");
  const [provenance, setProvenance] = useState("");
  const [tier, setTier] = useState("SESSION");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<string | null>(null);
  const submit = async (): Promise<void> => {
    setBusy(true);
    setIssue(null);
    try {
      await api.proposeMemory({
        tier,
        kind: "FACT",
        content: content.trim(),
        provenance: provenance.trim(),
        confidence: 0.8,
        curator_approved: false,
      });
      setContent("");
      onCommitted();
    } catch (err) {
      setIssue(problemText(err));
    } finally {
      setBusy(false);
    }
  };
  return { content, setContent, provenance, setProvenance, tier, setTier, busy, issue, submit };
}

function MemoryProposeForm({ zh, onCommitted }: { zh: boolean; onCommitted: () => void }) {
  const form = useMemoryProposal(onCommitted);
  const hint = zh
    ? "SESSION/RUN 自动提交（须已登记 provenance 源）；PROJECT 需 curator 批准；ORGANIZATION 默认拒绝。"
    : [
        "SESSION/RUN auto-commit with registered provenance; ",
        "PROJECT needs curator; ORGANIZATION denied.",
      ].join("");
  return (
    <div className={styles.toolbar} data-testid="memory-propose-form">
      <MemoryProposeFields form={form} zh={zh} hint={hint} />
      <button
        className="btn sm primary"
        type="button"
        disabled={form.busy}
        onClick={() => {
          void form.submit();
        }}
      >
        {form.busy ? (zh ? "提案中…" : "Proposing…") : zh ? "提交提案" : "Propose"}
      </button>
      {form.issue !== null && <ErrorState message={form.issue} />}
    </div>
  );
}

type MemoryForm = ReturnType<typeof useMemoryProposal>;

function MemoryProposeFields({ form, zh, hint }: { form: MemoryForm; zh: boolean; hint: string }) {
  return (
    <>
      <Field label={zh ? "内容" : "Content"} htmlFor="memory-content" hint={hint}>
        <input
          id="memory-content"
          className="input"
          value={form.content}
          disabled={form.busy}
          onChange={(event) => {
            form.setContent(event.target.value);
          }}
        />
      </Field>
      <Field
        label={zh ? "Provenance（须已登记）" : "Provenance (registered source)"}
        htmlFor="memory-prov"
      >
        <input
          id="memory-prov"
          className="input mono"
          value={form.provenance}
          disabled={form.busy}
          placeholder="paper://..."
          onChange={(event) => {
            form.setProvenance(event.target.value);
          }}
        />
      </Field>
      <Field label="Tier" htmlFor="memory-tier">
        <select
          id="memory-tier"
          className="input"
          value={form.tier}
          disabled={form.busy}
          onChange={(event) => {
            form.setTier(event.target.value);
          }}
        >
          <option value="SESSION">SESSION</option>
          <option value="RUN">RUN</option>
          <option value="PROJECT">PROJECT</option>
        </select>
      </Field>
    </>
  );
}
