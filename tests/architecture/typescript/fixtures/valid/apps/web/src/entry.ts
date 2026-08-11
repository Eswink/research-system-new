import type { ResearchRepository } from "../../../packages/application/src/ports.js";
import {
  submitResearchQuestion,
  type SubmitResearchQuestionRequest,
} from "../../../packages/application/src/submit-research-question.js";

export const submitFromWebEntry = (
  repository: ResearchRepository,
  request: SubmitResearchQuestionRequest,
): Promise<void> => submitResearchQuestion(repository, request);
