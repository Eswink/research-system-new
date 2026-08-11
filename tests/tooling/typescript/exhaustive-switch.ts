type FixtureState = Readonly<{ kind: "idle" }> | Readonly<{ kind: "running"; taskId: string }>;

const assertNever = (value: never): never => {
  throw new Error(`Unhandled fixture state: ${String(value)}`);
};

export const describeFixtureState = (state: FixtureState): string => {
  switch (state.kind) {
    case "idle":
      return "idle";
    case "running":
      return state.taskId;
    default:
      return assertNever(state);
  }
};
