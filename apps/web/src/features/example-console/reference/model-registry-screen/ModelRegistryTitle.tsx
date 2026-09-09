import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";
import visual from "../ModelRegistryScreen.module.css";
import { PageToolbar } from "../PageToolbar";
import { SearchInput } from "../SearchInput";
import { ModelRegistryRegister } from "./ModelRegistryRegister";
import { ModelRegistrySection2 } from "./ModelRegistrySection2";

interface ModelRegistryTitleProps {
  t: (key: string, fallback?: string) => string;
  q: string;
  setQ: Dispatch<SetStateAction<string>>;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  cols: string;
  filtered: FixtureTypes.RegisteredModel[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  selected: FixtureTypes.RegisteredModel | undefined;
  drawer: { mode?: string } | null;
}

export function ModelRegistryTitle({
  t,
  q,
  setQ,
  setDrawer,
  cols,
  filtered,
  selectedId,
  setSelectedId,
  selected,
  drawer,
}: ModelRegistryTitleProps) {
  return (
    <div className={visual.column}>
      <PageToolbar title={t("mr.title")} subtitle={t("mr.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("mr.search")} width={220} />
        <button
          className="btn primary sm"
          onClick={() => {
            setDrawer({});
          }}
        >
          <Icon name="plus" size={11} /> {t("mr.register")}
        </button>
      </PageToolbar>

      <ModelRegistrySection2 {...{ cols, t, filtered, selectedId, setSelectedId, selected }} />

      <ModelRegistryRegister {...{ drawer, setDrawer, t }} />
    </div>
  );
}
