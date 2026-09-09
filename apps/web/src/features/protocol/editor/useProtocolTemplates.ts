import { useEffect, useRef, useState } from "react";
import { draftApi } from "../../../api/draftClient";
import { useCommand } from "../../../hooks/useCommand";
import { useResource } from "../../../hooks/useResource";
import type { EditorAction, EditorState } from "./editorState";
import { isDirty } from "./editorState";

type Replacement = { kind: "template"; id: string } | { kind: "discard" };

export function useProtocolTemplates(state: EditorState, dispatch: (action: EditorAction) => void) {
  const [open, setOpen] = useState(false);
  const [replacement, setReplacement] = useState<Replacement | null>(null);
  const current = useRef(state);
  current.current = state;
  const catalog = useResource("controlled-protocol-templates", () => draftApi.listTemplates());
  const load = useCommand(
    async (id: string) => draftApi.getTemplate(id),
    (template) => {
      if (!current.current.busy)
        dispatch({ type: "loadTemplate", text: template.yaml_text, sourcePath: template.source });
    },
  );
  useTemplateFocusRestore(open);
  const apply = (next: Replacement) => {
    if (state.busy || load.pending) return;
    if (next.kind === "template") {
      setOpen(false);
      void load.run(next.id);
    } else dispatch({ type: "reset", working: state.saved?.yaml_text ?? "", saved: state.saved });
    setReplacement(null);
  };
  const request = (next: Replacement) => {
    if (state.busy || load.pending) return;
    if (isDirty(state)) setReplacement(next);
    else apply(next);
  };
  return {
    open,
    setOpen,
    catalog,
    load,
    replacement,
    pick: (id: string) => {
      request({ kind: "template", id });
    },
    discard: () => {
      request({ kind: "discard" });
    },
    confirmReplacement: () => {
      if (replacement !== null) apply(replacement);
    },
    cancelReplacement: () => {
      setReplacement(null);
    },
  };
}

function useTemplateFocusRestore(open: boolean): void {
  const previous = useRef(false);
  useEffect(() => {
    if (previous.current && !open) document.getElementById("templates-toggle")?.focus();
    previous.current = open;
  }, [open]);
}
