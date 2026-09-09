import { useEffect, useState } from "react";
import { commitNavigation, requestNavigation } from "./navigationGuard";
import { parseSourceSelection, type SourceSelection } from "./presentationPolicy";

/** URL-only display preference; never stores examples, tokens, or Domain state. */
export function useSourceSelection(): [SourceSelection, (source: SourceSelection) => void] {
  const [source, setSource] = useState(() => parseSourceSelection(window.location.search));
  useEffect(() => {
    const read = () => {
      setSource(parseSourceSelection(window.location.search));
    };
    window.addEventListener("popstate", read);
    return () => {
      window.removeEventListener("popstate", read);
    };
  }, []);
  const change = (next: SourceSelection) => {
    if (next === source) return;
    const url = new URL(window.location.href);
    if (next === "auto") url.searchParams.delete("source");
    else url.searchParams.set("source", next);
    if (!requestNavigation(url.href)) return;
    window.history.pushState(null, "", url);
    commitNavigation();
    setSource(next);
  };
  return [source, change];
}
