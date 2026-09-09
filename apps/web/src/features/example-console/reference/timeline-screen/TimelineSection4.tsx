import visual from "../TimelineScreen.module.css";

interface TimelineSection4Props {
  task: {
    id: string;
    name: string;
    agent_id: string;
    status: string;
    start: number;
    end: number;
    attempt: number;
  };
  totalDuration: number;
  statusColor: string | undefined;
}

export function TimelineSection4({ task, totalDuration, statusColor }: TimelineSection4Props) {
  return (
    <div className={visual.surface16}>
      <div
        className={visual.overlay2}
        style={{
          left: `${String((task.start / totalDuration) * 100)}%`,
          width: `${String(((task.end - task.start) / totalDuration) * 100)}%`,
          background:
            task.status === "PENDING"
              ? "transparent"
              : task.status === "RUNNING"
                ? `linear-gradient(90deg, ${String(statusColor)}, ${String(statusColor)}66)`
                : statusColor,
          border: task.status === "PENDING" ? `1px dashed ${String(statusColor)}` : "none",
          boxShadow: task.status === "RUNNING" ? `0 0 12px ${String(statusColor)}44` : "none",
        }}
      />
      {task.status === "RUNNING" && (
        <div
          className={visual.overlay3}
          style={{
            left: `${String((task.start / totalDuration) * 100)}%`,
            width: `${String(((task.end - task.start) / totalDuration) * 100)}%`,
          }}
        />
      )}
    </div>
  );
}
