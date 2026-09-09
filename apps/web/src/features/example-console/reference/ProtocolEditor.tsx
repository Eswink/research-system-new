import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react";
import type * as E from "../exampleTypes";
import { DEFAULT_PROTOCOL } from "./defaultProtocol";
import { DigestBanner } from "./DigestBanner";
import { EditorChrome } from "./EditorChrome";
import { ErrorBanner } from "./ErrorBanner";
import { ProtocolEditorActionBar } from "./protocol-editor/ProtocolEditorActionBar";
import { ProtocolEditorSection } from "./protocol-editor/ProtocolEditorSection";
import visual from "./ProtocolEditor.module.css";
import { SectionNav } from "./SectionNav";
import { serialize } from "./serializeProtocol";
import { TemplatePicker } from "./TemplatePicker";
import { validate } from "./validateProtocol";
import { YamlView } from "./YamlView";

function createProtocol(languagesCount: number, temperatureCount: number): E.Protocol {
  const protocol = structuredClone(DEFAULT_PROTOCOL);
  protocol.evaluation.languages = protocol.evaluation.languages.slice(0, languagesCount);
  protocol.evaluation.temperature_grid = protocol.evaluation.temperature_grid.slice(
    0,
    temperatureCount,
  );
  return protocol;
}

function resizeEvaluation(
  protocol: E.Protocol,
  languagesCount: number,
  temperatureCount: number,
): E.Protocol {
  const next = structuredClone(protocol);
  next.evaluation.languages = DEFAULT_PROTOCOL.evaluation.languages.slice(0, languagesCount);
  next.evaluation.temperature_grid = DEFAULT_PROTOCOL.evaluation.temperature_grid.slice(
    0,
    temperatureCount,
  );
  return next;
}

function groupIssues(
  errors: ReturnType<typeof validate>["errors"],
  warnings: ReturnType<typeof validate>["warnings"],
) {
  const grouped: Record<string, { errors: number; warnings: number }> = {};
  [...errors, ...warnings].forEach((issue) => {
    const counts = grouped[issue.section] ?? { errors: 0, warnings: 0 };
    if (issue.severity === "error") counts.errors++;
    else counts.warnings++;
    grouped[issue.section] = counts;
  });
  return grouped;
}

function protocolUpdater(setProtocol: Dispatch<SetStateAction<E.Protocol>>): E.UpdateProtocol {
  return (updater) => {
    setProtocol((previous) => {
      const next = structuredClone(previous);
      updater(next);
      return next;
    });
  };
}

function useProtocolExampleSync({
  languagesCount,
  temperatureCount,
  setProtocol,
  setCommitted,
}: {
  languagesCount: number;
  temperatureCount: number;
  setProtocol: Dispatch<SetStateAction<E.Protocol>>;
  setCommitted: Dispatch<SetStateAction<E.Protocol>>;
}) {
  useEffect(() => {
    setProtocol((previous) => resizeEvaluation(previous, languagesCount, temperatureCount));
    setCommitted((previous) => resizeEvaluation(previous, languagesCount, temperatureCount));
  }, [languagesCount, temperatureCount, setProtocol, setCommitted]);
}

function useProtocolUiState(initialMode: string) {
  const [mode, setMode] = useState(initialMode);
  const [activeSection, setActiveSection] = useState("manifest");
  const [templateOpen, setTemplateOpen] = useState(false);
  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);
  return { mode, setMode, activeSection, setActiveSection, templateOpen, setTemplateOpen };
}

interface ProtocolEditorProps {
  mode?: string;
  errorLevel?: string;
  adminMode?: boolean;
  languagesCount?: number;
  temperatureCount?: number;
}

function useProtocolEditorState({
  mode: initialMode = "form",
  errorLevel = "some",
  adminMode = false,
  languagesCount = 7,
  temperatureCount = 6,
}: ProtocolEditorProps) {
  const ui = useProtocolUiState(initialMode);
  const [protocol, setProtocol] = useState(() => createProtocol(languagesCount, temperatureCount));
  const [committed, setCommitted] = useState(protocol);
  useProtocolExampleSync({
    languagesCount,
    temperatureCount,
    setProtocol,
    setCommitted,
  });

  const { errors, warnings } = useMemo(() => validate(protocol), [protocol, adminMode, errorLevel]);
  const errorsBySection = useMemo(() => groupIssues(errors, warnings), [errors, warnings]);
  const dirty = useMemo(
    () => JSON.stringify(protocol) !== JSON.stringify(committed),
    [protocol, committed],
  );
  const canApply = errors.length === 0 && dirty;
  const setP = protocolUpdater(setProtocol);
  const yamlText = useMemo(() => serialize(protocol), [protocol]);
  return {
    ...ui,
    dirty,
    setProtocol,
    errors,
    warnings,
    yamlText,
    errorsBySection,
    adminMode,
    protocol,
    setP,
    canApply,
    committed,
    setCommitted,
  };
}

type ProtocolEditorLayoutProps = ReturnType<typeof useProtocolEditorState>;

export const ProtocolEditor = (props: ProtocolEditorProps) => {
  return <ProtocolEditorLayout {...useProtocolEditorState(props)} />;
};

function ProtocolEditorLayout(props: ProtocolEditorLayoutProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <ProtocolEditorChromeBlock {...props} />
      <ProtocolEditorBodyBlock {...props} />
      <ProtocolEditorActionBar
        {...{
          dirty: props.dirty,
          canApply: props.canApply,
          errors: props.errors,
          warnings: props.warnings,
          setProtocol: props.setProtocol,
          committed: props.committed,
          setCommitted: props.setCommitted,
          protocol: props.protocol,
        }}
      />
    </div>
  );
}

function ProtocolEditorChromeBlock(props: ProtocolEditorLayoutProps) {
  return (
    <>
      <EditorChrome
        mode={props.mode}
        setMode={props.setMode}
        dirty={props.dirty}
        onTemplates={() => {
          props.setTemplateOpen((value) => !value);
        }}
      />
      {props.templateOpen && (
        <TemplatePicker
          onClose={() => {
            props.setTemplateOpen(false);
          }}
          onPick={(id) => {
            if (id === "reset") props.setProtocol(structuredClone(DEFAULT_PROTOCOL));
            props.setTemplateOpen(false);
          }}
        />
      )}
      {props.dirty && <DigestBanner />}
      {props.errors.length > 0 && (
        <ErrorBanner
          errors={props.errors}
          onJump={(section) => {
            props.setMode("form");
            props.setActiveSection(section);
          }}
        />
      )}
    </>
  );
}

function ProtocolEditorBodyBlock(props: ProtocolEditorLayoutProps) {
  if (props.mode === "yaml") return <YamlView text={props.yamlText} />;
  return (
    <div className={visual.grid}>
      <SectionNav
        active={props.activeSection}
        onChange={props.setActiveSection}
        errorsBySection={props.errorsBySection}
        adminMode={props.adminMode}
      />
      <ProtocolEditorSection
        activeSection={props.activeSection}
        protocol={props.protocol}
        setP={props.setP}
        errors={props.errors}
        adminMode={props.adminMode}
        warnings={props.warnings}
      />
    </div>
  );
}
