import type { ApprovalDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { PanelSection } from "../../components/PanelSection";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

export interface PendingDecision {
  approval: ApprovalDto;
  action: "approve" | "deny";
}

export function ApprovalDetail({
  approval,
  busy,
  onRequest,
}: {
  approval: ApprovalDto;
  busy: boolean;
  onRequest: (target: PendingDecision) => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const disabled = busy || approval.status !== "PENDING";
  return <ApprovalDetailPanelSection {...{ zh, approval, disabled, onRequest }} />;
}

interface ApprovalDetailPanelSectionProps {
  zh: boolean;
  approval: ApprovalDto;
  disabled: boolean;
  onRequest: (target: PendingDecision) => void;
}

function ApprovalDetailPanelSection({
  zh,
  approval,
  disabled,
  onRequest,
}: ApprovalDetailPanelSectionProps) {
  return (
    <PanelSection
      title={zh ? "审批详情与影响" : "Approval details and consequences"}
      extra={<Chip tone="warn">{approval.status}</Chip>}
    >
      <KeyValueList
        fields={[
          { label: "Approval", value: approval.id },
          { label: "Run", value: approval.run_id },
          { label: zh ? "动作" : "Action", value: approval.action },
          { label: zh ? "风险" : "Risk", value: approval.risk },
          { label: zh ? "上下文" : "Context", value: approval.context },
          { label: zh ? "策略来源" : "Policy source", value: approval.policy_source },
          { label: "ETag", value: approval.version },
        ]}
      />
      <p className={styles.notice}>
        {zh
          ? "裁决会提交至后端状态机并生成正式事件。界面不授予权限，不提供全批同意。"
          : [
              "Decisions go through the backend state machine and formal events. UI ",
              "visibility grants no permission; there is no approve-all action.",
            ].join("")}
      </p>
      <ApprovalDetailToolbar {...{ disabled, onRequest, approval, zh }} />
    </PanelSection>
  );
}

interface ApprovalDetailToolbarProps {
  disabled: boolean;
  onRequest: (target: PendingDecision) => void;
  approval: ApprovalDto;
  zh: boolean;
}

function ApprovalDetailToolbar({ disabled, onRequest, approval, zh }: ApprovalDetailToolbarProps) {
  return (
    <div className={styles.toolbar}>
      <button
        className="btn primary"
        type="button"
        disabled={disabled}
        data-testid="approve-button"
        onClick={() => {
          onRequest({ approval, action: "approve" });
        }}
      >
        {zh ? "同意" : "Approve"}
      </button>
      <button
        className="btn"
        type="button"
        disabled={disabled}
        data-testid="deny-button"
        onClick={() => {
          onRequest({ approval, action: "deny" });
        }}
      >
        {zh ? "拒绝" : "Deny"}
      </button>
    </div>
  );
}

export function ApprovalConfirmation({
  target,
  busy,
  onConfirm,
  onCancel,
}: {
  target: PendingDecision | null;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const denying = target?.action === "deny";
  const title = denying
    ? zh
      ? "确认拒绝此审批"
      : "Confirm denial"
    : zh
      ? "确认同意此审批"
      : "Confirm approval";
  return (
    <ApprovalDetailConfirmDialog {...{ target, title, busy, denying, zh, onConfirm, onCancel }} />
  );
}

interface ApprovalDetailConfirmDialogProps {
  target: PendingDecision | null;
  title: string;
  busy: boolean;
  denying: boolean;
  zh: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function ApprovalDetailConfirmDialog({
  target,
  title,
  busy,
  denying,
  zh,
  onConfirm,
  onCancel,
}: ApprovalDetailConfirmDialogProps) {
  return (
    <ConfirmDialog
      open={target !== null}
      title={title}
      busy={busy}
      danger={denying}
      consequence={<ApprovalConsequence {...{ target, denying, zh }} />}
      confirmLabel={title}
      cancelLabel={zh ? "返回检查" : "Back to review"}
      onConfirm={onConfirm}
      onCancel={onCancel}
    />
  );
}

function ApprovalConsequence({
  target,
  denying,
  zh,
}: Pick<ApprovalDetailConfirmDialogProps, "target" | "denying" | "zh">) {
  const decisionText = denying
    ? zh
      ? "拒绝会向后端提交审批拒绝，关联运行可能进入拒绝或终止状态。"
      : "Denial submits an approval rejection; the associated run may be rejected or terminated."
    : zh
      ? "同意后，后端可在策略与当前运行状态允许时继续执行。高风险动作可能不可逆。"
      : [
          "Approval may allow execution to continue when policy and current run state permit. ",
          "High-risk actions may be irreversible.",
        ].join("");
  const conflictText = zh
    ? "仅提交当前审批版本，冲突将重新读取，不自动重放裁决。"
    : "Only the displayed version is submitted. Conflicts trigger a reload, never a replay.";
  return (
    <div className={styles.page}>
      <p className="mono">
        {target?.approval.action} · {target?.approval.run_id}
      </p>
      <p>{decisionText}</p>
      <p>{conflictText}</p>
    </div>
  );
}
