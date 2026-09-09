import FIX_AGENTS from "../data/agents.json";
import FIX_MODELS from "../data/models.json";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { EventDrawerEvActor } from "./event-drawer/EventDrawerEvActor";
import { getEventTypeStyle } from "./getEventTypeStyle";

export const EventDrawer = ({ ev, onClose }: { ev: E.Event; onClose: () => void }) => {
  const { t } = useI18n();
  const typeStyle = getEventTypeStyle(ev.type);
  const agent = ev.actor.kind === "agent" ? FIX_AGENTS.find((a) => a.id === ev.actor.id) : null;
  const modelId = ev.payload.model_id ?? agent?.model_binding.model_id ?? agent?.resolved_model_id;
  const model = modelId ? FIX_MODELS.find((m) => m.id === modelId) : null;

  return <EventDrawerEvActor {...{ typeStyle, ev, onClose, t, agent, model }} />;
};
