import { useState } from "react";

import type { PhaseProgressDto, PhaseState } from "../../api/types";
import { Chip } from "../../components/Chip";
import { cx } from "../../components/cx";
import { PanelSection } from "../../components/PanelSection";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import phaseStyles from "./PhaseProgress.module.css";

/**
 * 十一相进度条（GOAL-20261101-103 EC-03）。
 *
 * **数据来源**：`RunDetailDto.phases`（EC-01 的读面）。本组件**不**自己推状态：
 * 四态（`PENDING` / `RUNNING` / `SUCCEEDED` / `FAILED`）逐字来自后端，前端只做着色与
 * 展开。这条分工是刻意的 —— 前端自己攒状态机是本仓反复修掉的那类漂移。
 *
 * **点击展开该相制品**：`artifact_ids` 是后端按「产出它的任务」归属好的（EC-01 的
 * `run_phase_view`），所以展开不需要再取一次。
 *
 * **null vs 空数组**：`phases === null` = 这条 run 没有冻结协议正文 ⇒ 相结构**读不到**
 * （旧 run），此时给一句明确的空态，**不**渲染零个节点冒充「没有相」。
 */
export function PhaseProgress({ phases }: { phases: PhaseProgressDto[] | null }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [expanded, setExpanded] = useState<string | null>(null);
  if (phases === null) {
    return (
      <div data-testid="phase-progress">
        <PanelSection title={zh ? "相位进度" : "Phase progress"}>
          <p className={styles.notice} data-testid="phase-progress-unavailable">
            {zh
              ? "这条运行没有冻结协议正文，读不到相结构（不是「零相」）。"
              : "This run has no frozen protocol body, so its phase structure is unreadable."}
          </p>
        </PanelSection>
      </div>
    );
  }
  return (
    <div data-testid="phase-progress">
      <PanelSection title={zh ? "相位进度" : "Phase progress"} count={phases.length}>
        <ol className={phaseStyles.track} data-testid="phase-track">
          {phases.map((phase, index) => (
            <PhaseNode
              key={phase.phase_id}
              phase={phase}
              index={index}
              zh={zh}
              expanded={expanded === phase.phase_id}
              onToggle={() => {
                setExpanded(expanded === phase.phase_id ? null : phase.phase_id);
              }}
            />
          ))}
        </ol>
      </PanelSection>
    </div>
  );
}

function PhaseNode({
  phase,
  index,
  zh,
  expanded,
  onToggle,
}: {
  phase: PhaseProgressDto;
  index: number;
  zh: boolean;
  expanded: boolean;
  onToggle: () => void;
}) {
  const stateClass = stateClassName(phase.state);
  const order = String(index + 1);
  return (
    <li className={phaseStyles.node} data-testid={`phase-node-${phase.phase_id}`}>
      <button
        type="button"
        className={cx(phaseStyles.button, stateClass)}
        data-phase-state={phase.state}
        aria-expanded={expanded}
        aria-label={zh ? `第 ${order} 相 ${phase.phase_id}` : `Phase ${order} ${phase.phase_id}`}
        onClick={onToggle}
      >
        <span className={phaseStyles.index}>{index + 1}</span>
        <span className={phaseStyles.id}>{phase.phase_id}</span>
        <Chip tone={toneOf(phase.state)}>{stateLabel(phase.state, zh)}</Chip>
      </button>
      {expanded && <PhaseDetail phase={phase} zh={zh} />}
    </li>
  );
}

/** 展开后的明细（该相的策略 + **本相自己的**制品列表；无产出给明确空态）。 */
function PhaseDetail({ phase, zh }: { phase: PhaseProgressDto; zh: boolean }) {
  const strategy = phase.strategy === "" ? "—" : phase.strategy;
  return (
    <div className={phaseStyles.detail} data-testid={`phase-detail-${phase.phase_id}`}>
      <div className={styles.muted}>
        {zh ? "策略" : "Strategy"}: {strategy}
      </div>
      {phase.artifact_ids.length === 0 ? (
        <div className={styles.muted} data-testid={`phase-artifacts-empty-${phase.phase_id}`}>
          {zh ? "本相暂无已登记产物" : "No artifacts recorded for this phase yet"}
        </div>
      ) : (
        <ul className={styles.list} data-testid={`phase-artifacts-${phase.phase_id}`}>
          {phase.artifact_ids.map((id) => (
            <li key={id} className="mono">
              {id}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

type LowerState = "pending" | "running" | "succeeded" | "failed";

/**
 * 状态 → CSS module 的着色 class（**显式映射**，不是 `styles[state.toLowerCase()]`）。
 *
 * 显式映射的理由（本轮 lint 实测）：动态下标在类型上返回 `string | undefined`
 * （`restrict-template-expressions` 直接判红），而"某个状态没有对应 class"正是
 * 应当在**编译期**暴露、而不是在页面上静默变成空 class 的事情。
 */
function stateClassName(state: PhaseState): string {
  const map: Record<LowerState, string> = {
    pending: phaseStyles.pending ?? "",
    running: phaseStyles.running ?? "",
    succeeded: phaseStyles.succeeded ?? "",
    failed: phaseStyles.failed ?? "",
  };
  return map[state.toLowerCase() as LowerState];
}

/** 四态着色**必须**互不相同（判据按 class 名核对；这也是「状态色」这条判据的对象）。 */
function toneOf(state: PhaseState): "neutral" | "accent" | "danger" | "success" {
  if (state === "RUNNING") return "accent";
  if (state === "FAILED") return "danger";
  if (state === "SUCCEEDED") return "success";
  return "neutral";
}

export function stateLabel(state: PhaseState, zh: boolean): string {
  if (state === "RUNNING") return zh ? "进行中" : "RUNNING";
  if (state === "FAILED") return zh ? "失败" : "FAILED";
  if (state === "SUCCEEDED") return zh ? "已完成" : "SUCCEEDED";
  return zh ? "未开始" : "PENDING";
}
