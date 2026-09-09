import { useEffect, useMemo, useRef, useState, type Dispatch, type SetStateAction } from "react";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { CommandPaletteSection } from "./command-palette/CommandPaletteSection";

export const CommandPalette = ({
  open,
  onClose,
  items = [],
}: {
  open: boolean;
  onClose: () => void;
  items?: E.CommandItem[];
}) => {
  const { t } = useI18n();
  const [q, setQ] = useState("");
  const [hover, setHover] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const filtered = useMemo(() => filterCommands(items, q), [q, items]);

  useEffect(() => {
    if (open) {
      setQ("");
      setHover(0);
      setTimeout(() => inputRef.current?.focus(), 40);
    }
  }, [open]);
  usePaletteKeyboard({ open, onClose, filtered, hover, setHover });

  if (!open) return null;
  const grouped: Record<string, E.CommandItem[]> = {};
  filtered.forEach((it) => {
    const g = it.section ?? "Actions";
    (grouped[g] ??= []).push(it);
  });

  return (
    <CommandPaletteSection
      {...{ onClose, inputRef, q, setQ, setHover, t, filtered, grouped, hover }}
    />
  );
};

function filterCommands(items: E.CommandItem[], query: string): E.CommandItem[] {
  const normalized = query.toLowerCase().trim();
  if (normalized === "") return items;
  return items.filter((item) =>
    [item.label, item.hint ?? "", item.section ?? ""].join(" ").toLowerCase().includes(normalized),
  );
}

interface PaletteKeyboardProps {
  open: boolean;
  onClose: () => void;
  filtered: E.CommandItem[];
  hover: number;
  setHover: Dispatch<SetStateAction<number>>;
}

function usePaletteKeyboard(props: PaletteKeyboardProps): void {
  useEffect(() => {
    if (!props.open) return;
    const handleKey = (event: KeyboardEvent) => {
      handlePaletteKey(event, props);
    };
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("keydown", handleKey);
    };
  });
}

function handlePaletteKey(event: KeyboardEvent, props: PaletteKeyboardProps): void {
  const selected = props.filtered[props.hover];
  if (event.key === "Escape") props.onClose();
  if (event.key === "ArrowDown") {
    event.preventDefault();
    props.setHover((value) => Math.min(props.filtered.length - 1, value + 1));
  }
  if (event.key === "ArrowUp") {
    event.preventDefault();
    props.setHover((value) => Math.max(0, value - 1));
  }
  if (event.key === "Enter" && selected !== undefined) {
    selected.action();
    props.onClose();
  }
}
