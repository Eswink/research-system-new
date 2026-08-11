import type { ResearchQuestion } from "../../domain/src/research-question.js";

export type ResearchRepository = Readonly<{
  save: (question: ResearchQuestion) => Promise<void>;
}>;
