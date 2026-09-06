import { useEffect, useState } from "react";

import { api } from "../../api/client";
import type { RunDetailDto, RunEventDto, TaskDto } from "../../api/types";

export interface RunPanelState {
  run: RunDetailDto | null;
  runs: RunDetailDto[];
  events: RunEventDto[];
  tasks: TaskDto[];
  busy: boolean;
  error: string | null;
}

export interface RunPanelActions {
  start: (protocolPath: string) => Promise<void>;
  cancel: () => Promise<void>;
  refresh: (runId: string) => Promise<void>;
  loadRun: (runId: string) => Promise<void>;
}

interface RunSetters {
  setRun: (value: RunDetailDto | null) => void;
  setRuns: (value: RunDetailDto[]) => void;
  setEvents: (value: RunEventDto[]) => void;
  setTasks: (value: TaskDto[]) => void;
  setBusy: (value: boolean) => void;
  setError: (value: string | null) => void;
  getRun: () => RunDetailDto | null;
  isCancelled: () => boolean;
}

const handleError = (err: unknown): string => {
  return err instanceof Error ? err.message : "run operation failed";
};

async function fetchRunSnapshot(runId: string) {
  const [detail, eventList, taskList] = await Promise.all([
    api.getRun(runId),
    api.runEvents(runId),
    api.runTasks(runId),
  ]);
  return { detail, eventList, taskList };
}

async function loadSnapshot(runId: string, setters: RunSetters) {
  if (runId.length === 0 || setters.isCancelled()) {
    return;
  }
  try {
    const snapshot = await fetchRunSnapshot(runId);
    setters.setRun(snapshot.detail);
    setters.setEvents(snapshot.eventList);
    setters.setTasks(snapshot.taskList);
  } catch (err) {
    setters.setError(handleError(err));
  }
}

async function startRunFlow(protocolPath: string, setters: RunSetters) {
  setters.setBusy(true);
  setters.setError(null);
  try {
    const started = await api.startRun(protocolPath);
    setters.setRun(started);
    await loadSnapshot(started.id, setters);
    setters.setRuns(await api.listRuns());
  } catch (err) {
    setters.setError(handleError(err));
  } finally {
    setters.setBusy(false);
  }
}

async function cancelRunFlow(setters: RunSetters) {
  const run = setters.getRun();
  if (run === null) {
    return;
  }
  setters.setBusy(true);
  try {
    const cancelled = await api.cancelRun(run.id);
    setters.setRun(cancelled);
  } catch (err) {
    setters.setError(handleError(err));
  } finally {
    setters.setBusy(false);
  }
}

async function refreshRuns(setters: RunSetters) {
  try {
    const items = await api.listRuns();
    setters.setRuns(items);
    if (items.length > 0) {
      await loadSnapshot(items[0]?.id ?? "", setters);
    }
  } catch {
    return;
  }
}

/**
 * Run 控制状态（server-state cache；刷新后从 API 恢复，不持 Canonical State）。
 * M13-R1 WP-M2：挂载时经 GET /projects/{id}/runs 自动恢复最近 run。
 */
export function useRunPanel(): RunPanelState & RunPanelActions {
  const [run, setRun] = useState<RunDetailDto | null>(null);
  const [runs, setRuns] = useState<RunDetailDto[]>([]);
  const [events, setEvents] = useState<RunEventDto[]>([]);
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setters: RunSetters = {
    setRun,
    setRuns,
    setEvents,
    setTasks,
    setBusy,
    setError,
    getRun: () => run,
    isCancelled: () => false,
  };

  useEffect(() => {
    let cancelled = false;
    void refreshRuns({ ...setters, isCancelled: () => cancelled });
    return () => {
      cancelled = true;
    };
  }, []);

  return {
    run,
    runs,
    events,
    tasks,
    busy,
    error,
    start: (protocolPath) => startRunFlow(protocolPath, setters),
    cancel: () => cancelRunFlow(setters),
    refresh: (runId) => loadSnapshot(runId, setters),
    loadRun: async (runId) => {
      await loadSnapshot(runId, setters);
      setters.setRuns(await api.listRuns());
    },
  };
}
