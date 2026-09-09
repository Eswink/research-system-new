interface ClaimsGraphrectProps {
  pos: { x: number; y: number };
  isProposed: boolean;
  statusColor: string | undefined;
  selected: boolean;
}

export function ClaimsGraphrect({ pos, isProposed, statusColor, selected }: ClaimsGraphrectProps) {
  return (
    <rect
      x={pos.x - 88}
      y={pos.y - 26}
      width={176}
      height={52}
      rx={4}
      fill={isProposed ? "transparent" : "var(--bg-panel)"}
      stroke={statusColor}
      strokeWidth={selected ? 2 : 1}
      strokeDasharray={isProposed ? "3 3" : undefined}
      opacity={isProposed ? 0.75 : 1}
    />
  );
}
