import { useState, type Dispatch, type SetStateAction } from "react";
import { api } from "../../api/client";
import type { RunDetailDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import visual from "./ComparePage.module.css";
import { RunComparisonColumn } from "./RunComparisonColumn";

export function ComparePage() {
  const { language, t } = useI18n();
  const runs = useResource("compare-runs", () => api.listRuns());
  return (
    <section className={styles.page} data-testid="compare-page">
      <PageHeader
        title={t("page.portfolio.compare")}
        kicker="PORTFOLIO / RUN COMPARISON"
        description={
          language === "zh"
            ? "并列检查两次真实运行的冻结身份、账本与实验指标。可比性未被后端确认时，不计算提升率或排名。"
            : [
                "Inspect two actual runs' frozen identity, ledger and experiment metrics. ",
                "Without backend-confirmed comparability, no improvement percentages or ",
                "rankings are calculated.",
              ].join("")
        }
        actions={
          <button
            type="button"
            className="btn"
            disabled={runs.phase === "loading"}
            onClick={runs.reload}
          >
            {language === "zh" ? "刷新运行" : "Refresh runs"}
          </button>
        }
      />
      <ResourceBoundary state={runs}>
        {runs.data !== null && <ComparisonSelection runs={runs.data} />}
      </ResourceBoundary>
    </section>
  );
}

function ComparisonSelection({ runs }: { runs: RunDetailDto[] }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set());
  const [limitReached, setLimitReached] = useState(false);
  const chosen = runs.filter((run) => selected.has(run.id));
  const toggle = (id: string) => {
    const run = runs.find((item) => item.id === id);
    if (run === undefined) return;
    if (chosen.length >= 2 && !selected.has(run.id)) {
      setLimitReached(true);
      return;
    }
    const next = new Set(chosen.map((item) => item.id));
    if (next.has(run.id)) next.delete(run.id);
    else next.add(run.id);
    setSelected(next);
    setLimitReached(false);
  };
  return (
    <ComparePagePage
      {...{ chosen, setSelected, setLimitReached, zh, limitReached, runs, selected, toggle }}
    />
  );
}

interface ComparePagePageProps {
  chosen: RunDetailDto[];
  setSelected: Dispatch<SetStateAction<ReadonlySet<string>>>;
  setLimitReached: Dispatch<SetStateAction<boolean>>;
  zh: boolean;
  limitReached: boolean;
  runs: RunDetailDto[];
  selected: ReadonlySet<string>;
  toggle: (id: string) => void;
}

function ComparePagePage({
  chosen,
  setSelected,
  setLimitReached,
  zh,
  limitReached,
  runs,
  selected,
  toggle,
}: ComparePagePageProps) {
  return (
    <div className={styles.page}>
      <ComparePageToolbar {...{ chosen, setSelected, setLimitReached, zh }} />
      {limitReached && (
        <p role="status" className={styles.notice}>
          {zh
            ? "最多选择两个运行，请先取消一个选择。"
            : "Choose at most two runs; deselect one first."}
        </p>
      )}
      <Table
        columns={comparisonColumns(zh)}
        rows={runs}
        rowKey={(run) => run.id}
        ariaLabel={zh ? "选择待对比运行" : "Select runs for inspection"}
        selectedKeys={selected}
        multiSelect
        onToggleRow={(run) => {
          toggle(run.id);
        }}
        empty={<EmptyState message={zh ? "没有可选择的真实运行" : "No actual runs available"} />}
      />
      <p className={styles.notice}>
        {zh
          ? "相同指标名称不代表相同单位、数据集或测量方法。下方只呈现各运行原始投影，不推断优劣。"
          : [
              "Matching metric names do not establish equal units, datasets or ",
              "measurement methods. Original projections are shown without inferring ",
              "superiority.",
            ].join("")}
      </p>
      <div className={visual.columns}>
        {chosen.map((run) => (
          <RunComparisonColumn key={run.id} run={run} />
        ))}
      </div>
    </div>
  );
}

interface ComparePageToolbarProps {
  chosen: RunDetailDto[];
  setSelected: Dispatch<SetStateAction<ReadonlySet<string>>>;
  setLimitReached: Dispatch<SetStateAction<boolean>>;
  zh: boolean;
}

function ComparePageToolbar({ chosen, setSelected, setLimitReached, zh }: ComparePageToolbarProps) {
  return (
    <div className={styles.toolbar}>
      <Chip>{chosen.length} / 2</Chip>
      <button
        className="btn sm"
        type="button"
        onClick={() => {
          setSelected(new Set());
          setLimitReached(false);
        }}
      >
        {zh ? "清空选择" : "Clear selection"}
      </button>
      <span className="muted">{zh ? "可比性：尚未确认" : "Comparability: not established"}</span>
    </div>
  );
}

function comparisonColumns(zh: boolean): Column<RunDetailDto>[] {
  return [
    { key: "id", header: "Run", render: (run) => <span className="mono">{run.id}</span> },
    { key: "state", header: zh ? "状态" : "State", render: (run) => <Chip>{run.state}</Chip> },
    { key: "protocol", header: zh ? "协议" : "Protocol", render: (run) => run.protocol_id },
    { key: "created", header: zh ? "创建时间" : "Created", render: (run) => run.created_at },
  ];
}
