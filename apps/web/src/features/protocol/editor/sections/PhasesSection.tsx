import { cx } from "../../../../components/cx";
import { SectionHeader } from "../EditorLayout";
import {
  GATE_TYPES,
  PHASE_STRATEGIES,
  type GateType,
  type PhaseForm,
  type PhaseStrategy,
  type ProtocolForm,
} from "../protocolDocument";
import { formToYaml } from "../protocolSerialize";
import styles from "./Sections.module.css";
import { CommaList, SelectField, TextField } from "./fieldPrimitives";

const GATE_TONE: Record<GateType, string | undefined> = {
  BUDGET_GATE: styles.toneWarn,
  QUALITY_GATE: styles.toneAccent,
  PUBLISH_GATE: styles.toneUnknown,
  SECURITY_GATE: styles.toneDanger,
  POLICY_GATE: styles.toneDanger,
  HUMAN_GATE: styles.toneSuccess,
};

const GATE_OPTIONS: readonly { value: string; label: string }[] = [
  { value: "", label: "— none —" },
  ...GATE_TYPES.map((gate) => ({ value: gate, label: gate })),
];

const STRATEGY_OPTIONS: readonly { value: string; label: string }[] = PHASE_STRATEGIES.map(
  (strategy) => ({ value: strategy, label: strategy }),
);

interface PhaseCardProps {
  phase: PhaseForm;
  index: number;
  onChange: (mutator: (phase: PhaseForm) => PhaseForm) => void;
  onRemove: () => void;
}

function CardHeader(props: { index: number; onRemove: () => void }): React.JSX.Element {
  return (
    <div className={styles.phaseCardHeader}>
      <span className="chip mono">{"PHASE " + String(props.index + 1).padStart(2, "0")}</span>
      <button
        type="button"
        className={cx("btn", "sm", "ghost", styles.removeBtn)}
        onClick={props.onRemove}
      >
        × Remove
      </button>
    </div>
  );
}

interface TimeoutProps {
  index: number;
  timeout: number | null;
  mutate: (m: (p: PhaseForm) => PhaseForm) => void;
}

function TimeoutField(props: TimeoutProps): React.JSX.Element {
  return (
    <TextField
      fieldIndex={props.index}
      name="timeout_seconds"
      label="timeout_seconds"
      value={props.timeout === null ? "" : String(props.timeout)}
      onChange={(value) => {
        props.mutate((p) => ({ ...p, timeoutSeconds: value === "" ? null : Number(value) }));
      }}
    />
  );
}

interface RolesListProps {
  index: number;
  roles: { role: string; minInstances: number; maxInstances: number }[];
  mutate: (mutator: (phase: PhaseForm) => PhaseForm) => void;
}

interface DependentListProps {
  index: number;
  value: string[];
  mutate: (mutator: (phase: PhaseForm) => PhaseForm) => void;
}

function DependsField(props: DependentListProps): React.JSX.Element {
  return (
    <CommaList
      index={props.index}
      label="depends_on"
      value={props.value}
      placeholder="execution"
      tooltip="Comma-separated phase ids; DAG validated by the compiler"
      onChange={(items) => {
        props.mutate((p) => ({ ...p, dependsOn: items }));
      }}
    />
  );
}

function CapsField(props: DependentListProps): React.JSX.Element {
  return (
    <CommaList
      index={props.index}
      label="required_capabilities"
      value={props.value}
      placeholder="workspace.read, artifact.write"
      tooltip="Comma-separated capability refs"
      onChange={(caps) => {
        props.mutate((p) => ({ ...p, requiredCapabilities: caps }));
      }}
    />
  );
}

function ContractsField(props: DependentListProps): React.JSX.Element {
  return (
    <CommaList
      index={props.index}
      label="task_contracts"
      value={props.value}
      placeholder="sort_analysis_execution"
      tooltip="Comma-separated TaskContract refs (must exist in the catalog)"
      onChange={(contracts) => {
        props.mutate((p) => ({ ...p, taskContracts: contracts }));
      }}
    />
  );
}

function RolesList(props: RolesListProps): React.JSX.Element {
  return (
    <CommaList
      index={props.index}
      label="required_roles"
      value={props.roles.map((role) => role.role)}
      placeholder="experiment_engineer"
      tooltip="Role refs resolved against the team catalog (min=max=1 per ref)"
      onChange={(roles) => {
        props.mutate((p) => ({
          ...p,
          requiredRoles: roles.map((role) => ({
            role,
            minInstances: 1,
            maxInstances: 1,
          })),
        }));
      }}
    />
  );
}

