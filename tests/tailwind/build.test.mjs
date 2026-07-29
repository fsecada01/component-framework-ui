/**
 * The vendored plugin, run through a real Tailwind build.
 *
 * `tests/js/plugin.test.mjs` calls the plugin's exports directly. That suite is
 * fast and it is where the logic is covered, but every claim it makes about
 * *Tailwind* is a proxy. The clearest example is the marker that lets the
 * CSS-first path pass options:
 *
 *     assert.equal(cfUiAxes.__isOptionsFunction, true);
 *
 * That asserts cf-ui still sets a flag. It does not assert Tailwind still reads
 * it. Both defects fixed in #7 were invisible to a 35-test suite and only
 * surfaced under a real build — one of them meaning a CSS-first consumer could
 * not pass a composition at all, so the plugin validated only the default
 * composition, which always passes. The feature was inert while looking fine.
 *
 * So this file spawns the actual CLI and reads the actual exit code. It never
 * skips: a missing toolchain throws, because a skipped check reads as a pass
 * and that is the failure mode this whole file exists to close.
 *
 * Requires `npm ci` in this directory. The Tailwind version is pinned in
 * package.json — when a bump breaks this, that is the signal, not noise.
 */

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { after, describe, it } from "node:test";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const FIXTURES = join(HERE, "fixtures");
const CLI_DIR = join(HERE, "node_modules", "@tailwindcss", "cli");

const DEFINITION = JSON.parse(
  readFileSync(
    fileURLToPath(new URL("../../src/cf_ui/static/cf_ui/cf_ui_axes.json", import.meta.url)),
    "utf-8",
  ),
);

/**
 * Path to the CLI's entry script.
 *
 * Spawned through `process.execPath` rather than the `.bin` shim so the same
 * call works on Windows, where the shim is a `.cmd` and needs a shell.
 */
function cliEntry() {
  const manifest = join(CLI_DIR, "package.json");
  if (!existsSync(manifest)) {
    throw new Error(
      "Tailwind is not installed for this check. Run `npm ci` in tests/tailwind " +
        "(or `just test-tailwind`, which does it for you). This throws rather than " +
        "skipping on purpose — a skip would read as a pass.",
    );
  }
  const { bin } = JSON.parse(readFileSync(manifest, "utf-8"));
  return join(CLI_DIR, typeof bin === "string" ? bin : Object.values(bin)[0]);
}

const OUT_DIR = mkdtempSync(join(tmpdir(), "cf-ui-tailwind-"));
after(() => rmSync(OUT_DIR, { recursive: true, force: true }));

/** Build one fixture, returning the raw exit status, output, and CSS. */
function build(fixture, { env } = {}) {
  const output = join(OUT_DIR, `${fixture}.out.css`);
  const result = spawnSync(
    process.execPath,
    [cliEntry(), "--input", join(FIXTURES, `${fixture}.css`), "--output", output],
    { encoding: "utf-8", env: { ...process.env, ...env } },
  );
  return {
    // `status` is null when a process dies on a signal; keep it raw so an
    // assertion against 0 cannot be satisfied by a crash.
    status: result.status,
    output: `${result.stdout ?? ""}${result.stderr ?? ""}`,
    css: existsSync(output) ? readFileSync(output, "utf-8") : "",
  };
}

describe("real Tailwind build — the good paths compile", () => {
  it("accepts a bare @plugin", () => {
    const { status, output } = build("bare");
    assert.equal(status, 0, `build failed:\n${output}`);
  });

  // The regression that matters. Tailwind forwards `@plugin { ... }` options
  // only to a plugin marked `__isOptionsFunction`; drop or rename that marker
  // upstream and this build starts failing with "does not accept options",
  // while the unit suite's `assert.equal(cfUiAxes.__isOptionsFunction, true)`
  // stays green.
  it("accepts options through @plugin { composition: console; }", () => {
    const { status, output } = build("composition");
    assert.equal(status, 0, `build failed:\n${output}`);
  });
});

describe("real Tailwind build — the CSS actually reaches the output", () => {
  const { status, css, output } = build("bare");

  it("compiled at all", () => {
    assert.equal(status, 0, `build failed:\n${output}`);
  });

  // A build that succeeds and emits nothing is the other silent failure: the
  // plugin would be "working" and the consumer would get no axis styling.
  it("emits a rule for every axis value, in both modes", () => {
    for (const axis of DEFINITION.axes) {
      const attr = DEFINITION.axisAttrs[axis];
      for (const value of Object.keys(DEFINITION.valueSets[axis] ?? {})) {
        const selector = `[${attr}="${value}"]`;
        assert.ok(css.includes(selector), `missing ${selector} in the compiled CSS`);
        if (DEFINITION.modeKeyedAxes.includes(axis)) {
          assert.ok(
            css.includes(`[data-theme="dark"]${selector}`),
            `missing the dark-mode rule for ${selector}`,
          );
        }
      }
    }
  });

  it("emits the Tailwind theme aliases", () => {
    for (const alias of Object.values(DEFINITION.aliases)) {
      assert.ok(css.includes(alias), `missing the ${alias} alias in the compiled CSS`);
    }
    assert.ok(css.includes("--color-primary"), "the --color-primary alias is the headline one");
  });

  it("emits the wide-gamut layer", () => {
    assert.ok(
      /@media\s*\(\s*color-gamut:\s*p3\s*\)/.test(css),
      "missing the @media (color-gamut: p3) layer",
    );
  });
});

describe("real Tailwind build — the bad path fails the build", () => {
  // The whole point of #7. Checked as an exit code from the process itself:
  // piping the CLI through anything else reports the pipeline's status, not
  // Tailwind's, and would pass against a build that never failed.
  it("exits non-zero on an unknown composition", () => {
    const { status, output } = build("bad-composition");
    assert.notEqual(status, 0, `the build succeeded — it must not:\n${output}`);
    assert.match(output, /unknown composition 'brutalist'/);
  });

  it("writes no stylesheet when it fails", () => {
    const { css } = build("bad-composition");
    assert.equal(css, "", "a failed build left a stylesheet behind");
  });
});
