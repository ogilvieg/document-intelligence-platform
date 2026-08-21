# Issue 9 Accessibility Verification

Date: 2026-08-21
Branch: `codex/issue-9-responsive-accessible`

## Contrast measurements

Ratios use WCAG relative luminance calculations against the solid design-token
backgrounds. Normal text must reach 4.5:1; large text, focus indicators, and UI
graphics must reach 3:1.

The initial `--text-muted: #7a6e62` measured 3.75:1 on `--bg-elevated` and
4.13:1 on `--bg-surface`. Initial `--text-dim: #b0a090` measured 2.31:1 on
`--bg-base` and 2.11:1 on `--bg-surface`; these failed the normal-text target.

Adjusted token evidence:

| Foreground | Background | Ratio |
| --- | --- | ---: |
| `--text-muted` `#6b6055` | `--bg-base` `#f9f4e8` | 5.58:1 |
| `--text-muted` `#6b6055` | `--bg-surface` `#f2ead3` | 5.10:1 |
| `--text-muted` `#6b6055` | `--bg-elevated` `#e9dfca` | 4.63:1 |
| `--text-dim` `#74685e` | `--bg-base` `#f9f4e8` | 4.93:1 |
| `--text-dim` `#74685e` | `--bg-surface` `#f2ead3` | 4.50:1 |
| `--cyan` focus `#2b5ea7` | `--bg-base` `#f9f4e8` | 5.87:1 |
| `--cyan` focus `#2b5ea7` | `--bg-surface` `#f2ead3` | 5.36:1 |

The automated stylesheet test guards the lowest muted/elevated and
dim/surface text pairs at 4.5:1. Rendered focus, target, viewport, and motion
checks will be appended during tasks T012-T013.

## Source validation

- `npm test`: 12 files and 59 tests passed.
- `./node_modules/.bin/tsc --noEmit --incremental false`: passed.
- `npm run build`: passed with all eight Next routes generated.
- `npm run lint`: remains at the documented `main` baseline of eight errors
  and one warning. The findings are the pre-existing effect-state rule in
  `app/page.tsx`, seven `no-explicit-any` findings in API clients, and the
  pre-existing unused `formatLatency` warning; issue #9 introduced no finding.

## Responsive empty-state evidence

The browser scrollbar occupies three CSS pixels, so the measured document
client widths are three pixels below the requested viewport widths. Every
state satisfies `scrollWidth === clientWidth`.

| Requested viewport | Client width | Scroll width | Screenshot |
| ---: | ---: | ---: | --- |
| 320 | 317 | 317 | `issue-9-screenshots/empty-320.png` |
| 390 | 387 | 387 | `issue-9-screenshots/empty-390.png` |
| 768 | 765 | 765 | `issue-9-screenshots/empty-768.png` |
| 1440 | 1437 | 1437 | `issue-9-screenshots/empty-1440.png` |

Visual inspection confirms the header stacks at mobile widths, the explainer
uses readable rows at 320/390, upload disclosures and the native chooser stay
within the page, and the footer wraps. At 768 and 1440 the explainer retains
three readable columns and the content shell remains bounded.

The local API was unavailable during browser QA, so the synthetic populated
state returned its accessible temporary-unavailable alert. Indexed and result
layout/heading/interaction states remain covered by the focused component
fixtures; no populated-state screenshot is claimed.

## Focus and target evidence

At 390 px, browser-computed focus checks found a solid 3 px `#2b5ea7`
outline on retry, introduction-dismiss, sample, upload-requirements-dismiss,
native file input, and project-resource link controls. All sampled buttons and
the native file input measured at least 44 px high; compact dismiss buttons
measured 44 by 44 px. Project-resource links are the documented inline-text
target-size exception and retain a visible 3 px focus outline.

The browser automation surface could focus the native chooser but did not
surface its operating-system picker from synthesized Enter or Space presses.
The component test verifies focus and file selection; a final human keyboard
picker check remains in T013. The browser surface also does not expose media
preference emulation, so reduced-motion behavior is guarded by the stylesheet
contract and awaits the same final pass.
