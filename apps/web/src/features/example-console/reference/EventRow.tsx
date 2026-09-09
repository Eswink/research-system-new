import FIX_AGENTS from "../data/agents.json";
import type * as E from "../exampleTypes";
import visual from "./EventRow.module.css";
import { Icon } from "./Icon";
import { getEventSummary } from "./getEventSummary";
import { getEventTypeStyle } from "./getEventTypeStyle";

/** Reference: screens/Timeline.jsx; EXAMPLE ONLY. */
export const EventRow = ({
  ev,
  selected,
  onClick,
  isLatest,
}: {
  ev: E.Event;
  selected: boolean;
  onClick: () => void;
  isLatest?: boolean;
}) => {
  const typeStyle = getEventTypeStyle(ev.type);
  const actorLabel =
    ev.actor.kind === "agent"
      ? (FIX_AGENTS.find((a) => a.id === ev.actor.id)?.name ?? ev.actor.id)
      : ev.actor.kind === "tool"
        ? ev.actor.id
        : ev.actor.kind === "policy"
          ? "policy"
          : ev.actor.kind === "user"
            ? ev.actor.id
            : "system";
  return (
    <div
      onClick={onClick}
      className={visual.grid}
      style={{
        background: selected ? "var(--bg-hover)" : "transparent",
        animation: isLatest ? "stream-in 400ms ease-out" : undefined,
      }}
    >
      <span className={visual.caption}>{ev.occurred_at.slice(11, 19)}</span>
      <Icon name={typeStyle.icon} size={11} style={{ color: typeStyle.color }} />
      <div className={visual.row}>
        <span className={`mono ${visual.label ?? ""}`} style={{ color: typeStyle.color }}>
          {ev.type}
        </span>
        <span className={visual.label2}>{getEventSummary(ev)}</span>
      </div>
      <span className={visual.caption2}>{actorLabel}</span>
    </div>
  );
};
