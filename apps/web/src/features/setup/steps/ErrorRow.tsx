import { Icon } from "../../../components/Icon";
import styles from "./steps.module.css";

/** 错误行：role=alert，技术细节（分类 / 诊断）以 mono 呈现，不伪装成功外观。 */
export function ErrorRow({
  message,
  detail,
  testid,
}: {
  message: string;
  detail?: string;
  testid?: string;
}) {
  return (
    <div className={styles.errorRow} role="alert" data-testid={testid}>
      <Icon name="warn-tri" size={12} className={styles.errorIcon} />
      <span>
        {message}
        {detail !== undefined && (
          <>
            {" · "}
            <span className="mono">{detail}</span>
          </>
        )}
      </span>
    </div>
  );
}
