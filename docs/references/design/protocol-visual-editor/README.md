# Handoff: Protocol Visual Editor

## Overview

A visual, form-based editor for `protocol.yaml` — the canonical run manifest used
by the Research OS control plane's **Plan → Protocol & Dry Run** screen.
Researchers can now configure a run (objectives, evaluation grid, budget,
gates, policy) through structured form controls **without hand-editing YAML**,
while still being able to flip to the raw YAML view at any time.

The editor lives inside the existing `DryRunScreen` (screen 4 of the app),
replacing what used to be a read-only YAML source panel. The right-hand
Preflight Report is unchanged.

## About the Design Files

The files in this bundle are **design references created in HTML** — a
React-in-Babel-standalone prototype that renders the intended layout,
copy, states, and interactions. They are not production code to copy
directly.

The task is to **recreate this editor in the target codebase's existing
environment** (React + your styling stack, Vue, Svelte, etc.), using
already-established primitives (design tokens, form controls, icon set,
i18n keys). Treat the HTML as a spec, not a component to lift.

## Fidelity

**High-fidelity.** All colors reference existing CSS tokens
(`--accent`, `--warn`, `--danger`, `--fg-muted`, etc. — already defined in
`styles/tokens.css`). Typography, spacing, borders, and states are all
finalized. The design assumes the app's existing token system exists and
should be reused verbatim.

## Where It Fits

- Domain: **Plan** (sidebar)
- Tab: **Protocol & Dry Run**
- Position: **Left panel** of a two-column layout. Right panel is the
  existing Preflight Report.
- Container: rendered inside `<DryRunScreen>` and passed 5 props from the
  AppShell's global `tweaks` state:
  - `protocolMode` (`"form"` | `"yaml"`)
  - `protocolErrorLevel` (`"none"` | `"some"` | `"many"`) — demo hook for
    the validation stress test; wire to real validation in production
  - `protocolLanguages` (1–7) — demo hook
  - `protocolTemperatures` (1–6) — demo hook
  - `protocolAdminMode` (bool) — gates edits to `policy.*`

The screen's outer grid is
`grid-template-columns: minmax(480px, 1fr) minmax(460px, 1.1fr)` with
`gap: 16px`. The editor is the first grid child.

## Views

The editor is a single component with **one mode toggle** and **seven
form sections**. It also has three ambient banners that appear
conditionally.

### 0. Editor Chrome (always visible)

Horizontal bar, ~40px tall, at the top of the panel.

- **Left**: `book` icon (12px, `--fg-muted`) · `protocol.yaml` (13px, weight 500) · optional `DIRTY` pill when there are unsaved edits (mono 10px, `--warn` on `--warn-dim` bg, `--warn-line` border, 3px radius).
- **Right, in order**: Segmented Toggle (Form ↔ YAML), vertical rule 16px, `Templates ▾` ghost button, `Diff` icon button (`fork` icon), `Validate` icon button (`check` icon).
- Border-bottom: 1px `--border`.

The Segmented Toggle is a 2px-padded pill (`--bg-sunken` bg, `--border`
border, 6px radius). The active segment has `--bg-panel` background,
`--border-strong` border, `shadow-1`, font weight 500. Inactive is
transparent with `--fg-muted` text.

### 1. Dirty digest banner (only when local edits pending)

Full-width strip, `--warn-dim` background, `--warn-line` bottom border,
11px `--warn` text.

Copy (EN):
> ⚠ **Editing invalidates run reproducibility.** Applying will produce a
> new revision + digest. `37b2c9… → dirty`

Copy (ZH):
> ⚠ **编辑将使运行不可复现。** 应用后会生成新的版本与摘要。 `37b2c9… → dirty`

### 2. Error banner (only when validation errors exist)

Full-width strip, `--danger-dim` background, `--danger-line` bottom border.

- Collapsed row: `x` icon · **N errors block Apply** · "Resolve field-level errors below or fix in YAML." · right-aligned `Show all ▸` toggle.
- Expanded rows: one clickable outline button per error, showing `E-CODE · path.to.field · message`. Clicking jumps to the section and switches to Form mode.

