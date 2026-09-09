import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ApprovalCardSection } from "./approval-card/ApprovalCardSection";

export const ApprovalCard = ({
  approval,
  selected,
  onSelect,
}: {
  approval: E.Approval;
  selected: boolean;
  expanded: boolean;
  onSelect: () => void;
  onToggle: () => void;
  onDecide: (decision: string) => void;
}) => {
  const { t } = useI18n();
  const riskTone =
    approval.risk === "high" ? "danger" : approval.risk === "medium" ? "warn" : "neutral";
  return <ApprovalCardSection {...{ onSelect, selected, approval, riskTone, t }} />;
};
