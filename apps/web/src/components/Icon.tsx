/** 12px 内联 SVG 图标（currentColor；状态四重编码中的"图标"通道）。 */

export type IconName =
  | "book"
  | "check"
  | "x"
  | "warn-tri"
  | "hex"
  | "diamond"
  | "circle-o"
  | "dot"
  | "q"
  | "play"
  | "plus"
  | "lock"
  | "ban"
  | "shield"
  | "flask"
  | "graph"
  | "copy"
  | "chevron-r"
  | "chevron-d"
  | "external"
  | "fork"
  | "edit"
  | "code"
  | "menu";

const PATHS: Record<IconName, string> = {
  book: "M2 2.5h4a2 2 0 0 1 2 2v7a1.5 1.5 0 0 0-1.5-1.5H2zM10 2.5H8.5A2 2 0 0 0 7 3.5M10 2.5v8.5H7",
  check: "M2.5 6.5 4.5 8.5 9.5 3",
  x: "M2.5 2.5 9.5 9.5M9.5 2.5 2.5 9.5",
  "warn-tri": "M6 1.5 11 10H1zM6 4.5v3M6 8.6v.4",
  hex: "M6 1 10.5 3.5v5L6 11 1.5 8.5v-5zM6 4v4M4 5l4 2M8 5 4 7",
  diamond: "M6 1 11 6 6 11 1 6z",
  "circle-o":
    "M6 1.5A4.5 4.5 0 1 1 6 10.5 4.5 4.5 0 0 1 6 1.5zM6 4A2 2 0 1 1 6 8 2 2 0 0 1 6 4z",
  dot: "M6 4.5A1.5 1.5 0 1 1 6 7.5 1.5 1.5 0 0 1 6 4.5z",
  q: "M4 3.5A2 2 0 1 1 6 6v1.2M6 9.4v.3",
  play: "M3 2.5 9.5 6 3 9.5z",
  plus: "M6 2v8M2 6h8",
  lock: "M3.5 5V3.8A2.5 2.5 0 0 1 8.5 3.8V5M2.5 5h7v5h-7z",
  ban: "M6 1.5A4.5 4.5 0 1 1 6 10.5 4.5 4.5 0 0 1 6 1.5zM3 9 9 3",
  shield: "M6 1 10 2.5v3.5c0 2.2-1.7 3.7-4 4.5-2.3-.8-4-2.3-4-4.5V2.5zM4 5.5l1.5 1.5L8.5 4",
  flask:
    "M4.5 1.5h3M5 1.5v3L2.5 9a1.6 1.6 0 0 0 1.4 2.5h4.2A1.6 1.6 0 0 0 9.5 9L7 4.5v-3M3.6 7.5h4.8",
  graph: "M1.5 10.5h9M3 10V6.5M6 10V3.5M9 10V5",
  copy: "M3.5 3.5h5v5h-5zM5.5 1.5h5v5",
  "chevron-r": "M4 2.5 7.5 6 4 9.5",
  "chevron-d": "M2.5 4 6 7.5 9.5 4",
  external: "M6.5 2.5H9.5V5.5M9.5 2.5 5 7M7.5 8.5v1.5h-6v-6H3",
  fork: "M3 1.5v3a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-3M6 6.5v4M3.5 10.5h5",
  edit: "M6 2 8 4 4 8 1.5 8.5 2 6z",
  code: "M4 2.5 1.5 5 4 7.5M6 2.5 8.5 5 6 7.5",
  menu: "M2 3.5h8M2 6h8M2 8.5h8",
};

export function Icon({
  name,
  size = 12,
  className,
}: {
  name: IconName;
  size?: number;
  className?: string | undefined;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
