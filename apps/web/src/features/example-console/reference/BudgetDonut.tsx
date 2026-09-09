import type * as E from "../exampleTypes";

/** Reference: screens/ProtocolEditor.sections.jsx; EXAMPLE ONLY. */
export const BudgetDonut = ({
  reservations,
  cap,
  palette,
}: {
  reservations: E.Protocol["budget"]["reservations"];
  cap: number;
  palette: string[];
}) => {
  const total = cap;
  const r = 32,
    cx = 44,
    cy = 44,
    strokeW = 10;
  const circ = 2 * Math.PI * r;
  let acc = 0;
  return (
    <svg width="88" height="88" viewBox="0 0 88 88">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--bg-panel)" strokeWidth={strokeW} />
      {reservations.map((res, i) => {
        const frac = (res.minor || 0) / total;
        const dash = frac * circ;
        const offset = -acc * circ;
        acc += frac;
        return (
          <circle
            key={i}
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={palette[i % palette.length]}
            strokeWidth={strokeW}
            strokeDasharray={`${String(dash)} ${String(circ)}`}
            strokeDashoffset={offset}
            transform={`rotate(-90 ${String(cx)} ${String(cy)})`}
            strokeLinecap="butt"
          />
        );
      })}
    </svg>
  );
};
