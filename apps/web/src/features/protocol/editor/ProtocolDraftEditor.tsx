import { useState, type Dispatch, type SetStateAction } from "react";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { ResourceBoundary } from "../../../components/ResourceBoundary";
import { ErrorState, LoadingState } from "../../../components/States";
import { useI18n } from "../../../i18n/useI18n";
import shared from "../../shared/LivePage.module.css";
import { DigestBanner, TemplatePicker } from "./EditorBanners";
import { EditorBody } from "./EditorBody";
import { EditorChrome } from "./EditorChrome";
import { EditorDiff } from "./EditorDiff";
import { EditorFeedback } from "./EditorFeedback";
import type { SectionId } from "./EditorLayout";
import styles from "./EditorShell.module.css";
import { EditorStatusBar } from "./EditorStatusBar";
import { useProtocolDocument, type ProtocolEditorProps } from "./useProtocolDocument";
import { useProtocolTemplates } from "./useProtocolTemplates";
import { useUnsavedProtocolGuard } from "./useUnsavedProtocolGuard";

export function ProtocolDraftEditor(props: ProtocolEditorProps = {}) {
  const editor = useProtocolDocument(props);
  const templates = useProtocolTemplates(editor.state, editor.dispatch);
  useUnsavedProtocolGuard(editor.state, templates.load.pending);
  const [section, setSection] = useState<SectionId>("identity");
  const [diffOpen, setDiffOpen] = useState(false);
  const busy = editor.state.busy || templates.load.pending || editor.restored.phase === "loading";
  return (
    <div className={shared.page}>
      <ResourceBoundary state={editor.restored}>{null}</ResourceBoundary>
      <TemplateRequestState templates={templates} />
      <ProtocolDraftEditorsection
        {...{ editor, templates, busy, setDiffOpen, section, setSection }}
      />
      <EditorFeedback state={editor.state} />
      <EditorDiff
        open={diffOpen}
        onClose={() => {
          setDiffOpen(false);
        }}
        before={editor.state.saved?.yaml_text ?? editor.state.sourceText ?? ""}
        after={editor.state.working}
      />
      <ReplacementConfirmation templates={templates} busy={busy} />
    </div>
  );
}

interface ProtocolDraftEditorsectionProps {
  editor: ReturnType<typeof useProtocolDocument>;
  templates: ReturnType<typeof useProtocolTemplates>;
  busy: boolean;
  setDiffOpen: Dispatch<SetStateAction<boolean>>;
  section: SectionId;
  setSection: Dispatch<SetStateAction<SectionId>>;
}

function ProtocolDraftEditorsection({
  editor,
  templates,
  busy,
  setDiffOpen,
  section,
  setSection,
}: ProtocolDraftEditorsectionProps) {
  return (
    <section className={styles.editorPanel} data-testid="protocol-editor">
      <EditorChrome
        mode={editor.state.mode}
        dirty={editor.dirty}
        fileName="protocol.yaml"
        onModeChange={(mode) => {
          editor.dispatch({ type: "mode", mode });
        }}
        templateOpen={templates.open}
        onToggleTemplates={() => {
          if (!busy) templates.setOpen(!templates.open);
        }}
        onValidate={editor.actions.validateDraft}
        onDiff={() => {
          setDiffOpen(true);
        }}
        validateBusy={busy}
      />
      <EditorDocumentArea
        editor={editor}
        templates={templates}
        busy={busy}
        section={section}
        setSection={setSection}
      />
      <EditorStatusBar
        state={{ ...editor.state, busy }}
        dirty={editor.dirty}
        stale={editor.stale}
        ackWarnings={editor.ackWarnings}
        onAckWarnings={editor.setAckWarnings}
        onSave={editor.actions.saveDraft}
        onDiscard={templates.discard}
        onStart={editor.actions.startRun}
        onPreflight={editor.actions.runPreflight}
      />
    </section>
  );
}

function EditorDocumentArea({
  editor,
  templates,
  busy,
  section,
  setSection,
}: {
  editor: ReturnType<typeof useProtocolDocument>;
  templates: ReturnType<typeof useProtocolTemplates>;
  busy: boolean;
  section: SectionId;
  setSection: (section: SectionId) => void;
}) {
  return (
    <>
      {templates.open && (
        <ResourceBoundary state={templates.catalog}>
          <TemplatePicker
            templates={templates.catalog.data ?? []}
            onPick={templates.pick}
            onClose={() => {
              templates.setOpen(false);
            }}
          />
        </ResourceBoundary>
      )}
      {editor.dirty && (
        <DigestBanner digest={editor.state.saved?.source_digest.slice(0, 8) ?? "new"} />
      )}
      <fieldset disabled={busy} className={styles.documentLock} aria-label="Protocol document">
        <EditorBody
          mode={editor.state.mode}
          working={editor.state.working}
          savedRevision={editor.state.saved?.revision ?? null}
          activeSection={section}
          onSectionChange={setSection}
          onEditText={(text) => {
            if (!busy) editor.dispatch({ type: "edit", text });
          }}
        />
      </fieldset>
    </>
  );
}

function TemplateRequestState({
  templates,
}: {
  templates: ReturnType<typeof useProtocolTemplates>;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <>
      {templates.load.pending && (
        <LoadingState message={zh ? "正在读取受控模板…" : "Loading controlled template…"} />
      )}
      {templates.load.error !== null && <ErrorState message={templates.load.error} />}
      {templates.catalog.error !== null && (
        <div>
          <ErrorState message={templates.catalog.error} />
          <button className="btn" type="button" onClick={templates.catalog.reload}>
            {zh ? "重试模板目录" : "Retry template catalog"}
          </button>
        </div>
      )}
    </>
  );
}

function ReplacementConfirmation({
  templates,
  busy,
}: {
  templates: ReturnType<typeof useProtocolTemplates>;
  busy: boolean;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <ConfirmDialog
      open={templates.replacement !== null}
      danger
      busy={busy}
      title={zh ? "确认放弃未保存修改" : "Discard unsaved changes?"}
      consequence={
        <p>
          {zh
            ? "当前未保存正文将被替换。此操作不会删除服务器上的草稿或修改冻结运行。"
            : [
                "Unsaved text will be replaced. Server drafts and frozen runs ",
                "are not deleted or modified.",
              ].join("")}
        </p>
      }
      confirmLabel={zh ? "放弃并继续" : "Discard and continue"}
      cancelLabel={zh ? "保留修改" : "Keep changes"}
      onConfirm={templates.confirmReplacement}
      onCancel={templates.cancelReplacement}
    />
  );
}
