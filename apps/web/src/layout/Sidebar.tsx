import { cx } from "../components/cx";
import { useI18n } from "../i18n/useI18n";
import { DOMAIN_PAGES, routeToHash } from "../navigation/routes";
import styles from "./Sidebar.module.css";

const DOMAINS = ["plan", "run", "evidence", "assets", "govern"] as const;

type Domain = (typeof DOMAINS)[number];

const DOMAIN_KEY: Record<
  Domain,
  "domain.plan" | "domain.run" | "domain.evidence" | "domain.assets" | "domain.govern"
> = {
  plan: "domain.plan",
  run: "domain.run",
  evidence: "domain.evidence",
  assets: "domain.assets",
  govern: "domain.govern",
};

function pageKey(domain: Domain, page: string): `page.${Domain}.${string}` {
  return `page.${domain}.${page}`;
}

function NavItem({
  hash,
  label,
  active,
  testId,
  onNavigate,
}: {
  hash: string;
  label: string;
  active: boolean;
  testId: string;
  onNavigate: (hash: string) => void;
}) {
  return (
    <button
      type="button"
      className={cx(styles.item, active ? styles.active : null)}
      aria-current={active ? "page" : undefined}
      data-testid={testId}
      onClick={() => {
        onNavigate(hash);
      }}
    >
      {label}
    </button>
  );
}

/** 左侧信息域导航：只渲染真实可用页面（不为规划中功能造空页） */
export function Sidebar({
  route,
  onNavigate,
  onOpenSetup,
}: {
  route: string;
  onNavigate: (hash: string) => void;
  onOpenSetup: () => void;
}) {
  const { t } = useI18n();
  const active = route.replace(/^#\//, "");
  return (
    <nav className={styles.sidebar} aria-label="console navigation">
      {DOMAINS.map((domain) => (
        <div key={domain} className={styles.domain}>
          <div className={styles.domainLabel}>{t(DOMAIN_KEY[domain])}</div>
          {DOMAIN_PAGES[domain].map((page) => {
            const hash = routeToHash({ domain, page });
            const target = hash.slice(2);
            const label = t(pageKey(domain, page) as Parameters<typeof t>[0]);
            return (
              <NavItem
                key={page}
                hash={hash}
                label={label}
                active={active === target}
                testId={`nav-${domain}-${page}`}
                onNavigate={onNavigate}
              />
            );
          })}
        </div>
      ))}
      <div className={styles.footer}>
        <button
          type="button"
          className={styles.item}
          data-testid="nav-open-setup"
          onClick={onOpenSetup}
        >
          {t("app.openSetup")}
        </button>
      </div>
    </nav>
  );
}
