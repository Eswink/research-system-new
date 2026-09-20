import type { ModelDriftDto, ModelReadDto, ProbeResultDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

export function ModelDetails({ model }: { model: ModelReadDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <PanelSection title={zh ? "模型身份与能力声明" : "Model identity and capability assertions"}>
      <KeyValueList
        fields={[
          { label: "ID", value: model.id },
          { label: "Model", value: model.model_name },
          { label: "Endpoint", value: model.endpoint_id },
          { label: "Version", value: model.version },
        ]}
      />
      <DeclaredParameters model={model} />
      <CapabilityAssertions model={model} />
    </PanelSection>
  );
}

/** 声明参数（EC-02）：读面可见 + 明说「声明不等于已生效」。 */
function DeclaredParameters({ model }: { model: ModelReadDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const window =
    model.context_window_tokens === null
      ? null
      : `${String(model.context_window_tokens)} tokens`;
  const declared = window !== null || model.thinking_intensity !== null;
  return (
    <div data-testid="model-declared-parameters">
      <KeyValueList
        fields={[
          {
            label: zh ? "声明上下文窗口" : "Declared context window",
            value: window ?? undeclaredText(zh),
          },
          {
            label: zh ? "声明思考强度" : "Declared thinking intensity",
            value: model.thinking_intensity ?? undeclaredText(zh),
          },
        ]}
      />
      <p className={styles.notice}>{declarationNotice(declared, zh)}</p>
    </div>
  );
}

function undeclaredText(zh: boolean): string {
  return zh ? "未声明" : "not declared";
}

function declarationNotice(declared: boolean, zh: boolean): string {
  if (!declared) {
    return zh
      ? "尚无参数声明；未声明不等于使用默认值。"
      : "No parameter declarations; undeclared does not mean a default is applied.";
  }
  return zh
    ? "声明值：本版本不发送给 provider，也不参与 eligibility 判定。"
    : [
        "Declared values: not sent to the provider and not used for eligibility ",
        "in this version.",
      ].join("");
}

function CapabilityAssertions({ model }: { model: ModelReadDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const assertions = Object.entries(model.capabilities);
  if (assertions.length === 0)
    return (
      <EmptyState
        message={
          zh
            ? "尚无能力声明，不等于不支持"
            : "No capability assertions; this does not imply unsupported"
        }
      />
    );
  return (
    <ul className={styles.list}>
      {assertions.map(([name, assertion]) => (
        <li key={name} className={styles.card}>
          <div className={styles.cardHead}>
            <span className="mono">{name}</span>
            <Chip>{assertion.status}</Chip>
          </div>
          <KeyValueList
            fields={[
              { label: zh ? "来源" : "Source", value: assertion.source },
              { label: zh ? "声明置信度" : "Assertion confidence", value: assertion.confidence },
              { label: "Probe version", value: assertion.probe_version ?? "—" },
            ]}
          />
        </li>
      ))}
    </ul>
  );
}

export function ProbeSummary({ probe }: { probe: ProbeResultDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <div data-testid="probe-summary" className={styles.page}>
      <PanelSection
        title={zh ? "真实探测结果" : "Actual probe result"}
        extra={<Chip tone={probe.ok ? "success" : "danger"}>{probe.ok ? "OK" : "ERROR"}</Chip>}
      >
        <ModelDriftNotice drift={probe.drift} zh={zh} />
        <KeyValueList
          fields={[
            { label: "Model ID", value: probe.model_id },
            {
              label: zh ? "返回模型名" : "Returned model",
              value: probe.returned_model_name ?? "—",
            },
            { label: zh ? "探测时间" : "Probed at", value: probe.probed_at ?? "—" },
            {
              label: zh ? "观察到的能力" : "Observed capabilities",
              value: probe.observed_capabilities.join(", "),
            },
            { label: zh ? "错误类别" : "Error category", value: probe.error_category ?? "—" },
            {
              label: zh ? "脱敏详情" : "Redacted detail",
              value: probe.error_message_redacted ?? "—",
            },
          ]}
        />
        <p className={styles.notice}>
          {probe.provider_fingerprint_available
            ? "Configuration reproducible / provider fingerprint available"
            : "Configuration reproducible / provider fingerprint unavailable"}
        </p>
      </PanelSection>
      <ProbeFailures probe={probe} />
    </div>
  );
}

/**
 * 漂移三态（GOAL-008 EC-05 / AGENTS.md §4）：登记声明值 vs provider 返回标识。
 *
 * **`UNKNOWN` 必须自带反义**——它是「无法证明一致」，不是「已证明一致」；
 * 只显示一个中性标签会让「没探到」被读成「没问题」，那正是 §4 要禁止的美化。
 * `DRIFT` 必须点名两个值，让读的人自己判断差在哪。
 */
function ModelDriftNotice({ drift, zh }: { drift: ModelDriftDto; zh: boolean }) {
  const tone = drift.state === "MATCH" ? "success" : drift.state === "DRIFT" ? "danger" : "neutral";
  const label = zh
    ? { MATCH: "一致", DRIFT: "漂移", UNKNOWN: "未知" }[drift.state]
    : { MATCH: "Match", DRIFT: "Drift", UNKNOWN: "Unknown" }[drift.state];
  const explanation = zh
    ? {
        MATCH: "声明值与 provider 返回的模型标识一致（精确匹配）。",
        DRIFT: "声明值与 provider 返回的模型标识不同：请核对是不是同一底层模型。",
        UNKNOWN: "未探到模型标识——**未知不等于无漂移**（可能没探到或探测失败）。",
      }[drift.state]
    : {
        MATCH: "Declared value and the identifier returned by the provider agree (exact match).",
        DRIFT: "Declared value differs from the identifier returned by the provider — " +
          "check whether this is the same underlying model.",
        UNKNOWN: "No model identifier was returned — unknown is not the same as no drift " +
          "(not probed, or the probe failed).",
      }[drift.state];
  return (
    <div data-testid="probe-drift" data-drift-state={drift.state} className={styles.notice}>
      <p>
        <strong>{zh ? "模型标识漂移" : "Model identifier drift"}</strong>{" "}
        <Chip tone={tone}>{label}</Chip>
      </p>
      <p>{explanation}</p>
      <p>
        {zh ? "声明" : "Declared"}: <code>{drift.declared_model_name}</code>
        {" · "}
        {zh ? "返回" : "Returned"}: <code>{drift.returned_model_name ?? "—"}</code>
      </p>
    </div>
  );
}

function ProbeFailures({ probe }: { probe: ProbeResultDto }) {
  const { language } = useI18n();
  if (probe.capability_failures.length === 0) return null;
  return (
    <PanelSection title={language === "zh" ? "能力探测失败明细" : "Capability probe failures"}>
      <ul className={styles.list}>
        {probe.capability_failures.map((failure) => (
          <li key={failure.capability} className={styles.notice}>
            <strong>{failure.capability}</strong> · {failure.error_category ?? "UNKNOWN"}
            <p>{failure.error_message_redacted ?? "—"}</p>
          </li>
        ))}
      </ul>
    </PanelSection>
  );
}
