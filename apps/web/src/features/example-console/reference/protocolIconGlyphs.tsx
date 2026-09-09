import type { ReactNode } from "react";

/** Frozen design paths; no runtime dispatch or generated markup. */
export const glyphs: ReadonlyMap<string, ReactNode> = new Map<string, ReactNode>([
  [
    "edit",
    <>
      <path d="M6 2 L8 4 L4 8 L1.5 8.5 L2 6 Z" />
    </>,
  ],
  [
    "code",
    <>
      <path d="M4 2.5 L1.5 5 L4 7.5" />
      <path d="M6 2.5 L8.5 5 L6 7.5" />
    </>,
  ],
]);
