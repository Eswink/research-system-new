import type { DeliverableDto } from "../../api/types";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

/** 渲染 persisted deliverable（read-only；未知块以扁平键值表兜底）。 */
export function ReportBody({ data, zh }: { data: DeliverableDto; zh: boolean }) {
  if (!data.available) {
    return (
      <EmptyState
        message={
          data.reason ?? (zh ? "该运行尚无持久化交付物" : "This run has no persisted deliverable")
        }
      />
    );
  }
  const report = data.deliverable;
  const objective = typeof report.objective === "string" ? report.objective : "";
  const blocks = Object.entries(report).filter(([key]) => key !== "objective");
  return (
    <div className={styles.cards}>
      <PanelSection title={zh ? "研究目标" : "Objective"}>
        <p className={styles.metadata}>{objective === "" ? "—" : objective}</p>
      </PanelSection>
      {blocks.map(([key, value]) => (
        <PanelSection key={key} title={key}>
          <KeyValueList fields={flatten(value)} />
        </PanelSection>
      ))}
      <PanelSection title={zh ? "来源" : "Provenance"}>
        <KeyValueList
          fields={[
            { label: "run_id", value: data.run_id },
            { label: "artifact_id", value: data.artifact_id ?? "—" },
            { label: "artifact_digest", value: data.artifact_digest ?? "—" },
          ]}
        />
      </PanelSection>
    </div>
  );
}

/** 只读取标量叶子的扁平键值表；数组与对象递归展开，空值显示 —。 */
function flatten(value: unknown): { label: string; value: string }[] {
  const rows: { label: string; value: string }[] = [];
  const walk = (node: unknown, path: string): void => {
    if (node === null || node === undefined) {
      rows.push({ label: path, value: "—" });
      return;
    }
    if (Array.isArray(node)) {
      rows.push({ label: path, value: node.map((item) => scalarText(item)).join(", ") });
      return;
    }
    if (typeof node === "object") {
      for (const [key, child] of Object.entries(node as Record<string, unknown>)) {
        walk(child, path === "" ? key : `${path}.${key}`);
      }
      return;
    }
    rows.push({ label: path, value: scalarText(node) });
  };
  walk(value, "");
  return rows;
}

/** 标量转文本；对象/数组等非标量不会走到这里（结构已在 walk 中展开）。 */
function scalarText(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}
