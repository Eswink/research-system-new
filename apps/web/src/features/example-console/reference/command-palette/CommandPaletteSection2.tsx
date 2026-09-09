import { type Dispatch, type RefObject, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import visual from "../CommandPalette.module.css";
import { Icon } from "../Icon";
import { CommandPaletteSection3 } from "./CommandPaletteSection3";

interface CommandPaletteSection2Props {
  inputRef: RefObject<HTMLInputElement | null>;
  q: string;
  setQ: Dispatch<SetStateAction<string>>;
  setHover: Dispatch<SetStateAction<number>>;
  t: (key: string, fallback?: string) => string;
  filtered: E.CommandItem[];
  grouped: Record<string, E.CommandItem[]>;
  hover: number;
  onClose: () => void;
}

export function CommandPaletteSection2({
  inputRef,
  q,
  setQ,
  setHover,
  t,
  filtered,
  grouped,
  hover,
  onClose,
}: CommandPaletteSection2Props) {
  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
      }}
      className={visual.column}
    >
      <div className={visual.row2}>
        <Icon name="search" size={14} className={visual.surface} />
        <input
          ref={inputRef}
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setHover(0);
          }}
          placeholder={t("pal.placeholder", "Type a command, search anything…")}
          className={visual.field}
        />
        <kbd>ESC</kbd>
      </div>
      <CommandPaletteSection3 {...{ filtered, t, grouped, hover, setHover, onClose }} />
      <div className={visual.row4}>
        <span>
          <kbd>↑</kbd> <kbd>↓</kbd> {t("pal.navigate", "navigate")} · <kbd>↵</kbd>{" "}
          {t("pal.select", "select")} · <kbd>esc</kbd> {t("pal.close", "close")}
        </span>
        <span>
          {filtered.length} {t("pal.results", "results")}
        </span>
      </div>
    </div>
  );
}
