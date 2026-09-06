import type { RunEventDto } from "../../api/types";

const eventLabel = (type: string): string => {
  return type.replaceAll(".", " ");
};

export function TimelineView({ events }: { events: RunEventDto[] }) {
  return (
    <div data-testid="run-timeline">
      <h3>Timeline</h3>
      <ol>
        {events.map((event) => (
          <li key={event.event_id}>
            <time>{event.occurred_at}</time>{" "}
            <strong>{eventLabel(event.type)}</strong>
            {event.task_id !== null ? ` · task ${event.task_id.slice(0, 8)}` : ""}
            <span className="event-payload">{JSON.stringify(event.payload)}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}