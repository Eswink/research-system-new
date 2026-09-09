import { useState } from "react";
import type { RunEventDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { Drawer } from "../../components/Drawer";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

export function TimelineView({ events }: { events: RunEventDto[] }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [filter, setFilter] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = events.find((event) => event.event_id === selectedId);
  const filtered = events.filter((event) =>
    `${event.type} ${event.actor} ${event.task_id ?? ""}`
      .toLocaleLowerCase()
      .includes(filter.trim().toLocaleLowerCase()),
  );
  return (
    <div data-testid="run-timeline">
      <PanelSection
        title={zh ? "事件时间线" : "Event timeline"}
        count={events.length}
        extra={
          <input
            type="search"
            className="input"
            value={filter}
            aria-label={zh ? "筛选事件" : "Filter events"}
            placeholder={zh ? "按类型、Actor、Task 筛选" : "Filter type, actor, task"}
            onChange={(event) => {
              setFilter(event.target.value);
            }}
          />
        }
      >
        <EventRows events={filtered} onSelect={setSelectedId} selectedId={selectedId} />
      </PanelSection>
      <Drawer
        open={selected !== undefined}
        onClose={() => {
          setSelectedId(null);
        }}
        title={zh ? "正式事件详情" : "Persisted event details"}
      >
        {selected !== undefined && <EventDetails event={selected} />}
      </Drawer>
    </div>
  );
}

function EventRows({
  events,
  selectedId,
  onSelect,
}: {
  events: RunEventDto[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const { language } = useI18n();
  if (events.length === 0)
    return (
      <EmptyState
        message={language === "zh" ? "没有匹配的正式事件" : "No matching persisted events"}
      />
    );
  return (
    <ol className={styles.list}>
      {events.map((event) => (
        <li key={event.event_id}>
          <button
            type="button"
            className={styles.listButton}
            aria-pressed={selectedId === event.event_id}
            onClick={() => {
              onSelect(event.event_id);
            }}
          >
            <div className={styles.cardHead}>
              <strong>{event.type}</strong>
              <time dateTime={event.occurred_at} className="mono muted">
                {event.occurred_at}
              </time>
            </div>
            <Chip>{event.actor}</Chip> <span className="mono">{event.task_id ?? event.scope}</span>
          </button>
        </li>
      ))}
    </ol>
  );
}

function EventDetails({ event }: { event: RunEventDto }) {
  return (
    <div className={styles.page}>
      <KeyValueList
        fields={[
          { label: "Event", value: event.event_id },
          { label: "Type", value: event.type },
          { label: "Schema", value: event.schema_version },
          { label: "Timestamp", value: event.occurred_at },
          { label: "Run", value: event.run_id ?? "—" },
          { label: "Task", value: event.task_id ?? "—" },
          { label: "Trace", value: event.trace_id ?? "—" },
          { label: "Actor", value: event.actor },
        ]}
      />
      <pre className={styles.code}>{JSON.stringify(event.payload, null, 2)}</pre>
    </div>
  );
}
