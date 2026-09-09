import { Breadcrumb } from "./Breadcrumb";
import { RunIdentity } from "./RunIdentity";
import { SourceControl } from "./SourceControl";
import styles from "./TopBar.module.css";
import { TopBarActions } from "./TopBarActions";
import { TopBarAppearance } from "./TopBarAppearance";
import type { TopBarProps } from "./topBarProps";

export type { TopBarProps };

/** Shared route header: source labeling replaces the prototype's misleading LIVE flag. */
export function TopBar(props: TopBarProps) {
  return (
    <header className={styles.topbar}>
      <Breadcrumb route={props.route} />
      <RunIdentity runId={props.runId} />
      <div className={styles.right}>
        <TopBarActions {...props} />
        <SourceControl />
        <TopBarAppearance {...props} />
      </div>
    </header>
  );
}
