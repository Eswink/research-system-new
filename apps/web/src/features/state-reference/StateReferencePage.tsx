import { GapLayout } from "../shared/GapLayout";
import { pageSupport } from "../../navigation/pageSupport";
import { useI18n } from "../../i18n/useI18n";

/** 状态矩阵（T26）：明确标注的"界面状态说明"页；呈现组件状态，不冒充实时运维。 */
export function StateReferencePage() {
  const { t } = useI18n();
  const support = pageSupport({ domain: "ops", page: "matrix" });
  return (
    <div data-testid="gap-page-ops-matrix">
      <GapLayout
        title={t("page.ops.matrix")}
        support={support}
        columns={[t("matrix.state"), t("matrix.appearance")]}
        detailTitle={t("matrix.legend")}
        detailHint={t("matrix.hint")}
      />
    </div>
  );
}
