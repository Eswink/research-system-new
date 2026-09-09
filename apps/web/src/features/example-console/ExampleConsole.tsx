import { Suspense } from "react";
import { ConsoleFrame } from "../../layout/ConsoleFrame";
import { ConsoleLoading } from "../../layout/ConsoleLoading";
import type { ConsoleProps } from "../../layout/consoleProps";
import { CommandCenterStage } from "./command-center/CommandCenterStage";
import styles from "./ExampleConsole.module.css";
import { ExamplePage } from "./ExamplePage";

/** The example subtree has no real API hooks, provider credentials or persistent business state. */
export function ExampleConsole(props: ConsoleProps) {
  const route = props.resolved.route;
  if (route.domain === "command-center")
    return (
      <Suspense fallback={<ConsoleLoading {...props} />}>
        <CommandCenterStage {...props} />
      </Suspense>
    );
  return (
    <ConsoleFrame {...props}>
      <section
        data-design-surface="example"
        data-source="example"
        data-testid={`example-page-${route.domain}-${route.page}`}
        className={styles.surface}
      >
        <ExamplePage route={route} />
      </section>
    </ConsoleFrame>
  );
}
