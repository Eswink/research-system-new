import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Field } from "./Field";
import { Icon } from "./Icon";
import visual from "./PolicySection.module.css";
import { SectionHeader } from "./SectionHeader";
import { SegmentedField } from "./SegmentedField";

/** Reference: screens/ProtocolEditor.sections.jsx; EXAMPLE ONLY. */
export const PolicySection = ({
  value,
  setP,
  adminMode,
}: Pick<E.ProtocolSectionProps, "value" | "setP" | "adminMode">) => {
  const { t } = useI18n();
  const p = value.policy;
  const disabled = !adminMode;
  return <PolicySectionSecPolicy {...{ t, adminMode, disabled, p, setP }} />;
};

interface PolicySectionSecPolicyProps {
  t: (key: string, fallback?: string) => string;
  adminMode: boolean | undefined;
  disabled: boolean;
  p: { heterogeneous_review: string; memory_write: string; redact_prompts: boolean };
  setP: E.UpdateProtocol;
}

function PolicySectionSecPolicy({ t, adminMode, disabled, p, setP }: PolicySectionSecPolicyProps) {
  return (
    <div>
      <PolicySectionSecPolicy2 {...{ t, adminMode }} />

      {!adminMode && (
        <div className={visual.row}>
          <Icon name="lock" size={11} className={visual.surface} />
          <span>
            <strong className={visual.surface2}>{t("pe.pol.adminReq")}</strong>{" "}
            {t("pe.pol.adminMsg")}
          </span>
        </div>
      )}

      <PolicySectionField2 {...{ t, disabled, p, setP }} />

      <Field label="policy.memory_write" tooltip={t("pe.pol.tip.mem")} locked={disabled}>
        <SegmentedField
          value={p.memory_write}
          onChange={(v) => {
            setP((pp) => {
              pp.policy.memory_write = v;
            });
          }}
          options={[
            { value: "open", label: "open" },
            { value: "gated_by_provenance", label: "gated_by_provenance" },
            { value: "disabled", label: "disabled" },
          ]}
          disabled={disabled}
        />
      </Field>

      <PolicySectionField {...{ t, disabled, setP, p }} />
    </div>
  );
}

interface PolicySectionFieldProps {
  t: (key: string, fallback?: string) => string;
  disabled: boolean;
  setP: E.UpdateProtocol;
  p: { heterogeneous_review: string; memory_write: string; redact_prompts: boolean };
}

interface PolicySectionSecPolicy2Props {
  t: (key: string, fallback?: string) => string;
  adminMode: boolean | undefined;
}

interface PolicySectionField2Props {
  t: (key: string, fallback?: string) => string;
  disabled: boolean;
  p: { heterogeneous_review: string; memory_write: string; redact_prompts: boolean };
  setP: E.UpdateProtocol;
}

function PolicySectionField2({ t, disabled, p, setP }: PolicySectionField2Props) {
  return (
    <Field label="policy.heterogeneous_review" tooltip={t("pe.pol.tip.het")} locked={disabled}>
      <SegmentedField
        value={p.heterogeneous_review}
        onChange={(v) => {
          setP((pp) => {
            pp.policy.heterogeneous_review = v;
          });
        }}
        options={[
          { value: "relaxed", label: "relaxed" },
          { value: "standard", label: "standard" },
          { value: "strict", label: "strict" },
        ]}
        disabled={disabled}
      />
    </Field>
  );
}

function PolicySectionSecPolicy2({ t, adminMode }: PolicySectionSecPolicy2Props) {
  return (
    <SectionHeader
      title={t("pe.sec.policy")}
      subtitle={t("pe.sec.policyDesc")}
      extra={
        <span
          className="chip mono"
          style={{
            color: adminMode ? "var(--success)" : "var(--warn)",
            borderColor: adminMode ? "var(--success-line)" : "var(--warn-line)",
            background: adminMode ? "var(--success-dim)" : "var(--warn-dim)",
          }}
        >
          <Icon name="shield" size={9} /> {adminMode ? "ADMIN" : "READ-ONLY"}
        </span>
      }
    />
  );
}

function PolicySectionField({ t, disabled, setP, p }: PolicySectionFieldProps) {
  return (
    <Field label="policy.redact_prompts" tooltip={t("pe.pol.tip.redact")} locked={disabled}>
      <div className={visual.row2}>
        {[true, false].map((v) => (
          <button
            key={String(v)}
            disabled={disabled}
            onClick={() => {
              setP((pp) => {
                pp.policy.redact_prompts = v;
              });
            }}
            className={visual.action}
            style={{
              background: p.redact_prompts === v ? "var(--accent-dim)" : "var(--bg-sunken)",
              border: `1px solid ${
                p.redact_prompts === v ? "var(--accent-line)" : "var(--border)"
              }`,
              cursor: disabled ? "not-allowed" : "pointer",
              opacity: disabled ? 0.55 : 1,
              color: p.redact_prompts === v ? "var(--accent)" : "var(--fg-muted)",
            }}
          >
            <Icon name={v ? "check" : "ban"} size={10} /> {v ? "true" : "false"}
          </button>
        ))}
      </div>
    </Field>
  );
}
