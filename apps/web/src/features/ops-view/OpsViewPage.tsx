import type { ReactNode } from "react";

import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, UnavailableState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/**
 * 只读运维投影页骨架（PLAN-045）：拉取单一视图端点，渲染表格或空态，
 * 并在管理/处置能力不可用时诚实展示 UnavailableState（不伪装可操作）。
 *
 * `children` 可选的第二参数是 `reload`：带写面的页面（EC-03 调度）在写操作成功后
 * 重新加载读面，让"写面被读面消费"这件事在 UI 上也成立。
 */
export function OpsViewPage<T>({
  testid,
  title,
  kicker,
  description,
  fetch,
  isEmpty,
  unavailable,
  children,
}: {
  testid: string;
  title: string;
  kicker: string;
  description: string;
  fetch: () => Promise<T>;
  isEmpty: (data: T) => boolean;
  unavailable?: { title: string; reason: string } | null;
  children: (data: T, reload: () => void) => ReactNode;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const resource = useResource(testid, fetch);
  return (
    <section className={styles.page} data-testid={testid}>
      <PageHeader title={title} kicker={kicker} description={description} />
      {unavailable != null && (
        <UnavailableState title={unavailable.title} reason={unavailable.reason} />
      )}
      <ResourceBoundary state={resource}>
        {resource.data !== null &&
          (isEmpty(resource.data) ? (
            <EmptyState message={zh ? "无记录" : "No records"} />
          ) : (
            children(resource.data, resource.reload)
          ))}
      </ResourceBoundary>
    </section>
  );
}