### 3. Form mode body — two-column grid

`grid-template-columns: 148px minmax(0, 1fr)`

#### Left: Section Nav

- Container: `--bg-sunken` bg, `--border` right border, flex column.
- Header: 9px mono, `--fg-faint`, letter-spacing 0.1em, padding `10px 12px 6px`, text `Sections` / `区块`.
- Items: 7 buttons stacked, each `padding: 7px 12px`, `grid-template-columns: 12px 1fr auto` (icon · label · optional error badge).
  - Inactive: transparent bg, `--fg-muted` text, transparent left border.
  - Hover: `--bg-hover`.
  - Active: `--bg-panel` bg, 2px `--accent` left border, `--fg` text.
- Error badge: 14px pill, `--danger-dim` bg, `--danger-line` border, `--danger` text with the error count (mono 9px). Same shape in `--warn` tones when only warnings.
- Locked badge (Policy section): 9px `lock` icon in `--fg-faint`.
- Footer summary: `padding: 8px 12px`, mono 10px:
  - `errors    N` (green if 0, `--danger` if >0)
  - `warnings  N` (`--fg-faint` if 0, `--warn` if >0)

Sections, in order:
1. **Manifest** (`shield` icon)
2. **Objectives** (`flask` icon)
3. **Team** (`hex` icon)
4. **Evaluation** (`graph` icon)
5. **Budget** (`diamond` icon)
6. **Gates** (`circle-o` icon)
7. **Policy** (`lock` icon, locked when not admin)

#### Right: Section body

Scrollable, `padding: 16px 18px 80px` (bottom padding so content clears
the sticky action bar).

Every section starts with a `SectionHeader`:
- Title 15px weight 500, letter-spacing `-0.005em`.
- Subtitle 11px `--fg-muted`.
- Right-aligned `extra` slot (usually a chip: total count or computed value).
- Bottom border `1px --border-subtle`, `padding-bottom: 10px`, `margin-bottom: 16px`.

Every field is wrapped in a `Field`:
- Label row: 11px `--fg-muted` label · optional `q` icon tooltip trigger · optional `lock` icon.
- Control below.
- Error row (if any): 10px mono `--danger`, `x` icon + `E-CODE · message`.
- Hint row (if no error): 10px `--fg-faint`.

Tooltip on hover: 260px wide popover, `--bg-panel`, `--border-strong`,
`shadow-2`, 6px radius, `padding: 8px 10px`, 11px `--fg-muted`, positioned
6px above the trigger.

---

#### Section 1 · Manifest

- **Header extra**: chip `protocol_version 1.4` in accent tones.
- **Grid `minmax(0, 90px) 1fr`** for two locked fields:
  - `protocol_version` — read-only centered mono input, 60% opacity, cursor not-allowed. Tooltip: "Locked to platform runtime version. Contact ops to migrate."
  - `manifest.id` — read-only mono input + `copy` icon button on the right. Tooltip: "Assigned by the runtime at first save. Immutable."
- `manifest.name` — mono input, placeholder `lowercase-with-hyphens`. Validation: required, 3–64 chars, `^[a-z0-9-]+$`. On violation, input flips to `INPUT_ERR` (danger border + danger-dim bg).
- `manifest.autonomy_level` — 3 cards in a `1fr 1fr 1fr` grid:
  - `MANUAL` — success tones — "Every step requires human approval"
  - `GUARDED_AUTONOMOUS` — warn tones — "Runs autonomously between gates"
  - `AUTONOMOUS` — danger tones — "No pause · gates observed only"
  - Each card: `padding: 10px 12px`, 6px radius, mono 11px weight 500 code line, 10px `--fg-faint` description. Active state: `--{tone}-dim` bg + `--{tone}-line` border.

#### Section 2 · Objectives

