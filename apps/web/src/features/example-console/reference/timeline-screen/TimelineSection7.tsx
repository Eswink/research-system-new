import visual from "../TimelineScreen.module.css";

interface TimelineSection7Props {
  totalDuration: number;
}

export function TimelineSection7({ totalDuration }: TimelineSection7Props) {
  return (
    <div className={visual.surface11}>
      <div className={visual.row7}>
        {[0, 10, 20, 30, 40, 50, 60, 70].map((t) => (
          <span key={t}>+{String(t).padStart(2, "0")}m</span>
        ))}
      </div>
      <div className={visual.surface12}>
        {/* Now indicator at 68m */}
        <div
          className={visual.overlay}
          style={{ left: `${String((68 / totalDuration) * 100)}%` }}
        />
        <div className={visual.caption} style={{ left: `${String((68 / totalDuration) * 100)}%` }}>
          NOW
        </div>
      </div>
    </div>
  );
}
