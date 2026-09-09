import { type Dispatch, type RefObject, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import visual from "../CommandPalette.module.css";
import { CommandPaletteSection2 } from "./CommandPaletteSection2";

interface CommandPaletteSectionProps {
  onClose: () => void;
  inputRef: RefObject<HTMLInputElement | null>;
  q: string;
  setQ: Dispatch<SetStateAction<string>>;
  setHover: Dispatch<SetStateAction<number>>;
  t: (key: string, fallback?: string) => string;
  filtered: E.CommandItem[];
  grouped: Record<string, E.CommandItem[]>;
  hover: number;
}

export function CommandPaletteSection({
  onClose,
  inputRef,
  q,
  setQ,
  setHover,
  t,
  filtered,
  grouped,
  hover,
}: CommandPaletteSectionProps) {
  return (
    <div className={visual.row} onClick={onClose}>
      <CommandPaletteSection2
        {...{ inputRef, q, setQ, setHover, t, filtered, grouped, hover, onClose }}
      />
    </div>
  );
}
