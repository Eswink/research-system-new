import { useState } from "react";

import { api } from "../../api/client";
import type { LibraryResourceDto, ResourceKind } from "../../api/types";
import { Chip } from "../../components/Chip";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState } from "../../components/States";
import { Table } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { libraryColumns } from "./libraryColumns";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";
import { ResourceCreateBar } from "./ResourceCreateBar";

/**
 * 库目录 live 页（EC-03 第一批）：prompts / datasets / notebooks 三页共享，
 * 按 kind 实例化。承载用户标注的目录事实（名称/描述/标签/内容引用），
 * 不伪造内容存储、版本树或 A-B。
 */
export function LibraryPage({
  kind,
  title,
  kicker,
  description,
}: {
  kind: ResourceKind;
  title: string;
  kicker: string;
  description: string;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const [nonce, setNonce] = useState(0);
  const resources = useResource(`${kind}-${String(nonce)}`, () => api.listLibrary(kind));
  const refresh = (): void => {
    setNonce((n) => n + 1);
  };
  return (
    <section className={styles.page} data-testid={`library-${kind}-page`}>
      <PageHeader
        title={title}
        kicker={kicker}
        description={description}
        actions={
          resources.data !== null && (
            <Chip tone="accent">{String(resources.data.length)}</Chip>
          )
        }
      />
      <ResourceCreateBar kind={kind} zh={zh} onCreated={refresh} />
      <ResourceBoundary state={resources}>
        {resources.data !== null &&
          (resources.data.length === 0 ? (
            <EmptyState message={zh ? "尚无条目" : "No entries yet"} />
          ) : (
            <Table
              columns={libraryColumns(kind, zh)}
              rows={resources.data}
              rowKey={(row: LibraryResourceDto) => row.id}
              ariaLabel={zh ? "库条目" : "Library entries"}
            />
          ))}
      </ResourceBoundary>
    </section>
  );
}
