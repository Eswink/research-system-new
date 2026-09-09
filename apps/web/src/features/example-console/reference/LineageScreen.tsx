import { useMemo, useState, type Dispatch, type SetStateAction } from "react";
import FIX_CLAIMS from "../data/claims.json";
import FIX_DATASETS from "../data/datasets.json";
import FIX_PROMPTS from "../data/prompts.json";
import FIX_REGISTERED_MODELS from "../data/registered-models.json";
import FIX_RUNS_HISTORY from "../data/runs-history.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./LineageScreen.module.css";
import { LineageEmptyTitle } from "./lineage-screen/LineageEmptyTitle";
import { LineageSection } from "./lineage-screen/LineageSection";
import { LineageTitle } from "./lineage-screen/LineageTitle";

interface LineageNode {
  id: string;
  label: string;
  kind: string;
}

interface LineageEdge {
  from: string;
  to: string;
}

const KIND_COLORS: Record<string, string> = {
  dataset: "var(--success)",
  prompt: "var(--accent)",
  run: "var(--warn)",
  model: "var(--unknown)",
  endpoint: "var(--fg-muted)",
  claim: "var(--danger)",
};

const KIND_ICONS: Record<string, string> = {
  dataset: "book",
  prompt: "diamond",
  run: "play",
  model: "hex",
  endpoint: "wifi",
  claim: "shield",
};

function buildLineageNodes(): LineageNode[] {
  const nodes: LineageNode[] = [];
  FIX_DATASETS.slice(0, 3).forEach((item) => {
    nodes.push({ id: item.id, label: item.name.slice(0, 20), kind: "dataset" });
  });
  FIX_PROMPTS.slice(0, 3).forEach((item) => {
    nodes.push({ id: item.id, label: item.name.slice(0, 20), kind: "prompt" });
  });
  FIX_RUNS_HISTORY.slice(0, 4).forEach((item) => {
    nodes.push({ id: item.id, label: item.label.slice(0, 20), kind: "run" });
  });
  FIX_REGISTERED_MODELS.slice(0, 3).forEach((item) => {
    nodes.push({ id: item.id, label: item.family.slice(0, 20), kind: "model" });
  });
  FIX_CLAIMS.slice(0, 4).forEach((item) => {
    nodes.push({ id: item.id, label: (item.statement || item.id).slice(0, 20), kind: "claim" });
  });
  nodes.push({ id: "ep_prod_us_east", label: "prod-us-east", kind: "endpoint" });
  nodes.push({ id: "ep_stg_eu", label: "stg-eu-frankfurt", kind: "endpoint" });
  return nodes;
}

function buildLineageEdges(): LineageEdge[] {
  const datasets = FIX_DATASETS.slice(0, 3);
  const prompts = FIX_PROMPTS.slice(0, 3);
  const runs = FIX_RUNS_HISTORY.slice(0, 4);
  const models = FIX_REGISTERED_MODELS.slice(0, 3);
  const claims = FIX_CLAIMS.slice(0, 4);
  const edges: LineageEdge[] = [];
  datasets.forEach((item, index) => {
    const prompt = prompts[index];
    const run = runs[index];
    if (prompt !== undefined) edges.push({ from: item.id, to: prompt.id });
    if (run !== undefined) edges.push({ from: item.id, to: run.id });
  });
  prompts.forEach((item, index) => {
    const run = runs[index];
    if (run !== undefined) edges.push({ from: item.id, to: run.id });
  });
  runs.forEach((item, index) => {
    const model = models[index % models.length];
    const claim = claims[index];
    if (model !== undefined) edges.push({ from: model.id, to: item.id });
    if (claim !== undefined) edges.push({ from: item.id, to: claim.id });
  });
  if (models[0] !== undefined) edges.push({ from: models[0].id, to: "ep_prod_us_east" });
  if (models[1] !== undefined) edges.push({ from: models[1].id, to: "ep_stg_eu" });
  return edges;
}

function traverseGraph(startId: string, direction: "up" | "down", edges: LineageEdge[]): string[] {
  const visited = new Set([startId]);
  const stack = [startId];
  while (stack.length > 0) {
    const current = stack.pop();
    edges.forEach((edge) => {
      const next =
        direction === "up"
          ? edge.to === current
            ? edge.from
            : null
          : edge.from === current
            ? edge.to
            : null;
      if (next !== null && !visited.has(next)) {
        visited.add(next);
        stack.push(next);
      }
    });
  }
  visited.delete(startId);
  return [...visited];
}

export const LineageScreen = () => {
  const { t } = useI18n();
  const [selectedNode, setSelectedNode] = useState("mdl_claude_opus_41");
  const [filter, setFilter] = useState("all"); // all | upstream | downstream
  const nodes = useMemo(buildLineageNodes, []);
  const edges = useMemo(buildLineageEdges, []);
  const selected = nodes.find((n) => n.id === selectedNode);
  const upstream = selectedNode ? traverseGraph(selectedNode, "up", edges) : [];
  const downstream = selectedNode ? traverseGraph(selectedNode, "down", edges) : [];

  const filteredNodeIds =
    filter === "all"
      ? null
      : filter === "upstream"
        ? new Set([selectedNode, ...upstream])
        : new Set([selectedNode, ...downstream]);

  const graphNodes = nodes.map((n) => ({
    id: n.id,
    label: n.label,
    group: n.kind,
    highlighted: filteredNodeIds
      ? filteredNodeIds.has(n.id)
      : n.id === selectedNode || upstream.includes(n.id) || downstream.includes(n.id),
  }));
  return (
    <LineageScreenLayout
      {...{
        t,
        filter,
        setFilter,
        nodes,
        edges,
        graphNodes,
        setSelectedNode,
        selectedNode,
        selected,
        upstream,
        downstream,
      }}
    />
  );
};

interface LineageScreenLayoutProps {
  t: (key: string, fallback?: string) => string;
  filter: string;
  setFilter: Dispatch<SetStateAction<string>>;
  nodes: LineageNode[];
  edges: LineageEdge[];
  graphNodes: { id: string; label: string; group: string; highlighted: boolean }[];
  setSelectedNode: Dispatch<SetStateAction<string>>;
  selectedNode: string;
  selected: LineageNode | undefined;
  upstream: string[];
  downstream: string[];
}

function LineageScreenLayout(props: LineageScreenLayoutProps) {
  return (
    <div className={visual.column}>
      <LineageTitle t={props.t} filter={props.filter} setFilter={props.setFilter} />

      <div className={visual.grid}>
        <LineageSection
          {...{
            t: props.t,
            nodes: props.nodes,
            edges: props.edges,
            kindColors: KIND_COLORS,
            kindIcons: KIND_ICONS,
            graphNodes: props.graphNodes,
            setSelectedNode: props.setSelectedNode,
            selectedNode: props.selectedNode,
          }}
        />

        <LineageEmptyTitle
          {...{
            selected: props.selected,
            kindIcons: KIND_ICONS,
            kindColors: KIND_COLORS,
            t: props.t,
            upstream: props.upstream,
            downstream: props.downstream,
            nodes: props.nodes,
            setSelectedNode: props.setSelectedNode,
          }}
        />
      </div>
    </div>
  );
}
