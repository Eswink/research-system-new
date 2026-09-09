import { useEffect, useRef, useState } from "react";

export function useDigestCopy(value: string | null | undefined, onCopy?: (value: string) => void) {
  const [copied, setCopied] = useState(false);
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (timeout.current !== null) clearTimeout(timeout.current);
    },
    [],
  );
  const copy = async () => {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      onCopy?.(value);
      setCopied(true);
      if (timeout.current !== null) clearTimeout(timeout.current);
      timeout.current = setTimeout(() => {
        setCopied(false);
      }, 1200);
    } catch {
      setCopied(false);
    }
  };
  return { copied, copy };
}
