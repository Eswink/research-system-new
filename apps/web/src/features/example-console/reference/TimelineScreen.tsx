import { useState } from "react";
import FIX_EVENTS from "../data/events.json";
import type * as E from "../exampleTypes";
import { requiredExample } from "../requiredExample";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { EventDrawer } from "./EventDrawer";
import { TimelineSection3 } from "./timeline-screen/TimelineSection3";
import { TimelineSection5 } from "./timeline-screen/TimelineSection5";
import visual from "./TimelineScreen.module.css";

export const TimelineScreen = () => {
  const { t } = useI18n();
  const [selectedEvent, setSelectedEvent] = useState<E.Event | null>(
    requiredExample(FIX_EVENTS[3]),
  ); // tool.called (has model + cost + latency)
  const [filter, setFilter] = useState("all");
  const liveState = "live"; // live | reconnecting | behind
  const [autoScroll, setAutoScroll] = useState(true);

  const filteredEvents =
    filter === "all" ? FIX_EVENTS : FIX_EVENTS.filter((e) => e.type.startsWith(filter));
  const totalDuration = 72; // phase units

  return (
    <div className={visual.column}>
      {/* ── Top status bar ─────────────────────────────── */}
      <TimelineSection5 {...{ t, liveState }} />

      {/* ── Middle: Swimlanes + Event stream ──────────── */}
      <TimelineSection3
        {...{
          t,
          totalDuration,
          filteredEvents,
          setFilter,
          filter,
          selectedEvent,
          setSelectedEvent,
          autoScroll,
          setAutoScroll,
        }}
      />

      {/* ── Bottom drawer: event detail ─────────────────── */}
      {selectedEvent && (
        <EventDrawer
          ev={selectedEvent}
          onClose={() => {
            setSelectedEvent(null);
          }}
        />
      )}
    </div>
  );
};
