import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import visual from "../BudgetSection.module.css";
import { Icon } from "../Icon";
import { INPUT_MONO } from "../inputMono";

interface BudgetSectionSection3Props {
  capDraft: number;
  setCapDraft: Dispatch<SetStateAction<number>>;
  b: {
    cap_minor: number;
    hard_stop_on_breach: boolean;
    reservations: { resource: string; minor: number }[];
  };
  capConfirm: boolean;
  setCapConfirm: Dispatch<SetStateAction<boolean>>;
  t: (key: string, fallback?: string) => string;
  setP: E.UpdateProtocol;
}

export function BudgetSectionSection3({
  capDraft,
  setCapDraft,
  b,
  capConfirm,
  setCapConfirm,
  t,
  setP,
}: BudgetSectionSection3Props) {
  return (
    <div className={visual.row}>
      <input
        type="number"
        value={capDraft}
        onChange={(e) => {
          setCapDraft(Number(e.target.value));
        }}
        style={{ ...INPUT_MONO, flex: 1, minWidth: 0 }}
      />
      <span className={visual.label}>= ${(capDraft / 100000).toFixed(2)}</span>
      <BudgetCapAction {...{ capDraft, b, capConfirm, setCapConfirm, t, setP }} />
    </div>
  );
}

function BudgetCapAction(props: Omit<BudgetSectionSection3Props, "setCapDraft">) {
  const { capDraft, b, capConfirm, setCapConfirm, t, setP } = props;
  const apply = () => {
    setP((protocol) => {
      protocol.budget.cap_minor = capDraft;
    });
  };
  if (capDraft > b.cap_minor && !capConfirm) {
    return (
      <button
        className={`btn sm ${visual.action ?? ""}`}
        onClick={() => {
          setCapConfirm(true);
        }}
      >
        <Icon name="warn-tri" size={9} /> {t("pe.bd.capConfirm")}
      </button>
    );
  }
  if (capConfirm && capDraft > b.cap_minor) {
    return (
      <button
        className="btn sm primary"
        onClick={() => {
          apply();
          setCapConfirm(false);
        }}
      >
        <Icon name="check" size={9} /> {t("pe.bd.capApply")}
      </button>
    );
  }
  if (capDraft !== b.cap_minor) {
    return (
      <button className="btn sm primary" onClick={apply}>
        <Icon name="check" size={9} /> apply
      </button>
    );
  }
  return (
    <span className={`chip ${visual.surface ?? ""}`}>
      <Icon name="check" size={9} /> saved
    </span>
  );
}
