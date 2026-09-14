import type { ReactNode } from "react";

import type { LineageDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { EmptyState } from "../../components/States";
import { Table } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import { edgeColumns, nodeColumns } from "./lineageColumns";
import styles from "../shared/LivePage.module.css";

/**
 * Run 级来源血缘投影（nodes/edges 由后端 persisted evidence/claim 构造）。
 * 只 render 后端返回的节点/边；全局跨 run 血缘不可用如实标注（G9）。
 */
export function LineageProjection({ data }: { data: LineageDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <div className={styles.cards}>
      <ProjectionTable
        title={zh ? "节点" : "Nodes"}
        empty={zh ? "本运行无显式来源引用" : "No explicit references for this run"}
        count={data.nodes.length}
      >
        <Table
          columns={nodeColumns(zh)}
          rows={data.nodes}
          rowKey={(row) => row.id}
          ariaLabel={zh ? "血缘节点" : "Lineage nodes"}
        />
      </ProjectionTable>
      <ProjectionTable
        title={zh ? "边" : "Edges"}
        empty={zh ? "无显式关系" : "No explicit relations"}
        count={data.edges.length}
      >
        <Table
          columns={edgeColumns(zh)}
          rows={data.edges}
          rowKey={(row) => `${row.source}->${row.target}:${row.relation}`}
          ariaLabel={zh ? "血缘边" : "Lineage edges"}
        />
      </ProjectionTable>
      {!data.global_lineage_available && data.global_lineage_reason !== null && (
        <div className={styles.card}>
          <p className={styles.metadata}>{data.global_lineage_reason}</p>
        </div>
      )}
    </div>
  );
}

function ProjectionTable({
  title,
  empty,
  count,
  children,
}: {
  title: string;
  empty: string;
  count: number;
  children: ReactNode;
}) {
  return (
    <section className={styles.card}>
      <div className={styles.cardHead}>
        <h3 className={styles.cardTitle}>{title}</h3>
        <Chip tone="accent">{String(count)}</Chip>
      </div>
      {count === 0 ? <EmptyState message={empty} /> : children}
    </section>
  );
}