- Header extra: chip showing `{count} · objectives`.
- One mini-card per objective:
  - Card wrapper: 8px radius, `--bg-raised` body, `--border`. Header strip inside `--bg-panel` with `flask` icon · `OBJECTIVE 01` mono label · right-aligned red `× Remove` button.
  - Body padding 12: `id` mono input, `statement` textarea (min 60px, resize vertical).
  - Statement < 10 chars produces a warning (yellow border on textarea, warning row below).
- Dashed "+ Add objective" button at the bottom, full width, `borderStyle: dashed`.
  - Clicking pushes `{ id: 'obj_' + random5, statement: '' }`.

#### Section 3 · Team

- `team.template` — 3 cards `1fr 1fr 1fr`, similar to autonomy cards:
  - `LEAN` · "Solo · fast iteration" · 3 roles
  - `STANDARD` · "Balanced · heterogeneous review" · 8 roles
  - `RIGOROUS` · "Peer-review grade · ethics" · 12 roles
  - Active: accent tones.
- `team.overrides` — mini table:
  - Header row: 9px mono `--fg-faint`, columns `role | instances | collapse_when | (delete)`.
  - Body: `--bg-sunken` bg, `--border`, 6px radius. Rows have `grid-template-columns: 1.4fr 0.6fr 1.6fr 24px`, gap 8, `padding: 6px 8px`.
  - Role: mono select (`role_planner … role_ops` — 8 predefined).
  - Instances: mono number input (nullable → shows `—`).
  - Collapse_when: mono text input, placeholder `condition expression …`.
  - Delete: 22px ghost button, `x` icon in `--danger`.
- Dashed `+ Add override` full-width button below the table.

#### Section 4 · Evaluation

- Header extra: mono chip showing computed `n = languages × n_per_lang × temperature_grid.length`.
- **`evaluation.benchmarks`** — `ChipMultiSelect`:
  - Selected chips: 22px pill, `--bg-raised`, `--border-strong`, 4px radius, 11px mono, followed by an `x` remove.
  - Input row: mono text field `+ custom · Enter` + right-aligned `+N ▾` suggested-pool trigger (opens a floating list of unpicked items from `AVAILABLE_BENCHMARKS` — `medhalt-v2`, `internal.dosage_probe.v3`, `medqa-usmle`, `pubmedqa`, `medmcqa`, `medhalt-v1`).
- **`evaluation.languages`** — chip multi-select with dual pool:
  - Selected: colored accent chip, 24px, `--accent-dim` bg, `--accent-line` border, contains mono ISO code + native label + `×`.
  - Available (dashed pool): 22px, `border: 1px dashed --border-strong`, transparent bg, `--fg-muted`. Clicking moves it to selected.
  - Language pool: `en`, `es`, `zh`, `ar`, `pt`, `fr`, `ja`, `de`, `hi`, `ru` with native labels (English, Español, 中文, العربية, Português, Français, 日本語, Deutsch, हिन्दी, Русский).
  - Hint: `{selected} selected · {available} available`.
- **`evaluation.n_per_lang`** — stepper: `−50` button · 96px mono number input (centered) · `+50` button · trailing mono hint `× {langs} = {total} samples`. Wraps if narrow.
  - Validation: `< 30` → hard error `E-E001` (blocks Apply). `< 100` → warning `W-E002`.
- **`evaluation.temperature_grid`** — custom control:
  - Rectangular slot 44px tall, `--bg-sunken`, `--border`, 6px radius. Baseline line at 50%, 5 tick lines at 0/0.25/0.5/0.75/1.0. Each sampled value is drawn as a 14px blue dot with a 2px `--bg-panel` inner ring and `--accent-line` halo. Value labels 0.00–1.00 in mono 9px `--fg-faint` below the slot.
  - Below: chip list of current values (accent chip with `×`), plus an inline number input (60px, mono, step 0.05, min 0, max 1) and an `+ add` button.

#### Section 5 · Budget

