import { useState } from "react";

import { api } from "../../api/client";
import type { ResourceType } from "../../api/types";
import { ErrorState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { ADJUSTABLE_RESOURCES } from "./forecastPresentation";

/** 预算调整条（PLAN-046）：走 BudgetLedger（release 既有预留 + reserve 新额度）。
 *  语义变更（换 Agent/协议）不在此处——那需要 Manifest Revision，后端诚实 501。 */
export function BudgetAdjustBar({ runId, onAdjusted }: { runId: string; onAdjusted: () => void }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const state = useAdjustState(runId, onAdjusted);
  if (runId === "") return null;
  return (
    <form
      className={styles.toolbar}
      onSubmit={(event) => {
        event.preventDefault();
        state.submit();
      }}
    >
      <AdjustFields state={state} zh={zh} />
      <button className="btn primary" type="submit" disabled={state.busy || !state.valid}>
        {zh ? "提交调整" : "Apply adjustment"}
      </button>
      {state.error !== null && <ErrorState message={state.error} />}
      {state.done !== null && <span className="muted">{state.done}</span>}
    </form>
  );
}

type AdjustState = ReturnType<typeof useAdjustState>;

function AdjustFields({ state, zh }: { state: AdjustState; zh: boolean }) {
  return (
    <>
      <select
        className="input"
        value={state.resource}
        aria-label={zh ? "资源类型" : "Resource type"}
        onChange={(event) => {
          state.setResource(event.target.value as ResourceType);
        }}
      >
        {ADJUSTABLE_RESOURCES.map((resource) => (
          <option key={resource} value={resource}>
            {resource}
          </option>
        ))}
      </select>
      <input
        className="input"
        type="number"
        min={0}
        value={state.quantity}
        aria-label={zh ? "新额度" : "New quota"}
        placeholder={zh ? "新额度" : "New quota"}
        onChange={(event) => {
          state.setQuantity(event.target.value);
        }}
      />
      <input
        className="input"
        value={state.unit}
        aria-label={zh ? "单位" : "Unit"}
        placeholder={zh ? "单位" : "Unit"}
        onChange={(event) => {
          state.setUnit(event.target.value);
        }}
      />
    </>
  );
}

function useAdjustState(runId: string, onAdjusted: () => void) {
  const [resource, setResource] = useState<ResourceType>(
    ADJUSTABLE_RESOURCES[0] ?? "MODEL_TOKENS",
  );
  const [quantity, setQuantity] = useState("1000");
  const [unit, setUnit] = useState("tokens");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const parsed = Number.parseInt(quantity, 10);
  const valid = runId !== "" && Number.isFinite(parsed) && parsed >= 0 && unit.trim() !== "";
  const submit = (): void => {
    if (!valid || busy) return;
    setBusy(true);
    setError(null);
    setDone(null);
    void api
      .adjustRunBudget(runId, [{ resource_type: resource, quantity: parsed, unit: unit.trim() }])
      .then((outcome) => {
        setDone(`reservation_ref=${outcome.reservation_ref.slice(0, 16)}`);
        setBusy(false);
        onAdjusted();
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : String(reason));
        setBusy(false);
      });
  };
  return {
    resource,
    setResource,
    quantity,
    setQuantity,
    unit,
    setUnit,
    busy,
    error,
    done,
    valid,
    submit,
  };
}
