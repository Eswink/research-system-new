/**
 * 研究程序读面 + 写面（GOAL-20261103-104 EC-03 起；GOAL-20261107-107 EC-02 补全）。
 *
 * **它补哪三格**（本轮）：① **建程序表单**（`POST /projects/{id}/programs` —— 这条路由
 * 此前只有客户端字面量、零调用点）；② **逐轮决定时间线**（`GET /programs/{id}` 的
 * `decisions[]` 早就带着 `after_index` / `kind` / `reason` / `cited_facts` / `decided_at`，
 * 页面上一个字都没显示）；③ **`cited_facts` 逐条可展开**（决定「为何继续 / 为何停」的
 * 原文依据）。
 *
 * **三条口径**：
 *
 * 1. **推进不是幂等操作**：它真的会启动一轮 run。按钮显示服务端返回的**决定本身**
 *    （继续 / 停 + 被引事实），不在前端推断成败。
 * 2. **没有决定就是没有决定**：`decisions` 为空 ⇒ 明确空态，**不**伪造一行「尚未推进」。
 * 3. **建程序失败照实说**：服务端 4xx/5xx 的正文原样呈现，不吞成「创建失败」。
 */

import { useState } from "react";

import { api } from "../../api/client";
import type { ProgramAdvanceDto, ProgramCreateDto, ProgramDetailDto } from "../../api/types";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { PanelSection } from "../../components/PanelSection";
import styles from "../shared/LivePage.module.css";

function AdvanceResult({ result, zh }: { result: ProgramAdvanceDto; zh: boolean }) {
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

/** 一条决定（时间线的一格）：序号 / 种类 / 理由 / 时间，`cited_facts` 可展开。 */
function DecisionRow({
  decision,
  zh,
}: {
  decision: ProgramDetailDto["decisions"][number];
  zh: boolean;
}) {
  const [open, setOpen] = useState(false);
  const rowTestId = `program-decision-${String(decision.after_index)}`;
  return (
    <li className={styles.listButton} data-testid={rowTestId}>
      <div>
        <strong className="mono">{`#${String(decision.after_index)} ${decision.kind}`}</strong>{" "}
        <span className={styles.notice}>{decision.reason}</span>
      </div>
      <span className={styles.notice}>{decision.decided_at}</span>
      <CitedFacts
        decision={decision}
        open={open}
        zh={zh}
        onToggle={() => {
          setOpen(!open);
        }}
      />
    </li>
  );
}

/** `cited_facts` 的展开面（与行渲染分开：两者都受 50 行函数门约束）。 */
function CitedFacts({
  decision,
  open,
  zh,
  onToggle,
}: {
  decision: ProgramDetailDto["decisions"][number];
  open: boolean;
  zh: boolean;
  onToggle: () => void;
}) {
  const facts = decision.cited_facts;
  if (facts.length === 0) return null;
  const suffix = String(decision.after_index);
  return (
    <>
      <button
        type="button"
        className="btn sm ghost"
        data-testid={`program-cited-toggle-${suffix}`}
        onClick={onToggle}
      >
        {open
          ? zh
            ? "收起依据"
            : "Hide cited facts"
          : zh
            ? `依据（${String(facts.length)}）`
            : `Cited facts (${String(facts.length)})`}
      </button>
      {open && (
        <ul className={styles.list} data-testid={`program-cited-${suffix}`}>
          {facts.map((fact) => (
            <li key={fact} className="mono">
              {fact}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

/** 逐轮决定时间线（在场才渲染；没有决定 ⇒ 明确空态）。 */
function DecisionTimeline({ programId, zh }: { programId: string; zh: boolean }) {
  const detail = useResource(`program-detail:${programId}`, () => api.programDetail(programId));
  if (detail.phase === "loading" || detail.data === null) return null;
  const decisions = detail.data.decisions;
  return (
    <div data-testid={`program-timeline-${programId}`}>
      {decisions.length === 0 ? (
        <p className={styles.notice} data-testid={`program-timeline-empty-${programId}`}>
          {zh ? "本程序还没有推进过，因此没有决定。" : "This program has no decisions yet."}
        </p>
      ) : (
        <ul className={styles.list}>
          {decisions.map((decision) => (
            <DecisionRow
              key={`${String(decision.after_index)}:${decision.kind}`}
              decision={decision}
              zh={zh}
            />
          ))}
        </ul>
      )}
    </div>
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
      <DecisionTimeline programId={program.id} zh={zh} />
    </li>
  );
}

/** 建程序表单：协议路径 + 轮数 + 续跑判词（服务端另有五个可选声明，见 `ProgramCreateDto`）。 */
function CreateProgramForm({ projectId, zh }: { projectId: string; zh: boolean }) {
  const form = useCreateProgram(projectId, zh);
  return (
    <form data-testid="program-create-form" onSubmit={form.submit}>
      <div className={styles.toolbar}>
        <input
          className="input"
          aria-label={zh ? "协议路径" : "Protocol path"}
          placeholder="examples/protocols/direction_to_manuscript_v1.yaml"
          value={form.protocol}
          onChange={(event) => {
            form.setProtocol(event.target.value);
          }}
        />
        <input
          className="input"
          aria-label={zh ? "最大轮数" : "Max runs"}
          type="number"
          min={1}
          max={20}
          value={form.maxRuns}
          onChange={(event) => {
            form.setMaxRuns(event.target.value);
          }}
        />
        <button
          type="submit"
          className="btn sm"
          disabled={form.busy}
          data-testid="program-create-submit"
        >
          {form.busy ? (zh ? "创建中…" : "Creating…") : zh ? "新建程序" : "Create program"}
        </button>
      </div>
      {form.created === null ? null : (
        <p className={styles.notice} data-testid="program-create-result" role="status">
          {zh ? "已创建" : "Created"}: <span className="mono">{form.created}</span>
        </p>
      )}
      {form.error === null ? null : (
        <p className={styles.notice} role="alert">
          {form.error}
        </p>
      )}
    </form>
  );
}

/** 建程序表单的**状态与副作用**（与渲染分开：两者都受 50 行函数门约束）。 */
function useCreateProgram(projectId: string, zh: boolean) {
  const [protocol, setProtocol] = useState("");
  const [maxRuns, setMaxRuns] = useState("3");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<string | null>(null);
  const submit = (event: React.FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (busy || protocol.trim() === "") return;
    setBusy(true);
    setError(null);
    setCreated(null);
    const payload: ProgramCreateDto = {
      protocol_path: protocol.trim(),
      max_runs: Number(maxRuns),
      // 续跑判词由**服务端**的 `continue_on_verdicts` 决定语义；这里不写字面量
      // （`tests/architecture/typescript/production-boundaries.test.mjs` 禁止前端
      // 源码出现判词枚举 —— 前端不参与判定，只转发声明）。
      continue_on_verdicts: [],
    };
    void api
      .createProgram(projectId, payload)
      .then((program) => {
        setCreated(program.id);
        setProtocol("");
      })
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : String(cause));
      })
      .finally(() => {
        setBusy(false);
      });
  };
  void zh;
  return { protocol, setProtocol, maxRuns, setMaxRuns, busy, error, created, submit };
}

export function ProgramsSection({ projectId }: { projectId: string }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const programs = useResource(`programs:${projectId}`, () => api.listPrograms(projectId));
  if (programs.phase === "loading" || programs.data === null) {
    return null;
  }
  return (
    <PanelSection title={zh ? "研究程序" : "Research programs"} count={programs.data.length}>
      <CreateProgramForm projectId={projectId} zh={zh} />
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
