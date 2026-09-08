import { useEffect, useState } from "react";

import type { RunEventDto } from "../../api/types";

export interface EventStreamState {
  events: RunEventDto[];
  connected: boolean;
  reconnecting: boolean;
}

/** 服务端 run_events.py 实际发出的具名 event: 帧（带 run_id 且有发布点）。 */
export const NAMED_SSE_EVENTS = [
  "manifest.frozen",
  "task.created",
  "task.leased",
  "task.completed",
  "task.retry_scheduled",
  "task.cancelled",
  "run.completed",
  "run.failed",
  "claim.verified",
  "claim.disputed",
  "approval.decided",
] as const;

export function mergeEvents(replay: RunEventDto[], live: RunEventDto[]): RunEventDto[] {
  /** replay + SSE 增量合并：按 event_id 去重；live 中 ≤ 最后 replay
   * event_id 的迟到事件丢弃（cursor 语义，与服务端 Last-Event-ID 一致）。 */
  const lastReplayId = replay.length > 0 ? replay[replay.length - 1]?.event_id ?? "" : "";
  const seen = new Set(replay.map((event) => event.event_id));
  const merged: RunEventDto[] = [...replay];
  for (const event of live) {
    if (seen.has(event.event_id)) {
      continue;
    }
    if (lastReplayId !== "" && event.event_id <= lastReplayId) {
      continue;
    }
    seen.add(event.event_id);
    merged.push(event);
  }
  return merged;
}

/**
 * Run 事件流（T18）：浏览器 EventSource 消费后端具名 SSE 帧。
 *
 * - 后端契约：`GET /runs/{id}/events`（Accept: text/event-stream），帧带
 *   `id:`（event_id）与具名 `event:`；onmessage 只收默认 message，因此必须
 *   按事件名 addEventListener（原生 EventSource 行为）。
 * - 浏览器原生重连自动发送 Last-Event-ID，后端按 cursor 续传。
 * - 客户端去重：按 event_id 维护已见集合，迟到/越界事件丢弃。
 */
export function useRunEventStream(runId: string | null): EventStreamState {
  const [events, setEvents] = useState<RunEventDto[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (runId === null) {
      return;
    }
    const seen = new Set<string>();
    setEvents([]);
    setConnected(false);
    const source = new EventSource(`/api/runs/${encodeURIComponent(runId)}/events`);
    source.onopen = () => {
      setConnected(true);
    };
    const handle = (message: MessageEvent<string>): void => {
      const event = parseEventFrame(message);
      if (event === null || seen.has(event.event_id)) {
        return;
      }
      seen.add(event.event_id);
      setEvents((current) => [...current, event]);
    };
    for (const name of NAMED_SSE_EVENTS) {
      source.addEventListener(name, handle as EventListener);
    }
    source.onerror = () => {
      setConnected(false);
    };
    return () => {
      source.close();
    };
  }, [runId]);

  return { events, connected, reconnecting: !connected };
}

function parseEventFrame(message: MessageEvent<string>): RunEventDto | null {
  try {
    const parsed = JSON.parse(message.data) as Partial<RunEventDto> | null;
    if (parsed === null || typeof parsed.event_id !== "string" || typeof parsed.type !== "string") {
      return null;
    }
    return {
      event_id: parsed.event_id,
      type: parsed.type,
      schema_version: parsed.schema_version ?? "",
      occurred_at: parsed.occurred_at ?? "",
      actor: parsed.actor ?? "",
      scope: parsed.scope ?? "",
      run_id: parsed.run_id ?? null,
      task_id: parsed.task_id ?? null,
      trace_id: parsed.trace_id ?? null,
      payload: parsed.payload ?? {},
    };
  } catch {
    return null;
  }
}
