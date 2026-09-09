import type { CSSProperties } from "react";
import { glyphs } from "./protocolIconGlyphs";

interface Props {
  name?: string | undefined;
  size?: number;
  style?: CSSProperties | undefined;
  className?: string | undefined;
}

/** Shared SVG attributes; unknown design icon names remain visible as a neutral outline. */
export function PECustomIcon({ name, size = 10, style, className }: Props) {
  const shape = glyphs.get(name ?? "") ?? <circle cx="6" cy="6" r="4" />;
  const effectiveStyle =
    name === "spin" ? { ...style, animation: "spin 1s linear infinite" } : style;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 10 10"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={effectiveStyle}
      aria-hidden="true"
    >
      {shape}
    </svg>
  );
}
