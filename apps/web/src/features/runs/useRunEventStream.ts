import { useEffect, useState } from "react";

import type { RunEventDto } from "../../api/types";

export interface EventStreamState {
  events: RunEventDto[];
  connected: boolean;
  reconnecting: boolean;
}

export function mergeEvents(
  replay: RunEventDto[],
  live: RunEventDto[],
): RunEventDto[] {
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
 * Run 事件流（M13-R1 WP-M4）：浏览器 EventSource 消费后端 SSE。
 *
 * - 后端契约：`GET /runs/{id}/events`（Accept: text/event-stream），
 *   帧带 `id:`（event_id）；浏览器原生重连自动发送 Last-Event-ID，
 *   后端按 cursor 续传（重复事件由服务端按 event_id 去重过滤）。
 * - 客户端去重：按 event_id 维护已见集合，迟到/越界事件丢弃。
 * - 首屏由 JSON replay 提供（useRunPanel）；本 hook 接管增量。
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
    source.onmessage = (message) => {
      const event = parseEventFrame(message);
      if (event === null || seen.has(event.event_id)) {
        return;
      }
      seen.add(event.event_id);
      setEvents((current) => [...current, event]);
    };
    source.onerror = () => {
      setConnected(false);
    };
    return () => {
      source.close();
    };
  }, [runId]);

  return { events, connected, reconnecting: !connected };
}

function parseEventFrame(message: MessageEvent<unknown>): RunEventDto | null {
  try {
    const parsed = JSON.parse(String(message.data)) as Partial<RunEventDto> | null;
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
