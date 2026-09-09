import type { SourceSelection } from "../navigation/presentationPolicy";
import { useState, type Dispatch, type SetStateAction } from "react";
import { Drawer } from "../components/Drawer";
import { useI18n } from "../i18n/useI18n";
import { usePresentation } from "../navigation/usePresentation";
import styles from "./SourceControl.module.css";

/** Always-visible provenance; example data never masquerades as a live connection. */
export function SourceControl() {
  const { source, selection, setSource, reason } = usePresentation();
  const { language } = useI18n();
  const [details, setDetails] = useState(false);
  const zh = language === "zh";
  return (
    <div className={styles.control} data-testid="data-source-control" data-source={source}>
      <button
        type="button"
        className={styles.badge}
        data-testid="data-source-badge"
        data-source={source}
        onClick={() => {
          setDetails(true);
        }}
      >
        {source === "example"
          ? zh
            ? "示例数据 · 不写入后端"
            : "EXAMPLE · NO API WRITES"
          : zh
            ? "真实 API"
            : "REAL API"}
      </button>
      <button
        type="button"
        className="btn sm ghost"
        data-testid={`mode-${source === "live" ? "example" : "live"}`}
        onClick={() => {
          setSource(source === "live" ? "example" : "live");
        }}
      >
        {source === "live" ? (zh ? "查看示例" : "Example") : zh ? "真实操作" : "Live"}
      </button>
      <SourceControlDetailsDrawer
        {...{ details, setDetails, zh, source, reason, selection, setSource }}
      />
    </div>
  );
}

function SourceDescription({ source, zh }: { source: string; zh: boolean }) {
  const text =
    source === "example"
      ? zh
        ? "本页全部数据来自设计包固定示例。筛选、选择与模拟修改仅存在于当前页面内存，不调用真实 API，不计入费用、评测、审计或研究证据。切换页面将重置示例。"
        : [
            "All page data is a fixed design example. Filters and simulated edits are ",
            "page-local. They never enter APIs, billing, evaluation, audit or research ",
            "evidence. Navigation resets examples.",
          ].join("")
      : zh
        ? "真实数据只来自现有后端。加载失败不会自动展示示例，未接入操作保持不可用。"
        : [
            "Live data comes only from the existing backend. Failed loads never fall ",
            "back to examples.",
          ].join("");
  return <p>{text}</p>;
}

interface SourceControlDetailsDrawerProps {
  details: boolean;
  setDetails: Dispatch<SetStateAction<boolean>>;
  zh: boolean;
  source: string;
  reason: string;
  selection: string;
  setSource: (source: SourceSelection) => void;
}

function SourceControlDetailsDrawer({
  details,
  setDetails,
  zh,
  source,
  reason,
  selection,
  setSource,
}: SourceControlDetailsDrawerProps) {
  return (
    <Drawer
      open={details}
      onClose={() => {
        setDetails(false);
      }}
      title={zh ? "数据来源与能力边界" : "Data provenance and capability boundaries"}
      width={440}
    >
      <SourceDescription source={source} zh={zh} />
      {reason && <p>{reason}</p>}
      <p>
        {zh ? "当前来源选择：" : "Selection: "}
        {selection}
      </p>
      <button
        type="button"
        className="btn"
        data-testid="mode-auto"
        onClick={() => {
          setSource("auto");
          setDetails(false);
        }}
      >
        {zh
          ? "自动：已接入页面用真实数据，缺口页面用示例"
          : "Auto: live where supported, examples for missing contracts"}
      </button>
    </Drawer>
  );
}