function PhaseCard(props: PhaseCardProps): React.JSX.Element {
  const phase = props.phase;
  const index = props.index;
  const mutate = (mutator: (phase: PhaseForm) => PhaseForm): void => {
    props.onChange(mutator);
  };
  return (
    <div className={styles.phaseCard} data-testid={"phase-card-" + String(index)}>
      <CardHeader index={index} onRemove={props.onRemove} />
      <div className={styles.phaseCardBody}>
        <div className={styles.fieldRow}>
          <NameIdFields index={index} phase={phase} mutate={mutate} />
        </div>
        <div className={styles.fieldRow}>
          <StrategyGateFields index={index} phase={phase} mutate={mutate} />
          <TimeoutField index={index} timeout={phase.timeoutSeconds} mutate={mutate} />
        </div>
        <DependsField index={index} value={phase.dependsOn} mutate={mutate} />
        <RolesList index={index} roles={phase.requiredRoles} mutate={mutate} />
        <CapsField index={index} value={phase.requiredCapabilities} mutate={mutate} />
        <ContractsField index={index} value={phase.taskContracts} mutate={mutate} />
      </div>
    </div>
  );
}

function NameIdFields(props: {
  index: number;
  phase: PhaseForm;
  mutate: (mutator: (phase: PhaseForm) => PhaseForm) => void;
}): React.JSX.Element {
  return (
    <>
      <TextField
        fieldIndex={props.index}
        name="id"
        label="id"
        value={props.phase.id}
        onChange={(value) => {
          props.mutate((p) => ({ ...p, id: value }));
        }}
      />
      <TextField
        fieldIndex={props.index}
        name="name"
        label="name"
        value={props.phase.name}
        onChange={(value) => {
          props.mutate((p) => ({ ...p, name: value }));
        }}
      />
    </>
  );
}

function StrategyGateFields(props: {
  index: number;
  phase: PhaseForm;
  mutate: (mutator: (phase: PhaseForm) => PhaseForm) => void;
}): React.JSX.Element {
  return (
    <>
      <SelectField
        fieldIndex={props.index}
        name="strategy"
        label="strategy"
        value={props.phase.strategy}
        options={STRATEGY_OPTIONS}
        onChange={(value) => {
          props.mutate((p) => ({ ...p, strategy: value as PhaseStrategy }));
        }}
      />
      <SelectField
        fieldIndex={props.index}
        name="gate"
        label="gate"
        value={props.phase.gate ?? ""}
        options={GATE_OPTIONS}
        className={props.phase.gate !== null ? GATE_TONE[props.phase.gate] : undefined}
        onChange={(value) => {
          const gate: GateType | null = value === "" ? null : (value as GateType);
          props.mutate((p) => ({ ...p, gate }));
        }}
      />
    </>
  );
}

interface PhasesSectionProps {
  form: ProtocolForm;
  onEditText: (text: string) => void;
}

/** 阶段区块：phases 卡片编辑（结构复用设计稿 Objectives 区） */
export function PhasesSection(props: PhasesSectionProps): React.JSX.Element {
  const form = props.form;
  const applyForm = (next: ProtocolForm): void => {
    props.onEditText(formToYaml(next));
  };
  const removeAt = (index: number): void => {
    applyForm({ ...form, phases: form.phases.filter((_, i) => i !== index) });
  };
  return (
    <div>
      <SectionHeader
        title="Phases"
        subtitle="Phase DAG: strategy, roles, capabilities, contracts, gates, stop conditions"
        extra={<span className="chip">{form.phases.length}</span>}
      />
      {form.phases.map((phase, index) => (
        <PhaseCard
          key={String(index)}
          phase={phase}
          index={index}
          onChange={(mutator) => {
            const nextPhase = mutator(phase);
            applyForm({
              ...form,
              phases: form.phases.map((item, i) => (i === index ? nextPhase : item)),
            });
          }}
          onRemove={() => {
            removeAt(index);
          }}
        />
      ))}
      <AddPhaseButton
        onAdd={() => {
          applyForm({ ...form, phases: [...form.phases, emptyPhase(form.phases.length)] });
        }}
      />
    </div>
  );
}

function AddPhaseButton(props: { onAdd: () => void }): React.JSX.Element {
  return (
    <button type="button" className={cx("btn", styles.addPhaseBtn)} onClick={props.onAdd}>
      + Add phase
    </button>
  );
}

function emptyPhase(count: number): PhaseForm {
  return {
    id: "phase_" + String(count + 1),
    name: "",
    strategy: "single_agent",
    dependsOn: [],
    inputs: [],
    outputs: [],
    requiredRoles: [],
    requiredCapabilities: [],
    taskContracts: [],
    timeoutSeconds: null,
    gate: null,
    stopConditions: null,
  };
}