- **`budget.cap_minor`** — mono number input · trailing text `= $X.XX` · smart apply button. Comparison logic on the draft:
  - Equal to saved: shows a green `✓ saved` chip.
  - Different: green `✓ apply` button.
  - Higher than saved (upgrade): switches to two-step confirmation. First click shows `⚠ Confirm raise` in warn tones, second click shows `✓ Confirmed · apply` primary button.
  - Hint below: `≈ $X.XX USD · minor units, 1/100000 USD`.
- **`budget.hard_stop_on_breach`** — pair of mono toggle buttons:
  - `✓ HARD_STOP` — active in success tones.
  - `⊘ SOFT_WARN` — active in danger tones. When SOFT_WARN is active, a warning `W-B002` message appears: "hard_stop_on_breach is OFF — run may exceed cap silently."
- **`budget.reservations`** — two-column layout `1fr 130px`:
  - Left: table (`--bg-sunken`, 6px radius). Header chip beside label shows `Σ $USED / $CAP` in green (equal), muted (< cap), or danger (> cap). Rows: 3px color swatch · resource mono select (full width, wraps to fit) · 90px mono number input right-aligned · % text · 20px red `×` button. Bottom-edge dashed `+ Add reservation` button, `borderTop: 1px --border-subtle`.
  - Right: 88×88 SVG donut with per-reservation arcs colored by index (palette: accent, unknown-purple, warn, success, danger, teal). Center caption: percent-of-cap allocated (in danger red if over).
- **Resource pool** (predefined): `llm_tokens`, `gpu_a100_hr`, `gpu_h100_hr`, `external_tools`, `embedding_local`, `storage_gb_mo`.

#### Section 6 · Gates

- Header extra: `{count} · gates`.
- Each gate is a card, `padding: 10px 12px`, `--bg-raised`, `--border`, 6px radius.
  - Top row grid `minmax(0, 160px) minmax(0, 1fr) 20px`:
    - Kind select (mono, weight 500, tone-colored per kind — see mapping) — options: `BUDGET_GATE`, `QUALITY_GATE`, `PUBLISH_GATE`, `SECURITY_GATE`, `ETHICS_GATE`.
    - Trigger condition mono input, placeholder `trigger condition …`.
    - 20px red `×` button.
  - Below: 10px `--fg-faint` hint line, changes per gate kind:
    - `BUDGET_GATE` → "Trigger: fraction-of-cap threshold, e.g. '60% of cap'"
    - `QUALITY_GATE` → "Trigger: checkpoint expression, e.g. 'after each language subset'"
    - `PUBLISH_GATE` → "Trigger: deliverable state, e.g. 'deliverable finalized'"
    - `SECURITY_GATE` → "Trigger: any external write, e.g. 'any external artifact publish'"
    - `ETHICS_GATE` → "Trigger: sensitive content detection"
- Kind → tone mapping (affects select background/border/text color):
  - `BUDGET_GATE` → warn
  - `QUALITY_GATE` → accent
  - `PUBLISH_GATE` → unknown (purple)
  - `SECURITY_GATE` → danger
  - `ETHICS_GATE` → danger
- Full-width dashed `+ Add gate` at the bottom.
- Validation:
  - `BUDGET_GATE` missing → error `E-G001`.
  - `PUBLISH_GATE` missing → warning `W-G001`.

#### Section 7 · Policy (admin-gated)

- Header extra: mono chip `🛡 ADMIN` (success tones when admin on) or `🛡 READ-ONLY` (warn tones when admin off).
- If admin is off: full-width warn callout banner just below the header:
  > 🔒 **Admin permissions required.** Changes to `policy.*` rewrite governance. Toggle 'Admin mode' in the Tweaks panel to demo.
  - `padding: 10px 12px`, `--warn-dim` bg, `--warn-line` border, 6px radius, 11px `--warn`.
- All controls are rendered but disabled + 55% opacity + `cursor: not-allowed` when admin is off.
- **`policy.heterogeneous_review`** — 3-segment control `relaxed | standard | strict` (all mono).
- **`policy.memory_write`** — 3-segment control `open | gated_by_provenance | disabled` (all mono).
- **`policy.redact_prompts`** — pair of buttons `✓ true` / `⊘ false`, similar to hard_stop_on_breach, but in accent tones.

