import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import visual from "../CommandPalette.module.css";
import { Icon } from "../Icon";

interface CommandPaletteSection3Props {
  filtered: E.CommandItem[];
  t: (key: string, fallback?: string) => string;
  grouped: Record<string, E.CommandItem[]>;
  hover: number;
  setHover: Dispatch<SetStateAction<number>>;
  onClose: () => void;
}

export function CommandPaletteSection3({
  filtered,
  t,
  grouped,
  hover,
  setHover,
  onClose,
}: CommandPaletteSection3Props) {
  return (
    <div className={visual.surface2}>
      {filtered.length === 0 && (
        <div className={visual.label}>
          {t("pal.noMatches", 'No matches. Try "run", "budget", "approval", or "claim".')}
        </div>
      )}
      {Object.entries(grouped).map(([group, items]) => (
        <CommandGroup key={group} {...{ group, items, filtered, hover, setHover, onClose }} />
      ))}
    </div>
  );
}

interface CommandGroupProps {
  group: string;
  items: E.CommandItem[];
  filtered: E.CommandItem[];
  hover: number;
  setHover: Dispatch<SetStateAction<number>>;
  onClose: () => void;
}

function CommandGroup(props: CommandGroupProps) {
  return (
    <div>
      <div className={visual.caption}>{props.group}</div>
      {props.items.map((item) => {
        const index = props.filtered.indexOf(item);
        return <CommandItemRow key={item.label} {...{ item, index, ...props }} />;
      })}
    </div>
  );
}

function CommandItemRow(props: CommandGroupProps & { item: E.CommandItem; index: number }) {
  const active = props.index === props.hover;
  return (
    <div
      onMouseEnter={() => {
        props.setHover(props.index);
      }}
      onClick={() => {
        props.item.action();
        props.onClose();
      }}
      className={visual.row3}
      style={{
        background: active ? "var(--bg-hover)" : "transparent",
        borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
      }}
    >
      <Icon
        name={props.item.icon ?? "chevron-r"}
        size={12}
        style={{ color: active ? "var(--accent)" : "var(--fg-muted)" }}
      />
      <div className={visual.surface3}>
        <div className={visual.label2}>{props.item.label}</div>
        {props.item.hint && <div className={visual.caption2}>{props.item.hint}</div>}
      </div>
      {props.item.shortcut && <kbd>{props.item.shortcut}</kbd>}
    </div>
  );
}
