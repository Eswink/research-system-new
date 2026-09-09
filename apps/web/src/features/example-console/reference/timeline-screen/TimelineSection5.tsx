import visual from "../TimelineScreen.module.css";
import { TimelineSection9 } from "./TimelineSection9";

interface TimelineSection5Props {
  t: (key: string, fallback?: string) => string;
  liveState: string;
}

export function TimelineSection5({ t, liveState }: TimelineSection5Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <TimelineSection9 {...{ t, liveState }} />
    </div>
  );
}
