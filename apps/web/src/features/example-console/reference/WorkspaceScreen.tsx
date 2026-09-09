import { useState } from "react";
import FIX_EXPERIMENTS from "../data/experiments.json";
import { requiredExample } from "../requiredExample";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { WorkspaceStateReprod2 } from "./workspace-screen/WorkspaceStateReprod2";

const WORKSPACE = [
  {
    path: "data/",
    type: "dir",
    children: [
      {
        path: "medhalt_v2/",
        type: "dir",
        children: [
          { path: "medhalt_v2/en_1200.jsonl", type: "file", size: "4.2 MB", modified: "14:04" },
          { path: "medhalt_v2/es_1200.jsonl", type: "file", size: "4.6 MB", modified: "14:08" },
          { path: "medhalt_v2/zh_1200.jsonl", type: "file", size: "5.1 MB", modified: "14:12" },
          { path: "medhalt_v2/ar_1200.jsonl", type: "file", size: "6.3 MB", modified: "14:18" },
        ],
      },
      { path: "internal_dosage.v3.jsonl", type: "file", size: "2.4 MB", modified: "14:03" },
    ],
  },
  {
    path: "analysis/",
    type: "dir",
    children: [
      {
        path: "analysis/es_dose_chi2.csv",
        type: "file",
        size: "18 KB",
        modified: "14:30",
        highlight: true,
      },
      {
        path: "analysis/cross_lingual_variance.csv",
        type: "file",
        size: "22 KB",
        modified: "14:33",
      },
      { path: "analysis/cot_baseline_delta.csv", type: "file", size: "9 KB", modified: "14:36" },
    ],
  },
  {
    path: "prompts/",
    type: "dir",
    children: [
      { path: "prompts/dosage_probe.tmpl", type: "file", size: "3.1 KB", modified: "14:02" },
      {
        path: "prompts/generic_name_probe.tmpl",
        type: "file",
        size: "2.8 KB",
        modified: "14:02",
      },
    ],
  },
  {
    path: "artifacts/",
    type: "dir",
    children: [
      { path: "artifacts/lit_es_47.parquet", type: "file", size: "1.2 MB", modified: "14:05" },
      { path: "artifacts/lit_zh_63.parquet", type: "file", size: "1.6 MB", modified: "14:09" },
    ],
  },
];

export const WorkspaceScreen = () => {
  const { t } = useI18n();
  const [selectedExp, setSelectedExp] = useState(
    requiredExample(FIX_EXPERIMENTS[3]).experiment_run_id,
  ); // the "not reproducible" one
  const [selectedFile, setSelectedFile] = useState("analysis/es_dose_chi2.csv");

  const exp = FIX_EXPERIMENTS.find((e) => e.experiment_run_id === selectedExp);

  return (
    <WorkspaceStateReprod2
      {...{
        t,
        workspace: WORKSPACE,
        selectedFile,
        setSelectedFile,
        setSelectedExp,
        selectedExp,
        exp,
      }}
    />
  );
};
