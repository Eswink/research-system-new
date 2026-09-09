import visual from "./FooterBar.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const FooterBar = () => (
  <div className={visual.row}>
    <span className={visual.surface}>■</span>
    <span>SESSION</span> <span className={visual.surface2}>l.tanaka@research.io</span>
    <span className={visual.surface3}>│</span>
    <span>WORKSPACE</span> <span className={visual.surface4}>Research.io Lab</span>
    <span className={visual.surface5}>│</span>
    <span>REGION</span> <span className={visual.surface6}>ap-northeast-1</span>
    <span className={visual.surface7}>│</span>
    <span>MANIFEST</span> <span className={visual.surface8}>sha256:a9c4e21f</span>
    <span className={visual.surface9}>v3.14.2 · build 2026.08.27-a9c4e21f · uptime 42d 07:12</span>
  </div>
);
