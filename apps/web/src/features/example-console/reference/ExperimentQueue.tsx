import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ExperimentQueueSection } from "./experiment-queue/ExperimentQueueSection";

export const ExperimentQueue = ({
  queue,
  selectedId,
  onSelect,
}: {
  queue: E.Experiment[];
  selectedId: string;
  onSelect: (id: string) => void;
}) => {
  const { t } = useI18n();
  return <ExperimentQueueSection {...{ t, queue, selectedId, onSelect }} />;
};
