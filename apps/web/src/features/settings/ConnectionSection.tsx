/**
 * 控制面连接（GOAL-20260926-020 EC-01）：写面 token 的**输入面**。
 *
 * 只做三件事：把 token 收进**内存**（`api/controlPlaneToken.ts`）、显示「已配置 / 未配置」、
 * 允许清除。**不回显**已保存的 token 明文；**不落盘**（见该模块的决策说明）。
 *
 * 本输入面**不是**访问控制：`docs/security/THREAT_MODEL.md` §6.3 第 3 条明写
 * `apps/web` 的按钮可见性 / 路由可见性**不是**访问控制——唯一控制点是服务端中间件。
 * 这里呈现的是「让开启认证后的写操作可用」所需的凭据面。
 */

import { useState, useSyncExternalStore } from "react";

import {
  clearControlPlaneToken,
  hasControlPlaneToken,
  setControlPlaneToken,
  subscribeControlPlaneToken,
} from "../../api/controlPlaneToken";
import { PanelSection } from "../../components/PanelSection";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

export function ConnectionSection() {
  const { t } = useI18n();
  const configured = useSyncExternalStore(subscribeControlPlaneToken, hasControlPlaneToken);
  const [draft, setDraft] = useState("");
  return (
    <PanelSection
      title={t("connection.title")}
      extra={
        <span className="chip" data-testid="connection-status">
          {configured ? t("connection.statusConfigured") : t("connection.statusMissing")}
        </span>
      }
    >
      <div className={styles.page} data-testid="connection-form">
        <TokenRow draft={draft} onDraftChange={setDraft} />
        <p className={styles.notice}>{t("connection.hint")}</p>
        <p className={styles.notice}>{t("connection.note")}</p>
      </div>
    </PanelSection>
  );
}

function TokenRow({
  draft,
  onDraftChange,
}: {
  draft: string;
  onDraftChange: (next: string) => void;
}) {
  const { t } = useI18n();
  return (
    <div className={styles.stack}>
      <label className={styles.queryLabel}>
        <span>{t("connection.label")}</span>
        <input
          className="input mono"
          type="password"
          autoComplete="off"
          spellCheck={false}
          data-testid="connection-token-input"
          placeholder={t("connection.placeholder")}
          value={draft}
          onChange={(event) => {
            onDraftChange(event.target.value);
          }}
        />
      </label>
      <TokenActions draft={draft} onDraftChange={onDraftChange} />
    </div>
  );
}

function TokenActions({
  draft,
  onDraftChange,
}: {
  draft: string;
  onDraftChange: (next: string) => void;
}) {
  const { t } = useI18n();
  return (
    <div className={styles.toolbar}>
      <button
        className="btn sm primary"
        type="button"
        data-testid="connection-save"
        onClick={() => {
          setControlPlaneToken(draft);
          onDraftChange("");
        }}
      >
        {t("connection.save")}
      </button>
      <button
        className="btn sm"
        type="button"
        data-testid="connection-clear"
        onClick={() => {
          clearControlPlaneToken();
          onDraftChange("");
        }}
      >
        {t("connection.clear")}
      </button>
    </div>
  );
}
