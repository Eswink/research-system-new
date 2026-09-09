import type * as E from "../../exampleTypes";
import { DigestText } from "../DigestText";
import visual from "../EventDrawer.module.css";
import { Icon } from "../Icon";
import { EventDrawerEvActor2 } from "./EventDrawerEvActor2";

interface EventDrawerEvActorProps {
  typeStyle: { icon: string; color: string };
  ev: E.Event;
  onClose: () => void;
  t: (key: string, fallback?: string) => string;
  agent: E.Agent | null | undefined;
  model: E.Model | null | undefined;
}

export function EventDrawerEvActor({
  typeStyle,
  ev,
  onClose,
  t,
  agent,
  model,
}: EventDrawerEvActorProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name={typeStyle.icon} size={13} style={{ color: typeStyle.color }} />
        <span className={`mono ${visual.label ?? ""}`} style={{ color: typeStyle.color }}>
          {ev.type}
        </span>
        <DigestText value={ev.event_id} label="event:" length={16} />
        <DigestText value={ev.trace_id} label="trace:" length={10} />
        <span className={visual.label2}>{ev.occurred_at}</span>
        <button className={`btn sm ghost ${visual.action ?? ""}`} onClick={onClose}>
          <Icon name="x" size={10} />
        </button>
      </div>
      <EventDrawerEvActor2 {...{ t, ev, agent, model }} />
      <div className={visual.surface}>
        <div className={visual.row2}>
          <Icon name="eye-off" size={10} /> {t("tl.evPayload")}
          <span className={visual.surface2}>{t("tl.evRedacted")}</span>
        </div>
        <pre className={visual.label3}>{JSON.stringify(ev.payload, null, 2)}</pre>
      </div>
    </div>
  );
}