### 4. YAML mode body

When the segmented toggle is on `YAML`, the entire section body is
replaced by a scrollable YAML viewer (currently read-only in the
prototype). Rendering rules:

- Container: `flex: 1`, `overflow: auto`, `padding: 12px`, `--bg-sunken` bg.
- `<pre>` mono 12px, line-height 1.65, `--fg-muted`.
- Each line rendered as `{gutter} {content}`:
  - Gutter: 26px, right-aligned, mono, `--fg-faint` at 50% opacity, no select.
  - Content: minimal syntax highlight. Keys before `:` are colored `--accent`; values `--fg`; `#comments` italic `--fg-faint`.

The YAML text is regenerated from state via a `serialize(protocol)`
function on every render. In a production build, prefer a proper YAML
library (js-yaml) so round-tripping preserves user comments and
formatting when the toggle switches back to Form.

### 5. Template picker (dropdown)

Appears between the chrome and the body when the user clicks `Templates`.

- `--bg-raised` container, `--border` bottom border.
- Header strip 6px 12px, 10px mono `--fg-faint`, letterspaced uppercase text `Copy from preset` + close `×`.
- 2×2 grid of preset cards, gap 6px, padding 8px:
  - **Prior study · Med QA** — book icon — "Reuse last month's Med QA baseline · same budget shape"
  - **STAT-heavy** — shield icon — "STANDARD + adversarial reviewers + ethics gate"
  - **Minimal exploratory** — flask icon — "Single language · no QUALITY_GATE · fast"
  - **Reset to canonical** — ban icon — "1.4 canonical shape · discards local edits"
- Each card: 6px radius, `--bg-panel` bg, `--border`, hover `→ --accent-line` border.
- Only "Reset" is fully wired in the prototype (resets to defaults). Others should call a template-loading endpoint in production.

### 6. Action bar (sticky bottom)

Full-width footer, `--bg-raised` bg, `1px --border` top border,
`padding: 8px 12px`.

- **Left** — status chip:
  - No changes: green `✓ No unsaved changes`.
  - Dirty, has errors: `--danger` `× N errors to resolve`.
  - Dirty, only warnings: `--warn` `⚠ N warnings · Apply allowed`.
  - Dirty, clean: `--accent` `• Unsaved changes`.
- **Right** — action group:
  - `Discard` ghost button — disabled when not dirty; reverts state to last committed.
  - `Apply` primary button (`✓ Apply`) — disabled unless dirty AND no errors. Tooltip on disabled: reason (errors vs no changes).

---

## Interactions & Behavior

### Mode toggle (Form ↔ YAML)

- Clicking a segment updates local state; both segments remain interactive.
- Switching modes preserves the current protocol state (no re-parse).
- Prop `mode` from parent seeds initial mode; local `useEffect` syncs when
  parent changes it (from the Tweaks panel default-mode radio).

### Section navigation

- Clicking a nav item sets active section; body scrolls back to top.
- Clicking an error in the error banner: switches to Form mode and
  activates the affected section.
- Sections are visually independent — no cross-section anchors or
  keyboard focus grouping.

### Field-level validation

- All validation is derived state via `useMemo` — recomputed on any
  protocol change.
- `validate(protocol, adminMode, errorLevel)` returns `{ errors, warnings }`
  arrays. Every entry has `{ path, section, severity, code, message }`.
- Errors block Apply. Warnings do not.
- The `errorLevel` prop is a demo-time hook — it injects synthetic
  errors to preview the "many errors" state. Remove in production.

