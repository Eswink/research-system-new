import type * as FixtureTypes from "../../fixtureTypes";
import { StatusBadge } from "../StatusBadge";

interface DatasetsLabelProps {
  d: FixtureTypes.Dataset;
  t: (key: string, fallback?: string) => string;
}

export function DatasetsLabel({ d, t }: DatasetsLabelProps) {
  return (
    <span>
      {d.schema_valid === true && <StatusBadge tone="success" icon="check" label="OK" size="sm" />}
      {d.schema_valid === false && (
        <StatusBadge
          tone="danger"
          icon="x"
          label={`${String(d.schema_errors?.length ?? 0)} ${t("ds.err")}`}
          size="sm"
          filled
        />
      )}
      {d.schema_valid == null && <span className="empty-mark">{t("ds.unvalidated")}</span>}
    </span>
  );
}
