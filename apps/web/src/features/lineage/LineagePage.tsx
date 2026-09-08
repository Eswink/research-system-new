import { api } from "../../api/client";
import type { ClaimMapDto, RelationDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  UnavailableState,
} from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { useResource } from "../../hooks/useResource";
import type { PageContext } from "../../navigation/pageContext";
import { GAPS } from "../../navigation/pageSupport";
import styles from "../shared/FeaturePage.module.css";

type FlatRelation = RelationDto & { claim: string };

function flattenRelations(claims: ClaimMapDto | null): FlatRelation[] {
  const list = claims?.claims ?? [];
  return list.flatMap((c) => c.relations.map((rel) => ({ claim: c.id, ...rel })));
}

/**
 * 血缘（T21）：仅用 API 明确返回的 Run/Evidence/Artifact/Model 引用构造当前 Run
 * 的来源关系；不存在的引用显示断开关系，禁止猜测连边。全局血缘不可用。
 */
export function LineagePage({ ctx }: { ctx: PageContext }) {
  const { t } = useI18n();
  const runId = ctx.selectedRunId;
  const claims = useResource(runId === "" ? null : runId, () => api.runClaimMap(runId));
  const evidence = useResource(runId === "" ? null : runId, () => api.runEvidence(runId));

  if (runId === "") {
    return (
      <div className={styles.page}>
        <h2 className={styles.heading}>{t("page.library.lineage")}</h2>
        <EmptyState message={t("overview.noRun")} />
      </div>
    );
  }
  if (claims.phase === "loading" || evidence.phase === "loading") {
    return <LoadingState message={t("state.loading")} />;
  }
  if (claims.phase === "error") {
    return <ErrorState message={claims.error ?? t("state.error")} />;
  }
  return (
    <div className={styles.page}>
      <div className={styles.head}>
        <h2 className={styles.heading}>{t("page.library.lineage")}</h2>
        <Chip tone="accent">{`${t("run.context.label")}: ${runId.slice(0, 12)}`}</Chip>
      </div>
      <div className={styles.body}>
        <RelationsPanel relations={flattenRelations(claims.data)} />
        <EvidencePanel count={evidence.data?.length ?? 0} />
      </div>
    </div>
  );
}

function RelationsPanel({ relations }: { relations: readonly FlatRelation[] }) {
  const { t } = useI18n();
  return (
    <div className={styles.panel}>
      <div className={styles.panelTitle}>{t("lineage.relations")}</div>
      {relations.length === 0 ? (
        <EmptyState message={t("state.empty")} />
      ) : (
        relations.map((rel, i) => (
          <div key={`${rel.claim}-${String(i)}`} className="row">
            <span className="mono">{rel.claim.slice(0, 12)}</span>
            <Chip tone="neutral">{rel.relation}</Chip>
            <span className="mono" style={{ color: "var(--fg-faint)" }}>
              {(rel.evidence_id || "—").slice(0, 12)}
            </span>
          </div>
        ))
      )}
    </div>
  );
}

function EvidencePanel({ count }: { count: number }) {
  const { t } = useI18n();
  return (
    <aside className={styles.panel}>
      <div className={styles.panelTitle}>{t("lineage.evidence")}</div>
      <p style={{ margin: "0 0 8px", fontSize: "var(--fs-caption)", color: "var(--fg-muted)" }}>
        {`${t("lineage.evidenceCount")}: ${String(count)}`}
      </p>
      <UnavailableState title={t("lineage.global")} reason={GAPS.globalLineage} />
    </aside>
  );
}
