import { useState } from "react";
import FIX_NOTEBOOKS from "../data/notebooks.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { NotebooksTitle } from "./notebooks-screen/NotebooksTitle";

export const NotebooksScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState("nb_01");
  const [q, setQ] = useState("");
  const [drawer, setDrawer] = useState<{ mode?: string } | null>(null);
  const selected = FIX_NOTEBOOKS.find((n) => n.id === selectedId);
  const filtered = q
    ? FIX_NOTEBOOKS.filter(
        (n) =>
          n.title.toLowerCase().includes(q.toLowerCase()) ||
          n.excerpt.toLowerCase().includes(q.toLowerCase()),
      )
    : FIX_NOTEBOOKS;

  return (
    <NotebooksTitle
      {...{ t, q, setQ, setDrawer, filtered, selectedId, setSelectedId, selected, drawer }}
    />
  );
};
