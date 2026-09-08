/** 预检 + 启动动作 hook（T14：模板同源预检/启动；自定义草稿禁用）。 */

import { useCallback } from "react";

import { api } from "../../../api/client";
import type { EditorAction, EditorState } from "./editorState";

/**
 * 诚实数据路径（cursor plan §5.2）：
 * - 未修改的受控模板：同源 compile/preflight + dry-run + 启动（protocol_path）；
 * - 自定义草稿（sourcePath=null）：预检与启动禁用（G1 草稿修订预检无接口），
 *   不发任何"代替预检"请求。
 */
export function usePreflightAndStart(
  state: EditorState,
  dispatch: (action: EditorAction) => void,
  seqRef: { current: number },
): { runPreflight: () => void; startRun: () => void; canPreflight: boolean; canStartRun: boolean } {
  const canPreflight = state.sourcePath !== null;
  const canStartRun = state.sourcePath !== null && !state.preflightStale;

  const runPreflight = useCallback(async () => {
    const source = state.sourcePath;
    if (source === null) {
      return; // 自定义草稿：无修订预检接口，禁用
    }
    const seq = ++seqRef.current;
    try {
      const [report, projection] = await Promise.all([
        api.compileAndPreflight(source),
        api.dryRun(source),
      ]);
      if (seq === seqRef.current) {
        dispatch({
          type: "preflight",
          context: { revision: 0, digest: state.working, report, projection },
          requestSeq: seq,
          currentSeq: seqRef.current,
        });
      }
    } catch (error) {
      dispatch({
        type: "preflightFailed",
        error: error instanceof Error ? error.message : "preflight failed",
      });
    }
  }, [dispatch, seqRef, state.sourcePath, state.working]);

  const startRun = useCallback(() => {
    const source = state.sourcePath;
    if (source !== null) {
      void api.startRun(source);
    }
  }, [state.sourcePath]);

  return {
    runPreflight: () => {
      void runPreflight();
    },
    startRun,
    canPreflight,
    canStartRun,
  };
}
