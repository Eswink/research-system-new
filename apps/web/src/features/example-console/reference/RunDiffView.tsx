import FIX_RUN_DIFF from "../data/run-diff.json";
import FIX_RUNS_HISTORY from "../data/runs-history.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { RunDiffViewSection2 } from "./run-diff-view/RunDiffViewSection2";

export const RunDiffView = ({
  aId,
  bId,
}: {
  aId?: string | undefined;
  bId?: string | undefined;
}) => {
  const { t } = useI18n();
  const a = FIX_RUNS_HISTORY.find((r) => r.id === aId);
  const b = FIX_RUNS_HISTORY.find((r) => r.id === bId);
  const diff = FIX_RUN_DIFF;
  if (!a || !b) return <div className="empty-mark">Select two example runs</div>;

  return <RunDiffViewSection2 {...{ a, b, t, diff }} />;
};
