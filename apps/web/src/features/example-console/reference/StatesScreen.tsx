import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import { StateDemo } from "./StateDemo";
import { StatesSection } from "./states-screen/StatesSection";
import { StatesStateDemo } from "./states-screen/StatesStateDemo";
import { StatesStateDemo2 } from "./states-screen/StatesStateDemo2";
import { StatesStateDemo3 } from "./states-screen/StatesStateDemo3";
import { StatesStateDemo4 } from "./states-screen/StatesStateDemo4";
import { StatesStateDemo5 } from "./states-screen/StatesStateDemo5";
import visual from "./StatesScreen.module.css";

function stateExamples(t: (key: string, fallback?: string) => string) {
  return [...primaryStateExamples(t), ...secondaryStateExamples(t)];
}

function primaryStateExamples(t: (key: string, fallback?: string) => string) {
  return [
    {
      id: "empty",
      tone: "neutral",
      icon: "circle-o",
      title: t("sm.empty"),
      desc: t("sm.emptyDesc"),
      demo: <StatesStateDemo5 {...{ t }} />,
    },
    {
      id: "loading",
      tone: "info",
      icon: "spin",
      title: t("sm.loading"),
      desc: t("sm.loadingDesc"),
      demo: <LoadingStateDemo />,
    },
    {
      id: "error",
      tone: "danger",
      icon: "x",
      title: t("sm.error"),
      desc: t("sm.errorDesc"),
      demo: <StatesStateDemo2 {...{ t }} />,
    },
    {
      id: "partial",
      tone: "warn",
      icon: "warn-tri",
      title: t("sm.partial"),
      desc: t("sm.partialDesc"),
      demo: <StatesStateDemo {...{ t }} />,
    },
  ];
}

function secondaryStateExamples(t: (key: string, fallback?: string) => string) {
  return [
    {
      id: "forbidden",
      tone: "danger",
      icon: "lock",
      title: t("sm.forbidden"),
      desc: t("sm.forbiddenDesc"),
      demo: <ForbiddenStateDemo t={t} />,
    },
    {
      id: "stale",
      tone: "warn",
      icon: "clock",
      title: t("sm.stale"),
      desc: t("sm.staleDesc"),
      demo: <StatesStateDemo3 {...{ t }} />,
    },
    {
      id: "live",
      tone: "success",
      icon: "dot",
      title: t("sm.live"),
      desc: t("sm.liveDesc"),
      demo: <StatesStateDemo4 {...{}} />,
    },
  ];
}

export const StatesScreen = () => {
  const { t } = useI18n();
  const states = stateExamples(t);
  return <StatesSection {...{ t, states }} />;
};

function LoadingStateDemo() {
  return (
    <StateDemo>
      <div className={visual.column}>
        {[0.9, 0.7, 0.85, 0.6].map((width, index) => (
          <div
            key={index}
            className={visual.indicator}
            style={{ width: `${String(width * 100)}%`, animationDelay: `${String(index * 0.1)}s` }}
          />
        ))}
      </div>
    </StateDemo>
  );
}

function ForbiddenStateDemo({ t }: { t: (key: string, fallback?: string) => string }) {
  return (
    <StateDemo>
      <div className={visual.surface9}>
        <Icon name="lock" size={18} className={visual.surface10} />
        <div className={visual.label6}>{t("sm.demo.forbiddenTitle")}</div>
        <div className={visual.label7}>
          {t("sm.demo.forbiddenDesc")}{" "}
          <span className={`mono ${visual.surface11 ?? ""}`}>budget.write.expand</span>
          {t("sm.demo.forbiddenDesc2")}
        </div>
      </div>
    </StateDemo>
  );
}
