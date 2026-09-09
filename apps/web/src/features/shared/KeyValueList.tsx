import type { ReactNode } from "react";
import styles from "./LivePage.module.css";

export interface MetadataField {
  label: string;
  value: ReactNode;
}

export function KeyValueList({ fields }: { fields: readonly MetadataField[] }) {
  return (
    <dl className={styles.metadata}>
      {fields.map((field) => (
        <div key={field.label}>
          <dt>{field.label}</dt>
          <dd>{field.value}</dd>
        </div>
      ))}
    </dl>
  );
}
