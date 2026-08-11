import { createInMemoryRepository } from "../../../adapters/example/src/in-memory-repository.js";
import {
  submitResearchQuestion,
  type SubmitResearchQuestionRequest,
} from "../../../packages/application/src/submit-research-question.js";

export const runResearchService = (request: SubmitResearchQuestionRequest): Promise<void> =>
  submitResearchQuestion(createInMemoryRepository(), request);
