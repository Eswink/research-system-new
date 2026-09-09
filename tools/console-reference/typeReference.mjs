/** One-time, explicit type annotations for the audited native reference migration. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const root = "apps/web/src/features/example-console/reference";
const types = {
  ActionBar:
    "{ dirty: boolean; canApply: boolean; errorCount: number; warnCount: number; onDiscard: () => void; onApply: () => void }",
  ApprovalCard:
    "{ approval: E.Approval; selected: boolean; expanded: boolean; onSelect: () => void; onToggle: () => void; onDecide: (decision: string) => void }",
  BarSeries:
    "{ data: { label: string; values: number[] }[]; series: { color: string; label?: string }[]; width?: number; height?: number; showLabels?: boolean; showGrid?: boolean }",
  BudgetDonut:
    "{ reservations: E.Protocol['budget']['reservations']; cap: number; palette: string[] }",
  BudgetMetricCard: "E.MetricProps",
  MetricCard: "E.MetricProps",
  BudgetSection: "E.ProtocolSectionProps",
  EvaluationSection: "E.ProtocolSectionProps",
  GatesSection: "E.ProtocolSectionProps",
  ManifestSection: "E.ProtocolSectionProps",
  ObjectivesSection: "E.ProtocolSectionProps",
  PolicySection: "E.ProtocolSectionProps",
  TeamSection: "E.ProtocolSectionProps",
  BundleStat: "{ label: R.ReactNode; value: R.ReactNode; sub?: R.ReactNode; unknown?: boolean }",
  ChipMultiSelect:
    "{ items: string[]; available: (string | { code: string; label: string })[]; onAdd: (value: string) => void; onRemove: (value: string) => void; onFreeAdd?: ((value: string) => void) | undefined }",
  ClaimDetail: "{ claim: E.Claim }",
  ClaimsGraph: "{ claims: E.Claim[]; selectedId: string; onSelect: (id: string) => void }",
  ClaimsScreen: "{ initialView?: string }",
  ClaimsTable: "{ claims: E.Claim[]; selectedId: string; onSelect: (id: string) => void }",
  ClaimStatusBadge: "{ status: string }",
  ExpStatusBadge: "{ status: string }",
  ProjectStatusBadge: "{ status: string }",
  PromptStatusBadge: "{ status: string }",
  ReportStatusBadge: "{ status: string }",
  PreflightBadge: "{ status: string }",
  SectionStatusChip: "{ status: string }",
  RunStateBadge: "{ state: string }",
  CommandPalette: "{ open: boolean; onClose: () => void; items?: E.CommandItem[] }",
  ConsRow: "{ icon: string; tone: string; label: R.ReactNode }",
  ContextMenu: "{ x: number; y: number; items: E.MenuItem[]; onClose: () => void }",
  DigestText:
    "{ value?: string | null | undefined; prefix?: boolean; length?: number; label?: string; onCopy?: (() => void) | undefined }",
  Donut:
    "{ values: { label?: string; value: number; color: string }[]; size?: number; thickness?: number; center?: R.ReactNode }",
  Drawer:
    "{ open: boolean; onClose: () => void; title: R.ReactNode; subtitle?: R.ReactNode; width?: number; children?: R.ReactNode; footer?: R.ReactNode }",
  DrawerSection: "{ title: R.ReactNode; children: R.ReactNode }",
  DryRunScreen:
    "{ preflightState?: 'PASS' | 'WARN' | 'FAIL'; protocolMode?: string; protocolErrorLevel?: string; protocolLanguages?: number; protocolTemperatures?: number; protocolAdminMode?: boolean }",
  EditorChrome:
    "{ mode: string; setMode: (mode: string) => void; dirty: boolean; onTemplates: () => void }",
  EmptyState:
    "{ icon?: string; title: string; description: string; cta?: E.Cta; secondaryCta?: E.Cta; kicker?: string }",
  ErrCount: "{ tone: string; n: number }",
  ErrorBanner: "{ errors: E.ProtocolIssue[]; onJump: (section: string) => void }",
  EventDrawer: "{ ev: E.Event; onClose: () => void }",
  EventRow: "{ ev: E.Event; selected: boolean; onClick: () => void; isLatest?: boolean }",
  EvidenceRow: "{ ev: E.Evidence }",
  ExperimentCalendar: "{ experiments: E.Experiment[] }",
  ExperimentMatrix: "{ experiments: E.Experiment[] }",
  ExperimentDetail: "{ experiment: E.Experiment }",
  ExperimentQueue: "{ queue: E.Experiment[]; selectedId: string; onSelect: (id: string) => void }",
  Field:
    "{ label: R.ReactNode; hint?: R.ReactNode; tooltip?: string; error?: E.ProtocolIssue; children: R.ReactNode; locked?: boolean; badge?: R.ReactNode }",
  FileNode:
    "{ node: E.FileEntry; depth: number; selected: string; onSelect: (name: string) => void }",
  FilterChips:
    "{ filters: { key: string; field: string; value: string }[]; onRemove?: (key: string) => void }",
  FindingRow: "{ finding: E.Finding; selected: boolean; onSelect: () => void }",
  ForceGraph:
    "{ nodes: E.GraphNode[]; edges: E.GraphEdge[]; width?: number; height?: number; groupColors?: Record<string, string>; onNodeClick?: (id: string) => void; selectedId?: string }",
  FormField: "{ label: R.ReactNode; children: R.ReactNode }",
  FormRow: "{ label: R.ReactNode; hint?: R.ReactNode; required?: boolean; children: R.ReactNode }",
  GateChip: "{ type: string }",
  HealthGauge: "{ value?: number; size?: number; label?: string }",
  Heatmap:
    "{ data: number[][]; xLabels?: string[]; yLabels?: string[]; cell?: number; gap?: number; color?: string }",
  Icon: "{ name?: string | undefined; size?: number; style?: R.CSSProperties | undefined }",
  kv: "{ k: R.ReactNode; v: R.ReactNode; unknown?: boolean; warn?: boolean }",
  LineSeries:
    "{ data: E.LineData[]; xLabels?: string[]; width?: number; height?: number; colors?: string[]; yFormat?: (value: number) => R.ReactNode; showGrid?: boolean }",
  LiveIndicator: "{ state?: string; behind?: number }",
  Modal:
    "{ open: boolean; onClose: () => void; title: R.ReactNode; children?: R.ReactNode; footer?: R.ReactNode; width?: number }",
  NotificationBell: "{ items?: E.Notification[]; onOpenAll: () => void }",
  NotifRow: "{ label: string; desc: string; value: boolean; onChange: (value: boolean) => void }",
  ObjectiveRow: "{ id: string; statement: string; status: string }",
  PageToolbar:
    "{ title: R.ReactNode; subtitle?: R.ReactNode; children?: R.ReactNode; actions?: R.ReactNode }",
  PECustomIcon: "{ name?: string | undefined }",
  PriorityChip: "{ priority: string }",
  ProjectDetail: "{ project: E.Project }",
  ProjectForm: "{ project?: E.Project | undefined }",
  ProjectsBoardView: "E.ProjectsViewProps",
  ProjectsGridView: "E.ProjectsViewProps",
  ProjectsListView: "E.ProjectsViewProps",
  PromptAB: "{ prompt: E.Prompt }",
  PromptEditor: "{ prompt: E.Prompt }",
  ProtocolEditor:
    "{ mode?: string; errorLevel?: string; adminMode?: boolean; languagesCount?: number; temperatureCount?: number }",
  QuickCreate: "{ onCreate: (type: string) => void }",
  ReportForm: "{ report?: E.Report | undefined }",
  ReportPreview: "{ report: E.Report; onEdit: () => void }",
  ReproducibilityChip:
    "{ fingerprint?: string | null | undefined; providerAvailable?: boolean; compact?: boolean }",
  RunDiffView: "{ aId?: string | undefined; bId?: string | undefined }",
  Sankey: "{ nodes: E.SankeyNode[]; flows: E.SankeyFlow[]; width?: number; height?: number }",
  SearchInput:
    "{ value: string; onChange: (value: string) => void; placeholder?: string; width?: number }",
  Section: "{ label: R.ReactNode; children: R.ReactNode }",
  SectionHeader: "{ title: R.ReactNode; subtitle?: R.ReactNode; extra?: R.ReactNode }",
  SectionNav:
    "{ active: string; onChange: (id: string) => void; errorsBySection: Record<string, { errors: number; warnings: number }>; adminMode: boolean }",
  SegmentedField:
    "{ value: string; onChange: (value: string) => void; options: E.Option[]; disabled?: boolean }",
  SegmentedToggle: "{ value: string; onChange: (value: string) => void; options: E.Option[] }",
  Select: "{ value?: string | undefined; onChange?: (value: string) => void; options: E.Option[] }",
  SettingsPage:
    "{ title: R.ReactNode; subtitle?: R.ReactNode; action?: R.ReactNode; children: R.ReactNode }",
  Sparkline:
    "{ data: number[]; width?: number; height?: number; stroke?: string; fill?: string; strokeWidth?: number }",
  StateDemo: "{ children: R.ReactNode }",
  StatusBadge: "E.BadgeProps",
  TagInput: "{ tags?: string[]; onChange: (tags: string[]) => void }",
  TemperatureGrid: "{ values: number[]; onChange: (values: number[]) => void }",
  TemplatePicker: "{ onPick: (id: string) => void; onClose: () => void }",
  TextArea:
    "{ value: string; onChange: (value: string) => void; rows?: number; mono?: boolean; placeholder?: string }",
  TextInput:
    "Omit<R.InputHTMLAttributes<HTMLInputElement>, 'onChange'> & { onChange?: ((value: string) => void) | undefined; mono?: boolean }",
  Toggle: "{ on: boolean; onToggle: () => void }",
  TooltipIcon: "{ text: string }",
  TrendBadge: "{ delta: number; inverted?: boolean; format?: (value: number) => string }",
  UnknownValue: "{ hint?: string }",
  WorkspaceSwitcher: "{ workspaces: E.Workspace[] }",
  YamlView: "{ text: string }",
  ZoneHeader: "{ icon: string; title: R.ReactNode; count?: number; extra?: R.ReactNode }",
  findErr: ["E.ProtocolIssue[]", "string"],
  fmtDuration: ["number | null"],
  fmtMinor: ["number | null | undefined"],
  fmtVal: ["number | null | undefined", "string"],
  getEventSummary: ["E.Event"],
  getEventTypeStyle: ["string"],
  sectionText: ["string"],
  serializeProtocol: ["E.Protocol"],
  validateProtocol: ["E.Protocol", "boolean", "string"],
};
for (const [name, annotation] of Object.entries(types)) {
  const file = [name + ".tsx", name + ".ts"].map((x) => path.join(root, x)).find(fs.existsSync);
  if (!file) throw new Error("Missing " + name);
  let text = fs.readFileSync(file, "utf8");
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const st = sf.statements.find(
    (n) =>
      ts.isVariableStatement(n) && n.modifiers?.some((m) => m.kind === ts.SyntaxKind.ExportKeyword),
  );
  const fn = st.declarationList.declarations[0].initializer;
  const annotations = typeof annotation === "string" ? [annotation] : annotation;
  const edits = fn.parameters
    .map((param, index) => ({ pos: param.name.end, text: ": " + annotations[index] }))
    .reverse();
  for (const edit of edits) text = text.slice(0, edit.pos) + edit.text + text.slice(edit.pos);
  const joined = annotations.join(" ");
  if (joined.includes("R.")) text = 'import type * as R from "react";\n' + text;
  if (joined.includes("E.")) text = 'import type * as E from "../exampleTypes";\n' + text;
  fs.writeFileSync(file, text, "utf8");
}
console.log(
  "Annotated",
  Object.keys(types).length,
  "declarations without any or suppressed diagnostics",
);
