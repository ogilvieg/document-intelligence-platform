import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

const css = readFileSync("app/globals.css", "utf8");

function color(name: string) {
  return css.match(new RegExp(`--${name}:\\s*(#[0-9a-f]{6})`, "i"))?.[1] ?? "";
}

function luminance(hex: string) {
  const channels = [1, 3, 5].map((index) =>
    Number.parseInt(hex.slice(index, index + 2), 16) / 255,
  );
  const [red, green, blue] = channels.map((channel) =>
    channel <= 0.04045
      ? channel / 12.92
      : ((channel + 0.055) / 1.055) ** 2.4,
  );
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

function contrast(foreground: string, background: string) {
  const values = [luminance(foreground), luminance(background)].sort(
    (left, right) => right - left,
  );
  return (values[0] + 0.05) / (values[1] + 0.05);
}

describe("inclusive global styles", () => {
  it("provides shared focus treatment and full-size compact controls", () => {
    expect(css).toMatch(/:where\([^)]*button[^)]*input[^)]*\):focus-visible/);
    expect(css).toMatch(/\.compact-action\s*\{[^}]*min-height:\s*44px/);
    expect(css).toMatch(/\.compact-action\s*\{[^}]*min-width:\s*44px/);
    expect(css).toMatch(/\.analysis-choice-grid button\s*\{[^}]*min-height:\s*44px/);
  });

  it("keeps muted and disabled text at normal-text contrast", () => {
    expect(contrast(color("text-muted"), color("bg-elevated"))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(color("text-dim"), color("bg-surface"))).toBeGreaterThanOrEqual(4.5);
  });

  it("reduces all animations and transitions when requested", () => {
    expect(css).toMatch(/@media\s*\(prefers-reduced-motion:\s*reduce\)/);
    expect(css).toMatch(/animation-duration:\s*0\.01ms\s*!important/);
    expect(css).toMatch(/animation-iteration-count:\s*1\s*!important/);
    expect(css).toMatch(/transition-duration:\s*0\.01ms\s*!important/);
  });
});
