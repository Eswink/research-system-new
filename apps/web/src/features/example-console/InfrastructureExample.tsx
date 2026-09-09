import styles from "./InfrastructureExample.module.css";
import { MetricCard } from "./reference/MetricCard";
import { PageToolbar } from "./reference/PageToolbar";
import { StatusBadge } from "./reference/StatusBadge";
import { useExampleI18n } from "./useExampleI18n";

/** Compatibility pages have no original handoff; they use its panel/row vocabulary. */
export function InfrastructureExample({ kind }: { kind: "compute" | "observability" }) {
  const { lang } = useExampleI18n();
  const chinese = lang === "zh-CN";
  const title =
    kind === "compute"
      ? chinese
        ? "计算节点"
        : "Compute workers"
      : chinese
        ? "运维观测"
        : "Observability";
  return <InfrastructureExamplePage {...{ title, chinese }} />;
}

interface InfrastructureExamplePageProps {
  title: string;
  chinese: boolean;
}

function InfrastructureExamplePage({ title, chinese }: InfrastructureExamplePageProps) {
  return (
    <div className={styles.page}>
      <PageToolbar
        title={title}
        subtitle={
          chinese
            ? "兼容扩展页 · 固定示例，并非真实集群 / 遥测"
            : "Compatibility extension · EXAMPLE, not live telemetry"
        }
      />
      <div className={styles.metrics}>
        <MetricCard label="Workers · example" value="3" sub="2 ready · 1 draining" />
        <MetricCard
          label="GPU · example"
          value="1"
          sub="Synthetic capability, not device detection"
        />
        <MetricCard
          label="Queue lag · example"
          value="2.4 s"
          sub="Not an SLO or scheduler signal"
        />
        <MetricCard label="Usage / cost" value="UNKNOWN" sub="No UsageLedger is consulted" />
      </div>
      <div className="panel">
        <div className={`row head ${String(styles.row)}`}>
          <span>Worker</span>
          <span>State</span>
          <span>Capability</span>
          <span>Last signal · example</span>
        </div>
        {["sample-cpu-a", "sample-gpu-a", "sample-cpu-b"].map((id, index) => (
          <div className={`row ${String(styles.row)}`} key={id}>
            <span className="mono">{id}</span>
            <StatusBadge
              label={index === 2 ? "DRAINING" : "READY"}
              tone={index === 2 ? "warn" : "success"}
            />
            <span>{index === 1 ? "GPU" : "CPU"}</span>
            <span>2026-08-27T14:42:11Z</span>
          </div>
        ))}
      </div>
    </div>
  );
}
