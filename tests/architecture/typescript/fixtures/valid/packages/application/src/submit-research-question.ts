import type { ResearchQuestion } from "../../domain/src/research-question.js";
import type { ResearchRepository } from "./ports.js";

export type SubmitResearchQuestionRequest = Readonly<{
  id: string;
  prompt: string;
}>;

const toResearchQuestion = (request: SubmitResearchQuestionRequest): ResearchQuestion => request;

export const submitResearchQuestion = (
  repository: ResearchRepository,
  request: SubmitResearchQuestionRequest,
): Promise<void> => repository.save(toResearchQuestion(request));
