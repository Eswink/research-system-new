import { useEffect, useMemo, useRef, useState } from "react";

import { Icon, type IconName } from "../components/Icon";
import { useI18n } from "../i18n/useI18n";
import type { TranslationKey } from "../i18n/zh";
import { DOMAINS, routeToHash } from "../navigation/registry";
import styles from "./CommandPalette.module.css";

export interface PaletteItem {
  section: string;
  icon: IconName;
  label: string;
  hint: string;
  hash: string;
}

function pageItems(t: (key: TranslationKey) => string): PaletteItem[] {
  return DOMAINS.flatMap((d) =>
    d.pages.map((p) => ({
      section: t(`dom.${d.id}` as TranslationKey),
      icon: d.icon,
      label: t(`page.${d.id}.${p}` as TranslationKey),
      hint: `${d.id}/${p}`,
      hash: routeToHash({ domain: d.id, page: p }),
    })),
  );
}

function filterItems(items: readonly PaletteItem[], query: string): readonly PaletteItem[] {
  const q = query.trim().toLowerCase();
  if (q === "") {
    return items;
  }
  return items.filter(
    (item) => item.label.toLowerCase().includes(q) || item.hint.toLowerCase().includes(q),
  );
}

/**
 * 命令面板（⌘K）：只搜索已注册页面与已加载真实对象。
 * 对象搜索由调用方注入 extraItems（T07 扩展）。
 */
export interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onNavigate: (hash: string) => void;
  extraItems?: readonly PaletteItem[];
}

export function CommandPalette(props: CommandPaletteProps) {
  const { open, onClose, onNavigate, extraItems = [] } = props;
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const items = useMemo(() => [...pageItems(t), ...extraItems], [t, extraItems]);
  const filtered = useMemo(() => filterItems(items, query), [items, query]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setIndex(0);
      inputRef.current?.focus();
    }
  }, [open]);

  if (!open) {
    return null;
  }
  return (
    <PaletteDialog
      t={t}
      onClose={onClose}
      inputRef={inputRef}
      query={query}
      onQuery={(value) => { setQuery(value); setIndex(0); }}
      filtered={filtered}
      index={index}
      onMove={(delta) => {
        setIndex((i) => Math.max(0, Math.min(i + delta, filtered.length - 1)));
      }}
      onSelect={(item) => {
        if (item !== undefined) {
          onNavigate(item.hash);
          onClose();
        }
      }}
    />
  );
}

interface PaletteDialogProps {
  t: (key: TranslationKey) => string;
  onClose: () => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  query: string;
  onQuery: (value: string) => void;
  filtered: readonly PaletteItem[];
  index: number;
  onMove: (delta: number) => void;
  onSelect: (item: PaletteItem | undefined) => void;
}

function PaletteDialog(props: PaletteDialogProps) {
  const { t, onClose, inputRef, query, onQuery, filtered, index, onMove, onSelect } = props;
  return (
    <div className={styles.scrim} onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={t("app.search")}
        className={styles.panel}
        onClick={(event) => { event.stopPropagation(); }}
      >
        <PaletteInput
          inputRef={inputRef}
          query={query}
          placeholder={t("palette.placeholder")}
          onQuery={onQuery}
          onMove={onMove}
          onEnter={() => { onSelect(filtered[index]); }}
          onEscape={onClose}
        />
        <PaletteResults
          items={filtered}
          index={index}
          onSelect={onSelect}
          emptyLabel={t("palette.empty")}
        />
      </div>
    </div>
  );
}

function PaletteInput({
  inputRef,
  query,
  placeholder,
  onQuery,
  onMove,
  onEnter,
  onEscape,
}: {
  inputRef: React.RefObject<HTMLInputElement | null>;
  query: string;
  placeholder: string;
  onQuery: (value: string) => void;
  onMove: (delta: number) => void;
  onEnter: () => void;
  onEscape: () => void;
}) {
  return (
    <input
      ref={inputRef}
      className={styles.input}
      placeholder={placeholder}
      value={query}
      onChange={(event) => { onQuery(event.target.value); }}
      onKeyDown={(event) => {
        if (event.key === "ArrowDown") {
          event.preventDefault();
          onMove(1);
        } else if (event.key === "ArrowUp") {
          event.preventDefault();
          onMove(-1);
        } else if (event.key === "Enter") {
          onEnter();
        } else if (event.key === "Escape") {
          onEscape();
        }
      }}
    />
  );
}

function PaletteResults({
  items,
  index,
  onSelect,
  emptyLabel,
}: {
  items: readonly PaletteItem[];
  index: number;
  onSelect: (item: PaletteItem | undefined) => void;
  emptyLabel: string;
}) {
  return (
    <div className={styles.results}>
      {items.map((item, i) => (
        <button
          key={item.hash}
          type="button"
          className={i === index ? styles.rowActive : styles.row}
          onClick={() => { onSelect(item); }}
        >
          <Icon name={item.icon} size={12} />
          <span className={styles.rowLabel}>{item.label}</span>
          <span className={styles.rowHint}>{item.hint}</span>
        </button>
      ))}
      {items.length === 0 && <div className={styles.empty}>{emptyLabel}</div>}
    </div>
  );
}
