import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import { EventRow } from "../EventRow";
import visual from "../TimelineScreen.module.css";
import { TimelineSection8 } from "./TimelineSection8";

interface TimelineSection2Props {
  t: (key: string, fallback?: string) => string;
  filteredEvents: E.Event[];
  setFilter: Dispatch<SetStateAction<string>>;
  filter: string;
  selectedEvent: E.Event | null;
  setSelectedEvent: Dispatch<SetStateAction<E.Event | null>>;
  autoScroll: boolean;
  setAutoScroll: Dispatch<SetStateAction<boolean>>;
}

export function TimelineSection2({
  t,
  filteredEvents,
  setFilter,
  filter,
  selectedEvent,
  setSelectedEvent,
  autoScroll,
  setAutoScroll,
}: TimelineSection2Props) {
  return (
    <div className={`panel ${visual.panel3 ?? ""}`}>
      <TimelineSection8 {...{ t, filteredEvents, setFilter, filter }} />
      <div className={visual.surface18}>
        {filteredEvents.map((ev, i) => (
          <EventRow
            key={ev.event_id}
            ev={ev}
            selected={selectedEvent?.event_id === ev.event_id}
            onClick={() => {
              setSelectedEvent(ev);
            }}
            isLatest={i === filteredEvents.length - 1}
          />
        ))}
      </div>
      <div className={visual.row11}>
        <span>
          {t("tl.cursor")} evt_01K5FZ8H015 · {t("tl.resumable")}
        </span>
        <label className={visual.row12}>
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => {
              setAutoScroll(e.target.checked);
            }}
            className={visual.field}
          />
          {t("tl.autoScroll")}
        </label>
      </div>
    </div>
  );
}
