import { useCallback, useEffect, useRef } from "react";
import { api } from "../../api/client";
import { useResource } from "../../hooks/useResource";
import { useSelectedRun, type RunSelectionProps } from "../shared/useSelectedRun";
import { mergeEvents, useRunEventStream } from "./useRunEventStream";

/** Every read is keyed by selected Run; SSE triggers re-reads, not client state-machine changes. */
export function useRunTimeline(props: RunSelectionProps) {
  const { runId, selectRun } = useSelectedRun(props);
  const key = runId === "" ? null : runId;
  const run = useResource(key, () => api.getRun(runId));
  const tasks = useResource(key, () => api.runTasks(runId));
  const replay = useResource(key, () => api.runEvents(runId));
  // GOAL-20261103-104 EC-03：评审判词（逐条原文；失败不吞掉，由面板自己说）。
  const reviews = useResource(key, () => api.runReviews(runId));
  const stream = useRunEventStream(key);
  const { reload: reloadRun } = run;
  const { reload: reloadTasks } = tasks;
  const { reload: reloadReplay } = replay;
  const { reload: reloadReviews } = reviews;
  const refresh = useCallback(() => {
    reloadRun();
    reloadTasks();
    reloadReplay();
    reloadReviews();
  }, [reloadRun, reloadTasks, reloadReplay, reloadReviews]);
  useEventRefresh(key, stream.events.at(-1)?.event_id, refresh);
  return {
    runId,
    selectRun,
    run,
    tasks,
    replay,
    reviews,
    stream,
    refresh,
    events: mergeEvents(replay.data ?? [], stream.events),
  };
}

/** Throttle rather than debounce: a busy stream cannot postpone the snapshot indefinitely. */
function useEventRefresh(runId: string | null, eventId: string | undefined, refresh: () => void) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latest = useRef(refresh);
  latest.current = refresh;
  useEffect(
    () => () => {
      if (timer.current !== null) clearTimeout(timer.current);
      timer.current = null;
    },
    [runId],
  );
  useEffect(() => {
    if (eventId === undefined || timer.current !== null) return;
    timer.current = setTimeout(() => {
      timer.current = null;
      latest.current();
    }, 250);
  }, [eventId, runId]);
}