Real validation rules already implemented:
| Path | Rule | Code | Severity |
|---|---|---|---|
| `manifest.name` | Required, ≥ 3 chars | E-M001 | error |
| `manifest.name` | `^[a-z0-9-]+$` | E-M002 | error |
| `objectives` | ≥ 1 required | E-O001 | error |
| `objectives[i].id` | Required | E-O002 | error |
| `objectives[i].statement` | ≥ 10 chars recommended | W-O001 | warning |
| `evaluation.languages` | ≥ 2 if QUALITY_GATE present | W-E001 | warning |
| `evaluation.n_per_lang` | ≥ 30 | E-E001 | error |
| `evaluation.n_per_lang` | ≥ 100 recommended | W-E002 | warning |
| `evaluation.temperature_grid` | Non-empty | W-E003 | warning |
| `budget.reservations` sum | ≤ cap | E-B001 | error |
| `budget.reservations` sum | ≥ 50% of cap | W-B001 | warning |
| `budget.hard_stop_on_breach` | Should be true | W-B002 | warning |
| `gates` | Must contain BUDGET_GATE | E-G001 | error |
| `gates` | Should contain PUBLISH_GATE | W-G001 | warning |

### Apply / Discard

- The editor maintains **two protocol snapshots**: `protocol` (working
  draft) and `committed` (last successful Apply).
- `dirty = JSON.stringify(protocol) !== JSON.stringify(committed)`.
- `Apply` copies working → committed. In production this should also
  POST the new revision to the runtime and receive a new digest.
- `Discard` copies committed → working. No confirmation modal is shown;
  the primary safety net is that Discard is disabled when not dirty.
- The dirty digest banner shows only when `dirty === true`. The
  digest transition text (`37b2c9… → dirty`) is currently hardcoded —
  wire to the real committed digest in production.

### Admin gating

- The Policy section is always visible in the nav (with a lock icon),
  but its controls are disabled when `adminMode === false`.
- In production, resolve `adminMode` from the current user's roles
  server-side. The demo prop is a Tweak toggle for previewing both
  states.

### Budget cap two-step confirm

- If the user increases `cap_minor` above committed, the apply button
  becomes a warn-tone `⚠ Confirm raise`.
- After clicking once, it becomes a primary `✓ Confirmed · apply`.
- Reducing the cap or entering the same value skips the confirmation.
- Rationale: prevent accidental budget expansions; downgrades are safe.

### Tweaks integration

The AppShell exposes a "Protocol Editor" section in the Tweaks panel:
- `Default mode` radio (Form | YAML) → `protocolMode`
- `Validation errors` radio (None | Some | Many) → `protocolErrorLevel`
- `Languages` slider (1–7) → `protocolLanguages`
- `Temperatures` slider (1–6) → `protocolTemperatures`
- `Admin mode` toggle → `protocolAdminMode`

These are demo tools only. In production the editor should read the
real protocol from a data source and validate against real rules.

## State Management

### Local state (owned by ProtocolEditor)

```ts
protocol: Protocol            // working draft (all edits go here)
committed: Protocol           // last-applied snapshot
mode: 'form' | 'yaml'
activeSection: 'manifest' | 'objectives' | 'team' | 'evaluation'
              | 'budget' | 'gates' | 'policy'
templateOpen: boolean         // template dropdown visibility
```

### Derived (useMemo)

```ts
{ errors, warnings } = validate(protocol, adminMode, errorLevel)
errorsBySection: { [section]: { errors: number, warnings: number } }
dirty: boolean
canApply: errors.length === 0 && dirty
yamlText: string = serialize(protocol)
```

### Shape of `Protocol`

```ts
type Protocol = {
  protocol_version: string;                 // locked
  manifest: {
    id: string;                             // locked
    name: string;
    autonomy_level: 'MANUAL' | 'GUARDED_AUTONOMOUS' | 'AUTONOMOUS';
  };
  objectives: Array<{ id: string; statement: string }>;
  team: {
    template: 'LEAN' | 'STANDARD' | 'RIGOROUS';
    overrides: Array<{
      role: string;                         // enum, see roleOptions
      instances: number | null;
      collapse_when: string;                // condition expression
    }>;
  };
  evaluation: {
    benchmarks: string[];                   // freeform + suggestions
    languages: string[];                    // ISO 639-1
    n_per_lang: number;
    temperature_grid: number[];             // 0..1
  };
  budget: {
    cap_minor: number;                      // 1 USD = 100_000 minor units
    hard_stop_on_breach: boolean;
    reservations: Array<{ resource: string; minor: number }>;
  };
  gates: Array<{
    kind: 'BUDGET_GATE' | 'QUALITY_GATE' | 'PUBLISH_GATE'
        | 'SECURITY_GATE' | 'ETHICS_GATE';
    at: string;                             // trigger expression
  }>;
  policy: {
    heterogeneous_review: 'relaxed' | 'standard' | 'strict';
    memory_write: 'open' | 'gated_by_provenance' | 'disabled';
    redact_prompts: boolean;
  };
};
```

