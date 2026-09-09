import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import visual from "../TimelineScreen.module.css";
import { TimelineSection2 } from "./TimelineSection2";
import { TimelineSection6 } from "./TimelineSection6";

interface TimelineSection3Props {
  t: (key: string, fallback?: string) => string;
  totalDuration: number;
  filteredEvents: E.Event[];
  setFilter: Dispatch<SetStateAction<string>>;
  filter: string;
  selectedEvent: E.Event | null;
  setSelectedEvent: Dispatch<SetStateAction<E.Event | null>>;
  autoScroll: boolean;
  setAutoScroll: Dispatch<SetStateAction<boolean>>;
}

export function TimelineSection3({
  t,
  totalDuration,
  filteredEvents,
  setFilter,
  filter,
  selectedEvent,
  setSelectedEvent,
  autoScroll,
  setAutoScroll,
}: TimelineSection3Props) {
  return (
    <div className={visual.grid}>
      {/* Swimlanes */}
      <TimelineSection6 {...{ t, totalDuration }} />

      {/* Event stream */}
      <TimelineSection2
        {...{
          t,
          filteredEvents,
          setFilter,
          filter,
          selectedEvent,
          setSelectedEvent,
          autoScroll,
          setAutoScroll,
        }}
      />
    </div>
  );
}
