import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Field } from "./Field";
import { Icon } from "./Icon";
import visual from "./ManifestSection.module.css";
import { SectionHeader } from "./SectionHeader";
import { findErr } from "./findErr";
import { INPUT_ERR } from "./inputErr";
import { INPUT_MONO } from "./inputMono";

/** Reference: screens/ProtocolEditor.sections.jsx; EXAMPLE ONLY. */
export const ManifestSection = ({ value, setP, errors }: E.ProtocolSectionProps) => {
  const { t } = useI18n();
  const { manifest, protocol_version } = value;
  const eName = findErr(errors, "manifest.name");
  const levels = [
    { value: "MANUAL", label: t("pe.man.manual"), desc: t("pe.man.manualDesc") },
    { value: "GUARDED_AUTONOMOUS", label: t("pe.man.guarded"), desc: t("pe.man.guardedDesc") },
    { value: "AUTONOMOUS", label: t("pe.man.autonomous"), desc: t("pe.man.autonomousDesc") },
  ];
  return <ManifestSectionSecManifest {...{ t, protocol_version, manifest, eName, setP, levels }} />;
};

interface ManifestSectionSecManifestProps {
  t: (key: string, fallback?: string) => string;
  protocol_version: string;
  manifest: { id: string; name: string; autonomy_level: string };
  eName: E.ProtocolIssue | undefined;
  setP: E.UpdateProtocol;
  levels: { value: string; label: string; desc: string }[];
}

function ManifestSectionSecManifest({
  t,
  protocol_version,
  manifest,
  eName,
  setP,
  levels,
}: ManifestSectionSecManifestProps) {
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.manifest")}
        subtitle={t("pe.sec.manifestDesc")}
        extra={<span className={`chip mono ${visual.surface ?? ""}`}>protocol_version 1.4</span>}
      />

      <ManifestSectionSection {...{ t, protocol_version, manifest }} />

      <Field
        label="manifest.name"
        tooltip={t("pe.man.tip.name")}
        error={eName}
        hint={t("pe.man.hint.name")}
      >
        <input
          value={manifest.name}
          onChange={(e) => {
            setP((p) => {
              p.manifest.name = e.target.value;
            });
          }}
          style={eName ? { ...INPUT_ERR, fontFamily: "var(--font-mono)" } : INPUT_MONO}
          placeholder="lowercase-with-hyphens"
        />
      </Field>

      <ManifestSectionField {...{ t, levels, manifest, setP }} />
    </div>
  );
}

interface ManifestSectionFieldProps {
  t: (key: string, fallback?: string) => string;
  levels: { value: string; label: string; desc: string }[];
  manifest: { id: string; name: string; autonomy_level: string };
  setP: E.UpdateProtocol;
}

interface ManifestSectionSectionProps {
  t: (key: string, fallback?: string) => string;
  protocol_version: string;
  manifest: { id: string; name: string; autonomy_level: string };
}

function ManifestSectionSection({ t, protocol_version, manifest }: ManifestSectionSectionProps) {
  return (
    <div className={visual.grid}>
      <Field label="protocol_version" tooltip={t("pe.man.tip.version")} locked>
        <input
          value={protocol_version}
          readOnly
          disabled
          style={{ ...INPUT_MONO, opacity: 0.6, cursor: "not-allowed", textAlign: "center" }}
        />
      </Field>
      <Field label="manifest.id" tooltip={t("pe.man.tip.id")} locked>
        <div className={visual.row}>
          <input
            value={manifest.id}
            readOnly
            disabled
            style={{ ...INPUT_MONO, opacity: 0.6, cursor: "not-allowed", minWidth: 0 }}
          />
          <button className={`btn sm ghost ${visual.action ?? ""}`} title="Copy">
            <Icon name="copy" size={10} />
          </button>
        </div>
      </Field>
    </div>
  );
}

function ManifestSectionField({ t, levels, manifest, setP }: ManifestSectionFieldProps) {
  return (
    <Field label="manifest.autonomy_level" tooltip={t("pe.man.tip.autonomy")}>
      <div className={visual.grid2}>
        {levels.map((l) => {
          const active = manifest.autonomy_level === l.value;
          const tone =
            l.value === "AUTONOMOUS"
              ? "danger"
              : l.value === "GUARDED_AUTONOMOUS"
                ? "warn"
                : "success";
          return (
            <button
              key={l.value}
              onClick={() => {
                setP((p) => {
                  p.manifest.autonomy_level = l.value;
                });
              }}
              className={visual.action2}
              style={{
                background: active ? `var(--${tone}-dim)` : "var(--bg-sunken)",
                border: `1px solid ${active ? `var(--${tone}-line)` : "var(--border)"}`,
              }}
            >
              <div
                className={visual.label}
                style={{ color: active ? `var(--${tone})` : "var(--fg-muted)" }}
              >
                {l.value}
              </div>
              <div className={visual.caption}>{l.desc}</div>
            </button>
          );
        })}
      </div>
    </Field>
  );
}
