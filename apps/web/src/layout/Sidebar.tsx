import { cx } from "../components/cx";
import { Icon } from "../components/Icon";
import { useI18n } from "../i18n/useI18n";
import { DOMAINS, routeToHash, type DomainId, type PageId } from "../navigation/registry";
import styles from "./Sidebar.module.css";
import { SidebarIdentity } from "./SidebarIdentity";
import { WorkspaceIdentity } from "./WorkspaceIdentity";

/** 域标签 i18n key。 */
function domainLabelKey(id: DomainId): string {
  return `dom.${id}`;
}

function pageLabelKey(domain: DomainId, page: PageId): string {
  return `page.${domain}.${page}`;
}

function DomainButton({
  id,
  icon,
  label,
  active,
  collapsed,
  onClick,
}: {
  id: DomainId;
  icon: Parameters<typeof Icon>[0]["name"];
  label: string;
  active: boolean;
  collapsed: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={cx(styles.domainBtn, active && styles.domainActive)}
      aria-current={active ? "page" : undefined}
      aria-label={label}
      title={label}
      data-testid={`nav-domain-${id}`}
      onClick={onClick}
      style={collapsed ? { justifyContent: "center", padding: 10 } : undefined}
    >
      <Icon name={icon} size={13} />
      {!collapsed && <span>{label}</span>}
    </button>
  );
}

function PageButton({
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
      className={cx(styles.pageBtn, active && styles.pageActive)}
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

/** 左侧八域导航：域展开子页；折叠态只显图标。 */
export interface SidebarProps {
  route: string;
  onNavigate: (hash: string) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  onOpenSettings: () => void;
}

export function Sidebar(props: SidebarProps) {
  const { route, onNavigate, collapsed, onToggleCollapse, onOpenSettings } = props;
  const { t } = useI18n();
  const active = route.replace(/^#\//, "");
  const activeDomain = active.split("/")[0];
  return (
    <nav className={styles.sidebar} aria-label="console navigation">
      <button
        type="button"
        className={styles.logo}
        onClick={onToggleCollapse}
        aria-label="toggle sidebar"
      >
        <span className={styles.logoMark}>◇</span>
        {!collapsed && (
          <span className={styles.logoText}>
            <span className={styles.logoName}>{t("app.name")}</span>
            <span className={styles.logoPlane}>{t("app.plane")}</span>
          </span>
        )}
      </button>
      {!collapsed && <WorkspaceIdentity />}
      <DomainList
        active={active}
        activeDomain={activeDomain}
        collapsed={collapsed}
        onNavigate={onNavigate}
      />
      <SidebarIdentity collapsed={collapsed} onOpen={onOpenSettings} />
    </nav>
  );
}

function DomainList({
  active,
  activeDomain,
  collapsed,
  onNavigate,
}: {
  active: string;
  activeDomain: string | undefined;
  collapsed: boolean;
  onNavigate: (hash: string) => void;
}) {
  const { t } = useI18n();
  return (
    <div className={styles.domains}>
      {DOMAINS.map((domain) => (
        <div key={domain.id}>
          <DomainButton
            id={domain.id}
            icon={domain.icon}
            label={t(domainLabelKey(domain.id) as Parameters<typeof t>[0])}
            active={activeDomain === domain.id}
            collapsed={collapsed}
            onClick={() => {
              const first = domain.pages[0];
              if (first !== undefined) {
                onNavigate(routeToHash({ domain: domain.id, page: first }));
              }
            }}
          />
          {activeDomain === domain.id && !collapsed && (
            <div className={styles.pages}>
              {domain.pages.map((page) => (
                <PageButton
                  key={page}
                  hash={routeToHash({ domain: domain.id, page })}
                  label={t(pageLabelKey(domain.id, page) as Parameters<typeof t>[0])}
                  active={active === `${domain.id}/${page}`}
                  testId={`nav-${domain.id}-${page}`}
                  onNavigate={onNavigate}
                />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
