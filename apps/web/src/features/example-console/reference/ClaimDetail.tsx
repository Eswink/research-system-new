import FIX_EVIDENCE from "../data/evidence.json";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ClaimDetailNeedEv } from "./claim-detail/ClaimDetailNeedEv";

export const ClaimDetail = ({ claim }: { claim: E.Claim }) => {
  const { t } = useI18n();
  const evidence = FIX_EVIDENCE.filter((e) => e.claim_id === claim.id);
  const supports = evidence.filter((e) => e.relation === "SUPPORTS");
  const refutes = evidence.filter((e) => e.relation === "REFUTES");
  const isProposed = claim.status === "PROPOSED";

  return <ClaimDetailNeedEv {...{ claim, isProposed, t, supports, refutes }} />;
};
