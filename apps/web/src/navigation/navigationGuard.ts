export const BEFORE_NAVIGATION = "console:before-navigation";
export const NAVIGATION_COMMITTED = "console:navigation-committed";

/** Client-side loss prevention only; not backend authorization or cancellation. */
export function requestNavigation(url: string): boolean {
  return window.dispatchEvent(
    new CustomEvent(BEFORE_NAVIGATION, { cancelable: true, detail: { url } }),
  );
}

export function commitNavigation(): void {
  window.dispatchEvent(new Event(NAVIGATION_COMMITTED));
}
