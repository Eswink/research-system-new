import type { ReactNode } from "react";

/** Frozen design paths; no runtime dispatch or generated markup. */
export const glyphs: ReadonlyMap<string, ReactNode> = new Map<string, ReactNode>([
  [
    "check",
    <>
      <path d="M2.5 6.5 L5 9 L9.5 3.5" />
    </>,
  ],
  [
    "x",
    <>
      <path d="M3 3 L9 9 M9 3 L3 9" />
    </>,
  ],
  [
    "warn-tri",
    <>
      <path d="M6 1.5 L11 10.5 L1 10.5 Z" />
      <path d="M6 5 V7.5" strokeWidth="1.6" />
      <circle cx="6" cy="9" r="0.4" fill="currentColor" stroke="none" />
    </>,
  ],
  [
    "hex",
    <>
      <path d="M6 1.2 L10.2 3.6 V8.4 L6 10.8 L1.8 8.4 V3.6 Z" />
    </>,
  ],
  [
    "diamond",
    <>
      <path d="M6 1.5 L10.5 6 L6 10.5 L1.5 6 Z" />
    </>,
  ],
  [
    "circle-o",
    <>
      <circle cx="6" cy="6" r="4" />
    </>,
  ],
  [
    "circle",
    <>
      <circle cx="6" cy="6" r="4" fill="currentColor" stroke="none" />
    </>,
  ],
  [
    "circle-dash",
    <>
      <circle cx="6" cy="6" r="4" strokeDasharray="1.5 1.5" />
    </>,
  ],
  [
    "square",
    <>
      <rect x="2" y="2" width="8" height="8" rx="1" />
    </>,
  ],
  [
    "q",
    <>
      <circle cx="6" cy="6" r="4" />
      <path d="M4.6 5 A1.4 1.4 0 1 1 6 6.6 V7.4" />
      <circle cx="6" cy="9.2" r="0.35" fill="currentColor" stroke="none" />
    </>,
  ],
  [
    "play",
    <>
      <path d="M3.5 2.5 L9.5 6 L3.5 9.5 Z" fill="currentColor" stroke="none" />
    </>,
  ],
  [
    "pause",
    <>
      <rect x="3.2" y="2.8" width="1.8" height="6.4" fill="currentColor" stroke="none" />
      <rect x="7" y="2.8" width="1.8" height="6.4" fill="currentColor" stroke="none" />
    </>,
  ],
  [
    "stop",
    <>
      <rect x="3" y="3" width="6" height="6" fill="currentColor" stroke="none" />
    </>,
  ],
  [
    "fork",
    <>
      <circle cx="3" cy="2.5" r="1" />
      <circle cx="9" cy="2.5" r="1" />
      <circle cx="6" cy="10" r="1" />
      <path d="M3 3.5 V6.5 A1.5 1.5 0 0 0 4.5 8 H7.5 A1.5 1.5 0 0 0 9 6.5 V3.5" />
      <path d="M6 8 V9" />
    </>,
  ],
  [
    "copy",
    <>
      <rect x="4" y="4" width="6" height="6" rx="1" />
      <path d="M2 8 V3 A1 1 0 0 1 3 2 H8" />
    </>,
  ],
  [
    "external",
    <>
      <path d="M7 2 H10 V5" />
      <path d="M10 2 L5.5 6.5" />
      <path
        d={[
          "M9 7.5 V9.5 A0.5 0.5 0 0 1 8.5 10 H2.5 A0.5 0.5 0 0 1 2 9.5 ",
          "V3.5 A0.5 0.5 0 0 1 2.5 3 H4.5",
        ].join("")}
      />
    </>,
  ],
  [
    "chevron-r",
    <>
      <path d="M4.5 2.5 L8 6 L4.5 9.5" />
    </>,
  ],
  [
    "chevron-d",
    <>
      <path d="M2.5 4.5 L6 8 L9.5 4.5" />
    </>,
  ],
  [
    "search",
    <>
      <circle cx="5" cy="5" r="3" />
      <path d="M7.2 7.2 L10 10" />
    </>,
  ],
  [
    "plus",
    <>
      <path d="M6 2.5 V9.5 M2.5 6 H9.5" />
    </>,
  ],
  [
    "lock",
    <>
      <rect x="2.5" y="5.5" width="7" height="5" rx="0.6" />
      <path d="M4 5.5 V4 A2 2 0 0 1 8 4 V5.5" />
    </>,
  ],
  [
    "dot",
    <>
      <circle cx="6" cy="6" r="2" fill="currentColor" stroke="none" />
    </>,
  ],
  [
    "ban",
    <>
      <circle cx="6" cy="6" r="4" />
      <path d="M3.2 3.2 L8.8 8.8" />
    </>,
  ],
  [
    "clock",
    <>
      <circle cx="6" cy="6" r="4" />
      <path d="M6 3.5 V6 L7.6 7.6" />
    </>,
  ],
  [
    "spin",
    <>
      <path d="M6 2 A4 4 0 1 1 2 6" />
    </>,
  ],
  [
    "wifi",
    <>
      <path d="M1.5 4.5 A6 6 0 0 1 10.5 4.5" />
      <path d="M3 6.3 A4 4 0 0 1 9 6.3" />
      <path d="M4.5 8 A2 2 0 0 1 7.5 8" />
      <circle cx="6" cy="9.5" r="0.5" fill="currentColor" stroke="none" />
    </>,
  ],
  [
    "wifi-off",
    <>
      <path d="M1.5 4.5 A6 6 0 0 1 3.5 3.2" />
      <path d="M8.5 3.2 A6 6 0 0 1 10.5 4.5" />
      <path d="M4.5 8 A2 2 0 0 1 7.5 8" />
      <path d="M1.5 1.5 L10.5 10.5" />
    </>,
  ],
  [
    "shield",
    <>
      <path d="M6 1.5 L10 3 V6.5 C10 8.5 8 10 6 10.5 C4 10 2 8.5 2 6.5 V3 Z" />
    </>,
  ],
  [
    "eye-off",
    <>
      <path d="M2 2 L10 10" />
      <path d="M2.5 6.5 C4 4.5 4 4.5 6 4.5 C7 4.5 8 5 9.5 6.5" />
      <circle cx="6" cy="6.5" r="1.2" />
    </>,
  ],
  [
    "flask",
    <>
      <path d="M4.5 2 V4.5 L2.5 9 A1 1 0 0 0 3.5 10.5 H8.5 A1 1 0 0 0 9.5 9 L7.5 4.5 V2" />
      <path d="M4 2 H8" />
      <path d="M3.5 7 H8.5" />
    </>,
  ],
  [
    "book",
    <>
      <path d="M2 2.5 H5.5 A1 1 0 0 1 6 3 V9.5 A0.5 0.5 0 0 1 5.5 10 H2 Z" />
      <path d="M6 3 A1 1 0 0 1 6.5 2.5 H10 V9.5 A0.5 0.5 0 0 1 9.5 10 H6" />
    </>,
  ],
  [
    "graph",
    <>
      <circle cx="3" cy="3" r="1.2" />
      <circle cx="9" cy="4" r="1.2" />
      <circle cx="6" cy="9" r="1.2" />
      <path d="M4 3.4 L8 3.8" />
      <path d="M3.4 4 L5.4 8" />
      <path d="M8.4 5 L6.6 8" />
    </>,
  ],
  [
    "menu",
    <>
      <path d="M2 3.5 H10 M2 6 H10 M2 8.5 H10" />
    </>,
  ],
]);
