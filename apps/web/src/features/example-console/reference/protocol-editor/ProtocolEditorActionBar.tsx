import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import { ActionBar } from "../ActionBar";

interface ProtocolEditorActionBarProps {
  dirty: boolean;
  canApply: boolean;
  errors: E.ProtocolIssue[];
  warnings: E.ProtocolIssue[];
  setProtocol: Dispatch<
    SetStateAction<{
      protocol_version: string;
      manifest: { id: string; name: string; autonomy_level: string };
      objectives: { id: string; statement: string }[];
      team: {
        template: string;
        overrides: (
          | { role: string; instances: number; collapse_when: string }
          | { role: string; instances: null; collapse_when: string }
        )[];
      };
      evaluation: {
        benchmarks: string[];
        languages: string[];
        n_per_lang: number;
        temperature_grid: number[];
      };
      budget: {
        cap_minor: number;
        hard_stop_on_breach: boolean;
        reservations: { resource: string; minor: number }[];
      };
      gates: { kind: string; at: string }[];
      policy: { heterogeneous_review: string; memory_write: string; redact_prompts: boolean };
    }>
  >;
  committed: {
    protocol_version: string;
    manifest: { id: string; name: string; autonomy_level: string };
    objectives: { id: string; statement: string }[];
    team: {
      template: string;
      overrides: (
        | { role: string; instances: number; collapse_when: string }
        | { role: string; instances: null; collapse_when: string }
      )[];
    };
    evaluation: {
      benchmarks: string[];
      languages: string[];
      n_per_lang: number;
      temperature_grid: number[];
    };
    budget: {
      cap_minor: number;
      hard_stop_on_breach: boolean;
      reservations: { resource: string; minor: number }[];
    };
    gates: { kind: string; at: string }[];
    policy: { heterogeneous_review: string; memory_write: string; redact_prompts: boolean };
  };
  setCommitted: Dispatch<
    SetStateAction<{
      protocol_version: string;
      manifest: { id: string; name: string; autonomy_level: string };
      objectives: { id: string; statement: string }[];
      team: {
        template: string;
        overrides: (
          | { role: string; instances: number; collapse_when: string }
          | { role: string; instances: null; collapse_when: string }
        )[];
      };
      evaluation: {
        benchmarks: string[];
        languages: string[];
        n_per_lang: number;
        temperature_grid: number[];
      };
      budget: {
        cap_minor: number;
        hard_stop_on_breach: boolean;
        reservations: { resource: string; minor: number }[];
      };
      gates: { kind: string; at: string }[];
      policy: { heterogeneous_review: string; memory_write: string; redact_prompts: boolean };
    }>
  >;
  protocol: {
    protocol_version: string;
    manifest: { id: string; name: string; autonomy_level: string };
    objectives: { id: string; statement: string }[];
    team: {
      template: string;
      overrides: (
        | { role: string; instances: number; collapse_when: string }
        | { role: string; instances: null; collapse_when: string }
      )[];
    };
    evaluation: {
      benchmarks: string[];
      languages: string[];
      n_per_lang: number;
      temperature_grid: number[];
    };
    budget: {
      cap_minor: number;
      hard_stop_on_breach: boolean;
      reservations: { resource: string; minor: number }[];
    };
    gates: { kind: string; at: string }[];
    policy: { heterogeneous_review: string; memory_write: string; redact_prompts: boolean };
  };
}

export function ProtocolEditorActionBar({
  dirty,
  canApply,
  errors,
  warnings,
  setProtocol,
  committed,
  setCommitted,
  protocol,
}: ProtocolEditorActionBarProps) {
  return (
    <ActionBar
      dirty={dirty}
      canApply={canApply}
      errorCount={errors.length}
      warnCount={warnings.length}
      onDiscard={() => {
        setProtocol(committed);
      }}
      onApply={() => {
        setCommitted(protocol);
      }}
    />
  );
}
