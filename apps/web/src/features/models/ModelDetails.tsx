import type { ModelReadDto, ProbeResultDto } from "../../api/types";
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
