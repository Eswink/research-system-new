/**
 * 协议草稿编辑器主组件（PLAN-20260908-033 阶段四）。
 *
 * 高保真复用设计稿交互结构：Chrome、区块导航、未保存横幅、Form/YAML
 * 双模式、模板选择、sticky 状态条；字段适配真实契约（id/version/phases）。
 * 闭环：编辑 → 服务端校验 → 保存修订 → 预检 → 启动（失败状态阻断启动/警告需确认）。
 */

import { useEffect, useReducer, useRef, useState } from "react";

import { draftApi } from "../../../api/draftClient";
import type { ProtocolDraftTemplateDto, ProtocolDraftViewDto } from "../../../api/types";
import { EditorChrome } from "./EditorChrome";
import { DigestBanner, TemplatePicker } from "./EditorBanners";
import { EditorBody } from "./EditorBody";
import { EditorStatusBar } from "./EditorStatusBar";
import { type SectionId } from "./EditorLayout";
import {
  initialEditorState,
  isDirty,
  preflightIsStale,
  type EditorState,
} from "./editorState";
import { editorReducer } from "./editorReducer";
import { useEditorActions } from "./useEditorActions";
import styles from "./EditorShell.module.css";

export function ProtocolDraftEditor(): React.JSX.Element {
  const editor = useEditorController();
  return (
    <section className={styles.editorPanel} data-testid="protocol-editor">
      <EditorChrome
        mode={editor.state.mode}
        onModeChange={editor.dispatchMode}
        dirty={editor.dirty}
        fileName="protocol.yaml"
        templateOpen={editor.templateOpen}
        onToggleTemplates={editor.toggleTemplates}
        onValidate={editor.actions.saveDraft}
        onDiff={editor.jumpToPhases}
        validateBusy={editor.state.saveStatus === "saving"}
      />
      {editor.templateOpen && (
        <TemplatePicker
          templates={editor.templates}
          onPick={editor.pickTemplate}
          onClose={editor.toggleTemplates}
        />
      )}
      {editor.dirty && (
        <DigestBanner digest={editor.state.saved?.source_digest.slice(0, 8) ?? "new"} />
      )}
      <EditorBody
        mode={editor.state.mode}
        working={editor.state.working}
        savedRevision={editor.state.saved?.revision ?? null}
        activeSection={editor.activeSection}
        onSectionChange={editor.setActiveSection}
        onEditText={editor.dispatchEdit}
      />
      <EditorStatusBar
        state={editor.state}
        dirty={editor.dirty}
        stale={editor.stale}
        ackWarnings={editor.ackWarnings}
        onAckWarnings={editor.setAckWarnings}
        onSave={editor.actions.saveDraft}
        onDiscard={editor.discard}
        onStart={editor.actions.startRun}
        onPreflight={editor.actions.runPreflight}
      />
    </section>
  );
}

interface EditorController {
  state: EditorState;
  dirty: boolean;
  stale: boolean;
  templateOpen: boolean;
  templates: ProtocolDraftTemplateDto[];
  activeSection: SectionId;
  ackWarnings: boolean;
  actions: ReturnType<typeof useEditorActions>;
  dispatchMode: (mode: "form" | "yaml") => void;
  dispatchEdit: (text: string) => void;
  setActiveSection: (section: SectionId) => void;
  setAckWarnings: (next: boolean) => void;
  toggleTemplates: () => void;
  pickTemplate: (templateId: string) => void;
  jumpToPhases: () => void;
  discard: () => void;
}

function useTemplateCatalog(): ProtocolDraftTemplateDto[] {
  const [templates, setTemplates] = useState<ProtocolDraftTemplateDto[]>([]);
  useEffect(() => {
    let cancelled = false;
    draftApi
      .listTemplates()
      .then((items) => {
        if (!cancelled) {
          setTemplates(items);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);
  return templates;
}

function useEditorController(): EditorController {
  const [state, dispatch] = useReducer(editorReducer, "", initialEditorState);
  const templateControls = useTemplateControls();
  const templates = useTemplateCatalog();
  const [activeSection, setActiveSection] = useState<SectionId>("identity");
  const [ackWarnings, setAckWarnings] = useState(false);
  const actions = useEditorActions(state, dispatch);
  const discard = useDiscard(dispatch, state);
  const dispatchEdit = (text: string): void => {
    dispatch({ type: "edit", text });
  };
  const dispatchMode = (mode: "form" | "yaml"): void => {
    dispatch({ type: "mode", mode });
  };
  const pickTemplate = (templateId: string): void => {
    void draftApi
      .getTemplate(templateId)
      .then((template) => {
        dispatch({ type: "edit", text: template.yaml_text });
      })
      .catch(() => undefined);
    templateControls.close();
  };
  return {
    state,
    dirty: isDirty(state),
    stale: preflightIsStale(state),
    templateOpen: templateControls.open,
    templates,
    activeSection,
    ackWarnings,
    actions,
    dispatchMode,
    dispatchEdit,
    setActiveSection,
    setAckWarnings,
    toggleTemplates: templateControls.toggle,
    pickTemplate,
    jumpToPhases: () => {
      setActiveSection("phases");
    },
    discard,
  };
}

/** 模板面板开关 + 关闭后焦点恢复到触发按钮（可访问性硬要求） */
function useTemplateControls(): { open: boolean; toggle: () => void; close: () => void } {
  const [open, setOpen] = useState(false);
  const wasOpen = useRef(false);
  useEffect(() => {
    // commit 后恢复焦点：面板卸载会把焦点丢到 body
    if (wasOpen.current && !open) {
      document.getElementById("templates-toggle")?.focus();
    }
    wasOpen.current = open;
  }, [open]);
  return {
    open,
    toggle: () => {
      setOpen((current) => !current);
    },
    close: () => {
      setOpen(false);
    },
  };
}

interface ResetAction {
  type: "reset";
  working: string;
  saved: ProtocolDraftViewDto | null;
}

function useDiscard(dispatch: (action: ResetAction) => void, state: EditorState): () => void {
  return () => {
    dispatch({ type: "reset", working: state.saved?.yaml_text ?? "", saved: state.saved });
  };
}
