import { useEffect, useRef } from "react";
import { useI18n } from "../../../i18n/useI18n";
import { BEFORE_NAVIGATION } from "../../../navigation/navigationGuard";
import { parseContext, stripContext } from "../../../navigation/urlContext";
import { isDirty, type EditorState } from "./editorState";

export function useUnsavedProtocolGuard(state: EditorState, templateLoading: boolean) {
  const { language } = useI18n();
  const current = useRef({ state, templateLoading, language });
  current.current = { state, templateLoading, language };
  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => {
      const value = current.current;
      if (isDirty(value.state) || value.state.busy || value.templateLoading) event.preventDefault();
    };
    const beforeNavigate = (event: Event) => {
      const value = current.current;
      if (!isDirty(value.state) && !value.state.busy && !value.templateLoading) return;
      if (event instanceof CustomEvent && isOwnSavedContext(event.detail, value.state)) return;
      const message =
        value.language === "zh"
          ? "有未保存的协议修改或正在执行的请求。离开会丢弃未保存修改，且不会取消后端请求。确认离开？"
          : [
              "Unsaved protocol changes or pending requests exist. Leaving discards ",
              "edits and does not cancel backend requests. Leave?",
            ].join("");
      if (!window.confirm(message)) event.preventDefault();
    };
    window.addEventListener("beforeunload", beforeUnload);
    window.addEventListener(BEFORE_NAVIGATION, beforeNavigate);
    return () => {
      window.removeEventListener("beforeunload", beforeUnload);
      window.removeEventListener(BEFORE_NAVIGATION, beforeNavigate);
    };
  }, []);
}

function isOwnSavedContext(detail: unknown, state: EditorState): boolean {
  if (
    typeof detail !== "object" ||
    detail === null ||
    !("url" in detail) ||
    typeof detail.url !== "string"
  )
    return false;
  const next = new URL(detail.url, window.location.href);
  return (
    state.saved !== null &&
    next.search === window.location.search &&
    stripContext(next.hash) === stripContext(window.location.hash) &&
    parseContext(next.hash).draftId === state.saved.draft_id
  );
}
