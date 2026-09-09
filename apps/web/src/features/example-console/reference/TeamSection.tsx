import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { TeamSectionSecTeam } from "./team-section/TeamSectionSecTeam";

export const TeamSection = ({ value, setP }: E.ProtocolSectionProps) => {
  const { t } = useI18n();
  const templates = [
    { id: "LEAN", label: "LEAN", desc: t("pe.tm.leanDesc"), roles: 3 },
    { id: "STANDARD", label: "STANDARD", desc: t("pe.tm.stdDesc"), roles: 8 },
    { id: "RIGOROUS", label: "RIGOROUS", desc: t("pe.tm.rigDesc"), roles: 12 },
  ];
  const roleOptions = [
    "role_planner",
    "role_experimenter",
    "role_reviewer",
    "role_stats",
    "role_writer",
    "role_ethics",
    "role_qa",
    "role_ops",
  ];
  return <TeamSectionSecTeam {...{ t, templates, value, setP, roleOptions }} />;
};
