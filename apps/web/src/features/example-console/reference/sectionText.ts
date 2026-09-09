/** Reference: screens/Reports.jsx; EXAMPLE ONLY. */
export const sectionText = (id: string) => {
  const T: Record<string, string> = {
    abstract: [
      "We evaluated hallucination rates of five frontier LLMs on multilingual ",
      "medical dosage question-answering across seven languages (n=8,400). ",
      "Across our benchmark, Spanish and Chinese elicited substantially higher ",
      "hallucination rates than English (12.3% and 8.7% vs 4.1% respectively, ",
      "χ²=27.4, p<0.001). Claude Opus 4.1 showed the lowest cross-lingual ",
      "variance (σ=0.031); however, the Arabic subset (n=48) is underpowered ",
      "and this finding is currently disputed. Chain-of-thought prompting, ",
      "contrary to expectations, did not reduce hallucination — instead it ",
      "inflated model confidence without accuracy gains.",
    ].join(""),
    intro: [
      "1. Introduction. Large language models are increasingly deployed as ",
      "clinical decision support, yet their reliability under multilingual ",
      "medical queries remains poorly characterized. Prior work has focused ",
      "predominantly on English benchmarks (MedQA, MedMCQA). We ask whether the ",
      "frontier hallucination behavior observed on English generalizes across ",
      "the seven WHO-priority languages …",
    ].join(""),
    methods: [
      "2. Methods. We assembled a corpus of 8,420 dosage-QA pairs from the WHO ",
      "Dosage Guidelines (2024) and PubMed abstracts (2023). Each query was ",
      "translated by native-speaker clinicians and cross-verified. Five models ",
      "(GPT-4o, Claude Sonnet 4, Claude Opus 4.1, Gemini 2.5 Pro, Qwen3-235B) ",
      "were queried under a fixed protocol …",
    ].join(""),
    results: [
      "3. Results. Table 1 reports hallucination rates by (model × language). ",
      "Across the pooled sample (n=8,400), Spanish showed the highest ",
      "hallucination rate (12.3%, 95% CI [11.1, 13.6]). Chinese generic-name ",
      "substitution errors occurred at 2.8× the English baseline. Model-wise, ",
      "Claude Opus 4.1 was most stable across languages (σ=0.031) but the ",
      "Arabic subset was too small (n=48) for statistical conclusions and this ",
      "claim is currently under review …",
    ].join(""),
  };
  return T[id] ?? "";
};
