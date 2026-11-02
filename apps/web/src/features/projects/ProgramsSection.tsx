/**
 * 研究程序的最小读面（GOAL-20261103-104 EC-03）。
 *
 * **射程如实登记**：这里**只是**列表 + 一个「推进一轮」按钮。完整的程序页（建程序表单、
 * 逐轮决定时间线、`cited_facts` 展开）不在本轮 —— 本轮的目标是「四条路由**要么有消费者
 * 要么被登记**」，不是「每条路由都有完整 UI」。
 *
 * **推进不是幂等操作**：它真的会启动一轮 run。按钮因此显示服务端返回的**决定本身**
 * （继续 / 停 + 被引事实），不在前端推断成败。
 */

import { useState } from "react";

import { api } from "../../api/client";
import type { ProgramAdvanceDto, ProgramDetailDto } from "../../api/types";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { PanelSection } from "../../components/PanelSection";
import styles from "../shared/LivePage.module.css";

function AdvanceResult({
  result,
  zh,
}: {
  result: ProgramAdvanceDto;
  zh: boolean;
}) {
  return (
    <p className={styles.notice} data-testid="program-advance-result" role="status">
      {zh ? "本轮决定" : "Decision"}: <strong>{result.decision.kind}</strong>{" "}
      <span className="mono">{result.decision.reason}</span>
      {result.decision.cited_facts.length === 0 ? null : (
        <span className="mono"> — {result.decision.cited_facts.join("; ")}</span>
      )}
    </p>
  );
}

function ProgramRow({ program, zh }: { program: ProgramDetailDto; zh: boolean }) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ProgramAdvanceDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const advance = (): void => {
    if (busy) return;
    setBusy(true);
    setError(null);
    void api
      .advanceProgram(program.id)
      .then((outcome) => {
        setResult(outcome);
      })
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : String(cause));
      })
      .finally(() => {
        setBusy(false);
      });
  };
  return (
    <li className={styles.listButton} data-testid={`program-row-${program.id}`}>
      <div>
        <strong className="mono">{program.id}</strong>{" "}
        <span className={styles.notice}>
          {zh ? "协议" : "Protocol"}: {program.protocol_id}{" "}
          {zh ? "轮次" : "Runs"}: {program.run_count}/{program.max_runs}
        </span>
      </div>
      <button
        type="button"
        className="btn sm"
        disabled={busy}
        data-testid={`program-advance-${program.id}`}
        onClick={advance}
      >
        {busy ? (zh ? "推进中…" : "Advancing…") : zh ? "推进一轮" : "Advance one run"}
      </button>
      {result === null ? null : <AdvanceResult result={result} zh={zh} />}
      {error === null ? null : (
        <span className={styles.notice} role="alert">
          {error}
        </span>
      )}
    </li>
  );
}

export function ProgramsSection({ projectId }: { projectId: string }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const programs = useResource(`programs:${projectId}`, () => api.listPrograms(projectId));
  if (programs.phase === "loading" || programs.data === null) {
    return null;
  }
  return (
    <PanelSection
      title={zh ? "研究程序" : "Research programs"}
      count={programs.data.length}
    >
      {programs.data.length === 0 ? (
        <p className={styles.notice} data-testid="programs-empty">
          {zh
            ? "本项目还没有研究程序（多轮迭代的研究线）。"
            : "This project has no research program (a multi-run research line) yet."}
        </p>
      ) : (
        <ul className={styles.list} data-testid="programs-list">
          {programs.data.map((program) => (
            <ProgramRow key={program.id} program={program} zh={zh} />
          ))}
        </ul>
      )}
    </PanelSection>
  );
}
