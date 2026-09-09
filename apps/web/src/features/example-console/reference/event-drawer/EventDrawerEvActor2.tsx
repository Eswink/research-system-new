import FIX_ROLES from "../../data/roles.json";
import FIX_RUN from "../../data/run.json";
import type * as E from "../../exampleTypes";
import { DrawerSection } from "../DrawerSection";
import visual from "../EventDrawer.module.css";
import { KV } from "../kv";

interface EventDrawerEvActor2Props {
  t: (key: string, fallback?: string) => string;
  ev: E.Event;
  agent: E.Agent | null | undefined;
  model: E.Model | null | undefined;
}

export function EventDrawerEvActor2({ t, ev, agent, model }: EventDrawerEvActor2Props) {
  return (
    <div className={visual.grid}>
      <DrawerSection title={t("tl.evActor")}>
        <KV k="kind" v={ev.actor.kind} />
        {ev.actor.id && <KV k="id" v={ev.actor.id} />}
        {agent && <KV k="name" v={agent.name} />}
        {agent && <KV k="role" v={FIX_ROLES.find((r) => r.id === agent.role_id)?.name ?? "-"} />}
      </DrawerSection>
      <DrawerSection title={t("tl.evTaskScope")}>
        <KV k="scope" v={ev.scope} />
        {ev.task_id && <KV k="task_id" v={ev.task_id} />}
        <KV k="run_id" v={FIX_RUN.id.slice(0, 22)} />
      </DrawerSection>
      <DrawerSection title={model ? t("tl.evModel") : t("tl.evMetrics")}>
        {model ? (
          <>
            <KV k="model_id" v={model.model_id} />
            <KV k="returned" v={model.returned_model_name} warn={model.drift_alert !== undefined} />
            <KV
              k="fingerprint"
              v={model.system_fingerprint ?? "not provided"}
              unknown={!model.system_fingerprint}
            />
          </>
        ) : (
          <>
            {ev.cost_minor != null && <KV k="cost" v={`$${(ev.cost_minor / 100000).toFixed(4)}`} />}
            {ev.latency_ms != null && <KV k="latency" v={`${String(ev.latency_ms)}ms`} />}
            {ev.payload.artifact_id && <KV k="artifact" v={ev.payload.artifact_id} />}
          </>
        )}
      </DrawerSection>
    </div>
  );
}