### Data fetching (production wiring)

- Read initial protocol from the runtime for the current run.
- On Apply: POST the new protocol to the runtime; receive `{ revision, digest }`.
- On template pick: fetch the preset from the runtime's template catalog.
- Preflight report (right panel) is orthogonal; it recomputes on
  committed changes.

## Design Tokens

The design uses **exactly** the tokens already in `styles/tokens.css`.
Do not invent new colors. Full reference:

### Colors (dark, from `:root`)

| Token | Value | Use |
|---|---|---|
| `--bg-app` | #0B0D10 | Page background |
| `--bg-panel` | #12151A | Card / panel |
| `--bg-raised` | #171B21 | Nested card, button |
| `--bg-hover` | #1E242C | Row hover |
| `--bg-sunken` | #0E1114 | Input, YAML background |
| `--border` | #232A33 | Default border |
| `--border-strong` | #2E3742 | Hover / active border |
| `--border-subtle` | #1A2028 | Row separator |
| `--fg` | #E6EAF0 | Body text |
| `--fg-muted` | #9AA6B4 | Label / secondary |
| `--fg-faint` | #6B7684 | Hint / tertiary |
| `--accent` | #4C8DFF | Primary action, QUALITY tone |
| `--success` | #35A56F | OK state, MANUAL tone |
| `--warn` | #D9962A | Warning, BUDGET / GUARDED tone |
| `--danger` | #E0524C | Error, SECURITY / AUTONOMOUS tone |
| `--unknown` | #8B7BD8 | Unknown / PUBLISH tone |

Each tone also has `-dim` (background at ~0.14 alpha) and `-line`
(border at ~0.32 alpha) variants.

Light-theme values are in `styles/tokens.css`.

### Typography

- Sans: `IBM Plex Sans`, `PingFang SC`, `Microsoft YaHei`, system stack
- Mono: `JetBrains Mono`, `IBM Plex Mono`, `ui-monospace`
- Sizes: `--fs-caption 11px` · `--fs-meta 12px` · `--fs-body 13px` ·
  `--fs-title-sm 15px` · `--fs-title 18px` · `--fs-title-lg 22px`
- Line-height: `--lh-body 1.6` · `--lh-tight 1.35`

### Spacing scale

`--sp-1 4px` · `--sp-2 8px` · `--sp-3 12px` · `--sp-4 16px` ·
`--sp-5 24px` · `--sp-6 32px` · `--sp-7 48px`

### Radii

- `--r-chip 4px` — pill / chip
- `--r-ctrl 6px` — button / input
- `--r-card 8px` — objective card, mini-card
- `--r-panel 12px` — top-level panel

### Motion

- `--motion-fast 120ms cubic-bezier(0.2, 0, 0, 1)` — hover, chip toggles
- `--motion 180ms …` — default
- `--motion-slow 240ms …` — panel show/hide

Focus ring: `0 0 0 2px var(--bg-app), 0 0 0 4px var(--accent)`.

## Icons

All icons are 12px inline SVG using `currentColor`, from `components/atoms.jsx`.
The editor uses: `book`, `check`, `x`, `warn-tri`, `hex`, `diamond`,
`circle-o`, `dot`, `q`, `play`, `plus`, `lock`, `ban`, `shield`, `flask`,
`graph`, `menu`, `copy`, `chevron-r`, `chevron-d`, `external`, `fork`, `spin`.

