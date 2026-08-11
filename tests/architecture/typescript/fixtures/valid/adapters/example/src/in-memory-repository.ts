import type { ResearchRepository } from "../../../packages/application/src/ports.js";

export const createInMemoryRepository = (): ResearchRepository => ({
  save: (): Promise<void> => Promise.resolve(),
});
