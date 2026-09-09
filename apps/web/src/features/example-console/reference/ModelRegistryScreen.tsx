import { useState } from "react";
import FIX_REGISTERED_MODELS from "../data/registered-models.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ModelRegistryTitle } from "./model-registry-screen/ModelRegistryTitle";

export const ModelRegistryScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState("mdl_claude_opus_41");
  const [q, setQ] = useState("");
  const [drawer, setDrawer] = useState<{ mode?: string } | null>(null);
  const filtered = q
    ? FIX_REGISTERED_MODELS.filter(
        (m) =>
          m.family.toLowerCase().includes(q.toLowerCase()) ||
          m.provider.toLowerCase().includes(q.toLowerCase()),
      )
    : FIX_REGISTERED_MODELS;
  const selected = FIX_REGISTERED_MODELS.find((m) => m.id === selectedId);

  // Column tracks — `minmax(140px, …fr)` guarantees the model column keeps
  // enough room for the family label + tag chips even when the panel is
  // narrow, while `min-width: 0` on cells (see tokens.css) stops content
  // from pushing the track wider than allotted and breaking row alignment.
  // Layout: model | provider | released | context | license.
  // The 30d-usage column moved to the DETAIL panel (a full sparkline
  // already lives there) — removing it from the master list keeps the
  // remaining columns readable in a two-pane layout without a horizontal
  // scrollbar. Widened provider (→92) and license (→100) so "Anthropic"
  // / "apache-2.0" fit on one line at any panel width. Model column has
  // a stronger min-width so family + tag chips never wrap.
  const cols = "minmax(160px, 1.6fr) 92px 90px 60px 100px";

  return (
    <ModelRegistryTitle
      {...{ t, q, setQ, setDrawer, cols, filtered, selectedId, setSelectedId, selected, drawer }}
    />
  );
};
