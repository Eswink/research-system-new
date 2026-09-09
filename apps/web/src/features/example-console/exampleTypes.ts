import type * as R from "react";
import type agents from "./data/agents.json";
import type approvals from "./data/approvals.json";
import type claims from "./data/claims.json";
import type events from "./data/events.json";
import type evidence from "./data/evidence.json";
import type experiments from "./data/experiment-queue.json";
import type models from "./data/models.json";
import type notifications from "./data/notifications.json";
import type preflight from "./data/preflight.json";
import type projects from "./data/projects.json";
import type prompts from "./data/prompts.json";
import type reports from "./data/reports.json";
import type workspaces from "./data/workspaces.json";
import type { DEFAULT_PROTOCOL } from "./reference/defaultProtocol";

/** Presentation examples only; these are NOT API DTOs or canonical Domain entities. */
export type Project = Omit<(typeof projects)[number], "archived_at"> & {
  archived_at?: string | null | undefined;
  notes?: string;
  autonomy?: string;
};
export type Agent = (typeof agents)[number];
export type Model = (typeof models)[number];
export type Claim = (typeof claims)[number];
export type Evidence = (typeof evidence)[number];
export type Event = (typeof events)[number];
export type Approval = (typeof approvals)[number];
export type Experiment = (typeof experiments)[number];
export type Prompt = (typeof prompts)[number];
export type Report = (typeof reports)[number];
export type Notification = (typeof notifications)[number];
export type Workspace = (typeof workspaces)[number];
export type Finding = (typeof preflight.WARN.findings)[number];
export type Protocol = typeof DEFAULT_PROTOCOL;
export type UpdateProtocol = (updater: (draft: Protocol) => void) => void;
export interface ProtocolIssue {
  path: string;
  section: string;
  severity: string;
  code: string;
  message: string;
}
export interface ProtocolSectionProps {
  value: Protocol;
  setP: UpdateProtocol;
  errors: ProtocolIssue[];
  warnings?: ProtocolIssue[] | undefined;
  adminMode?: boolean | undefined;
}
export interface Option {
  value: string;
  label: string;
  icon?: string | undefined;
  disabled?: boolean | undefined;
}
export interface BadgeProps {
  tone?: string | undefined;
  label?: R.ReactNode;
  icon?: string | undefined;
  dashed?: boolean | undefined;
  filled?: boolean | undefined;
  size?: string | undefined;
}
export interface MetricProps {
  label: R.ReactNode;
  value: R.ReactNode;
  sub?: R.ReactNode;
  bar?: number | null | undefined;
  barColor?: string | undefined;
  unknownWarn?: boolean | undefined;
  trend?: number | null | undefined;
  spark?: number[] | undefined;
  sparkColor?: string | undefined;
}
export interface Cta {
  label: string;
  icon?: string | undefined;
  onClick: () => void;
}
export interface MenuItem {
  label?: string | undefined;
  icon?: string | undefined;
  shortcut?: string | undefined;
  danger?: boolean | undefined;
  divider?: boolean | undefined;
  action?: (() => void) | undefined;
  disabled?: boolean | undefined;
}
export interface CommandItem {
  id?: string;
  label: string;
  icon?: string;
  group?: string;
  hint?: string;
  section?: string;
  shortcut?: string;
  action: () => void;
}
export interface ProjectsViewProps {
  projects: Project[];
  onOpen: (project: Project) => void;
  onContextMenu: (event: R.MouseEvent, project: Project) => void;
}
export type ProjectDrawer =
  { mode: "create"; project?: undefined } | { mode: "view" | "edit"; project: Project };
export type ReportDrawer =
  { mode: "create"; report?: undefined } | { mode: "edit"; report: Report };
export interface GraphNode {
  id: string;
  label: string;
  group: string;
  highlighted?: boolean | undefined;
}
export interface GraphEdge {
  from: string;
  to: string;
}
export interface SankeyNode {
  id: string;
  label: string;
  type: string;
  col?: number;
}
export interface SankeyFlow {
  from: string;
  to: string;
  value: number;
}
export interface FileEntry {
  name?: string;
  type: string;
  highlight?: boolean;
  modified?: string;
  children?: FileEntry[];
  size?: string;
  digest?: string;
  path: string;
}
export interface LineData {
  label?: string;
  name?: string;
  values: number[];
}
