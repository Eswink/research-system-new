import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import { Drawer } from "../Drawer";
import { Icon } from "../Icon";
import { ReportForm } from "../ReportForm";
import visual from "../ReportsScreen.module.css";

interface ReportsDetailsDrawerProps {
  drawer: E.ReportDrawer | null;
  setDrawer: Dispatch<SetStateAction<E.ReportDrawer | null>>;
  t: (key: string, fallback?: string) => string;
}

export function ReportsDetailsDrawer({ drawer, setDrawer, t }: ReportsDetailsDrawerProps) {
  return (
    <Drawer
      open={!!drawer}
      onClose={() => {
        setDrawer(null);
      }}
      title={drawer?.mode === "create" ? t("rp.new") : t("rp.edit")}
      subtitle={drawer?.mode === "create" ? t("rp.newSub") : t("rp.editSub")}
      width={520}
      footer={
        <>
          <button
            className="btn ghost"
            onClick={() => {
              setDrawer(null);
            }}
          >
            {t("act.cancel")}
          </button>
          <button
            className={`btn primary ${visual.action ?? ""}`}
            onClick={() => {
              setDrawer(null);
            }}
          >
            <Icon name="check" size={11} />{" "}
            {drawer?.mode === "create" ? t("rp.createDraft") : t("act.save")}
          </button>
        </>
      }
    >
      <ReportForm report={drawer?.report} />
    </Drawer>
  );
}
