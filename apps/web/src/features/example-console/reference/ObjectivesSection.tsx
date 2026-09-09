import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Field } from "./Field";
import { Icon } from "./Icon";
import visual from "./ObjectivesSection.module.css";
import { SectionHeader } from "./SectionHeader";
import { findErr } from "./findErr";
import { INPUT_ERR } from "./inputErr";
import { INPUT_MONO } from "./inputMono";
import { INPUT } from "./protocolInput";

/** Reference: screens/ProtocolEditor.sections.jsx; EXAMPLE ONLY. */
export const ObjectivesSection = ({ value, setP, errors }: E.ProtocolSectionProps) => {
  const { t } = useI18n();
  return (
    <div>
      <SectionHeader
        title={t("pe.sec.objectives")}
        subtitle={t("pe.sec.objectivesDesc")}
        extra={
          <span className="chip">
            {value.objectives.length} · {t("pe.obj.total")}
          </span>
        }
      />

      {value.objectives.map((o, i) => {
        const eId = findErr(errors, `objectives[${String(i)}].id`);
        const eSt = findErr(errors, `objectives[${String(i)}].statement`);
        return (
          <div key={i} className={visual.surface}>
            <ObjectivesSectionSection2 {...{ i, setP, t }} />
            <ObjectivesSectionSection {...{ eId, o, setP, i, eSt, t }} />
          </div>
        );
      })}

      <button
        className={`btn ${visual.action2 ?? ""}`}
        onClick={() => {
          setP((p) => {
            p.objectives.push({
              id: `obj_${Math.random().toString(36).slice(2, 7)}`,
              statement: "",
            });
          });
        }}
      >
        <Icon name="plus" size={11} /> {t("pe.obj.add")}
      </button>
    </div>
  );
};

interface ObjectivesSectionSectionProps {
  eId: E.ProtocolIssue | undefined;
  o: { id: string; statement: string };
  setP: E.UpdateProtocol;
  i: number;
  eSt: E.ProtocolIssue | undefined;
  t: (key: string, fallback?: string) => string;
}

interface ObjectivesSectionSection2Props {
  i: number;
  setP: E.UpdateProtocol;
  t: (key: string, fallback?: string) => string;
}

function ObjectivesSectionSection2({ i, setP, t }: ObjectivesSectionSection2Props) {
  return (
    <div className={visual.row}>
      <Icon name="flask" size={10} className={visual.surface2} />
      <span className={visual.caption}>OBJECTIVE {String(i + 1).padStart(2, "0")}</span>
      <button
        className={`btn sm ghost ${visual.action ?? ""}`}
        onClick={() => {
          setP((p) => {
            p.objectives.splice(i, 1);
          });
        }}
      >
        <Icon name="x" size={9} /> {t("pe.obj.remove")}
      </button>
    </div>
  );
}

function ObjectivesSectionSection({ eId, o, setP, i, eSt, t }: ObjectivesSectionSectionProps) {
  return (
    <div className={visual.surface3}>
      <Field label="id" error={eId}>
        <input
          value={o.id}
          onChange={(e) => {
            setP((p) => {
              const row = p.objectives[i];
              if (row) row.id = e.target.value;
            });
          }}
          style={eId ? { ...INPUT_ERR, fontFamily: "var(--font-mono)" } : INPUT_MONO}
          placeholder="obj_short_snake_case"
        />
      </Field>
      <Field label="statement" error={eSt} tooltip={t("pe.obj.tip.statement")}>
        <textarea
          value={o.statement}
          onChange={(e) => {
            setP((p) => {
              const row = p.objectives[i];
              if (row) row.statement = e.target.value;
            });
          }}
          style={{
            ...INPUT,
            height: "auto",
            minHeight: 60,
            padding: 8,
            resize: "vertical",
            lineHeight: 1.55,
            ...(eSt ? { borderColor: "var(--warn-line)" } : {}),
          }}
          placeholder="Quantify …"
        />
      </Field>
    </div>
  );
}