Two custom mini-icons live inside `ProtocolEditor.parts.jsx` (`PECustomIcon`):
- `edit` (pencil) — used only in the segmented toggle Form label
- `code` (`<` `>` chevrons) — used only in the segmented toggle YAML label

## Interactions checklist

- [x] Form/YAML toggle preserves state
- [x] Section nav badges reflect current validation
- [x] Field-level red-border + inline error
- [x] Top error banner with expandable jump-to list
- [x] Dirty digest banner
- [x] Discard reverts, Apply commits, both dependent on `dirty` + `errors`
- [x] Budget cap raise requires two-click confirm
- [x] Policy locked when not admin (visual + interaction disabled)
- [x] Language chips can be added from a pool or removed
- [x] Temperature grid: visual sample slot + add/remove chips
- [x] Reservations table + donut summarizer + Σ chip
- [x] Gate kind color-toned select with per-kind hint
- [x] Templates dropdown (Reset is functional, others are stubs)
- [ ] Diff button opens a diff drawer — **not implemented**, spec only
- [ ] Real Validate button call — **stub**, wire to backend

## Files

The design lives in `App.html` and these JSX modules:

| File | Role |
|---|---|
| `App.html` | Entry HTML — loads all scripts, mounts `<AppShell/>` |
| `styles/tokens.css` | Design tokens (colors, type, spacing, radii, motion) |
| `screens/DryRun.jsx` | Screen 4 shell — hosts `<ProtocolEditor/>` on the left, Preflight Report on the right |
| `screens/ProtocolEditor.jsx` | Editor main: state, validate, serialize, section routing |
| `screens/ProtocolEditor.parts.jsx` | Chrome, banners, nav, action bar, template picker, YAML view, `Field` primitive |
| `screens/ProtocolEditor.sections.jsx` | 7 section forms + ChipMultiSelect, TemperatureGrid, BudgetDonut, SegmentedField |
| `components/AppShell.jsx` | Adds `protocol*` tweaks to global tweaks + wires props into DryRunScreen |
| `components/i18n.jsx` | Adds `pe.*` and `tw.pe.*` strings for EN and zh-CN |
| `components/atoms.jsx` | `<Icon>` and shared atomic primitives |
| `tweaks_panel.jsx` | Tweak controls (TweakRadio, TweakSlider, TweakToggle, etc.) |

## Assets

No new binary assets. All visuals are inline SVG (icons) or CSS-derived
shapes (donut chart, temperature slot). Fonts are loaded from Google
Fonts CDN: IBM Plex Sans + JetBrains Mono.

## Recreation checklist for the target codebase

1. **Reuse the existing design tokens.** Match every color/spacing/radius to what's in `tokens.css`. If the target already has a token system, map by role (accent, warn, danger, muted, etc.), not by hex.
2. **Bind local component state.** Editor state is entirely local (`useState`) — no Redux/global store needed. Parent passes 5 configuration props; editor is otherwise self-contained.
3. **Wire up the real data source.** Replace `DEFAULT_PROTOCOL` with a fetch from the runtime; replace `serialize` with a real YAML library (js-yaml). Replace the client-side `validate` with server-authoritative validation if available.
4. **Implement the Diff drawer.** The button exists but has no action. Follow the same panel-slide pattern used elsewhere in the app.
5. **Wire the Templates dropdown to a real preset endpoint.** In the prototype only "Reset" is functional.
6. **Keyboard accessibility.**
   - Section nav should be a `<nav role="navigation">` with arrow-key traversal.
   - Every input already benefits from the global `:focus-visible` ring; verify tab order.
   - Segmented controls should be `role="radiogroup"` with `role="radio"` children.
7. **Persist mode preference.** In the prototype `mode` is transient; consider writing it to localStorage under `ros.protocol.mode` (mirroring other persisted UI state).
8. **i18n.** All strings live under the `pe.*` and `tw.pe.*` prefixes. Both English and Simplified Chinese are supplied — extend the same pattern for additional locales.
