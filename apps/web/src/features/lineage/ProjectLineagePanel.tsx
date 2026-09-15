import type { ProjectLineageDto } from "../../api/types";
import { Table } from "../../components/Table";
import { useI18n } from "../../i18n/useI18n";
import {
  projectEdgeColumns,
  projectNodeColumns,
  projectResourceColumns,
} from "./projectLineageColumns";
import styles from "../shared/LivePage.module.css";

/**
 * 项目级来源血缘（G9）：项目内各 run 的血缘投影合并图。
 *
 * 跨 run 关系由**共享节点**表达（同一来源/制品/模型被多个 run 引用 ⇒ 标"共享"）；
 * 数据集/提示词只有未连边清单 —— 资源与 run 的引用关系没有记录面，后端
 * `reference_recording` 如实返回，这里原样呈现（不画猜测的边）。
 */
export function ProjectLineagePanel({ data }: { data: ProjectLineageDto }) {
  const zh = useI18n().language === "zh";
  return (
    <div className={styles.stack}>
      <NoteCard text={mergeSummary(data, zh)} />
      <PanelTable
        title={zh ? "节点（共享 = 跨运行）" : "Nodes (shared = cross-run)"}
        empty={zh ? "项目内暂无显式来源引用" : "No explicit references in this project"}
        count={data.nodes.length}
      >
        <Table
          columns={projectNodeColumns(zh)}
          rows={data.nodes}
          rowKey={(row) => row.id}
          ariaLabel={zh ? "项目血缘节点" : "Project lineage nodes"}
        />
      </PanelTable>
      <PanelTable
        title={zh ? "边" : "Edges"}
        empty={zh ? "无显式关系" : "No explicit relations"}
        count={data.edges.length}
      >
        <Table
          columns={projectEdgeColumns(zh)}
          rows={data.edges}
          rowKey={(row) => `${row.source}->${row.target}:${row.relation}`}
          ariaLabel={zh ? "项目血缘边" : "Project lineage edges"}
        />
      </PanelTable>
      <PanelTable
        title={zh ? "库资源（未连边清单）" : "Library resources (unlinked)"}
        empty={zh ? "项目内无库资源" : "No library resources in this project"}
        count={data.library_resources.length}
      >
        <Table
          columns={projectResourceColumns(zh)}
          rows={data.library_resources}
          rowKey={(row) => row.id}
          ariaLabel={zh ? "未连边库资源" : "Unlinked library resources"}
        />
      </PanelTable>
      {data.reference_recording_reason !== null && (
        <NoteCard text={data.reference_recording_reason} />
      )}
      {data.degraded && data.degraded_reason !== null && <NoteCard text={data.degraded_reason} />}
    </div>
  );
}

function mergeSummary(data: ProjectLineageDto, zh: boolean): string {
  const counts = [data.run_count, data.nodes.length, data.edges.length].join(" / ");
  if (zh) {
    return `项目级合并图（运行 / 节点 / 边）：${counts}`;
  }
  return `Project merge (runs / nodes / edges): ${counts}`;
}

function NoteCard({ text }: { text: string }) {
  return (
    <div className={styles.card}>
      <p className={styles.metadata}>{text}</p>
    </div>
  );
}

function PanelTable({
  title,
  empty,
  count,
  children,
}: {
  title: string;
  empty: string;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>
        {title} <span className={styles.metadata}>({String(count)})</span>
      </h3>
      {count === 0 ? <p className={styles.metadata}>{empty}</p> : children}
    </div>
  );
}
