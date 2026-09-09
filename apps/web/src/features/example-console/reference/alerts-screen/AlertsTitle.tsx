import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import { PageToolbar } from "../PageToolbar";
import { ViewSwitcher } from "../ViewSwitcher";

interface AlertsTitleProps {
  t: (key: string, fallback?: string) => string;
  tab: string;
  setTab: Dispatch<SetStateAction<string>>;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
}

export function AlertsTitle({ t, tab, setTab, setDrawer }: AlertsTitleProps) {
  return (
    <PageToolbar title={t("al.title")} subtitle={t("al.subtitle")}>
      <ViewSwitcher
        value={tab}
        onChange={setTab}
        views={[
          { value: "inbox", label: t("al.viewInbox"), icon: "menu" },
          { value: "rules", label: t("al.viewRules"), icon: "shield" },
          { value: "channels", label: t("al.viewChannels"), icon: "wifi" },
        ]}
      />
      <button
        className="btn primary sm"
        onClick={() => {
          setDrawer({ mode: "create-rule" });
        }}
      >
        <Icon name="plus" size={11} /> {t("al.new")}
      </button>
    </PageToolbar>
  );
}
