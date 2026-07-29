/**
 * Tailwind plugin tests (issue #7) — `node --test tests/js/`.
 *
 * The headline behavior is the throw: an unknown axis value has to stop the
 * CSS build, not warn and carry on. Everything else here exists to make sure
 * the throw is reachable in a real build and that nothing else regressed into
 * a silent no-op.
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

import cfUiAxes, {
  AxisPluginError,
  buildAxisBase,
  buildAxisCss,
  contrastReport,
  loadDefinition,
  mergeValueSets,
  oklabLightness,
  p3LightnessFailures,
  resolveComposition,
} from "../../src/cf_ui/static/cf_ui/cf_ui_tailwind_plugin.mjs";

const DEFINITION = JSON.parse(
  readFileSync(
    fileURLToPath(new URL("../../src/cf_ui/static/cf_ui/cf_ui_axes.json", import.meta.url)),
    "utf-8",
  ),
);

/** Collect what the plugin hands Tailwind, without importing Tailwind. */
function runHandler(plugin) {
  const collected = [];
  const handler = typeof plugin === "function" ? plugin.handler : plugin.handler;
  handler({ addBase: (styles) => collected.push(styles) });
  assert.equal(collected.length, 1, "expected exactly one addBase call");
  return collected[0];
}

describe("the build error", () => {
  it("throws on an unknown axis value", () => {
    assert.throws(() => cfUiAxes({ composition: { accent: "hotpink" } }), AxisPluginError);
  });

  it("names the axis and the valid values in the message", () => {
    try {
      cfUiAxes({ composition: { accent: "hotpink" } });
      assert.fail("expected a throw");
    } catch (error) {
      assert.match(error.message, /hotpink/);
      assert.match(error.message, /accent/);
      assert.match(error.message, /azure/, "the message must list what IS valid");
    }
  });

  it("throws on an unknown axis name", () => {
    assert.throws(() => cfUiAxes({ composition: { flavor: "vanilla" } }), /flavor/);
  });

  it("throws on an unknown named composition", () => {
    assert.throws(() => cfUiAxes({ composition: "brutalist" }), /brutalist/);
  });

  it("throws eagerly, before Tailwind ever calls the handler", () => {
    // A throw from inside the handler would still fail the build, but only
    // once Tailwind gets that far. Failing in the factory keeps the error at
    // the point of configuration, where the mistake actually is.
    assert.throws(() => cfUiAxes({ composition: { accent: "hotpink" } }));
  });

  it("accepts every shipped composition", () => {
    for (const name of Object.keys(DEFINITION.compositions)) {
      assert.doesNotThrow(() => cfUiAxes({ composition: name }));
    }
  });

  // Regression: membership was tested with `in`, which walks the prototype
  // chain. `"toString" in {}` is true, so an Object.prototype key sailed past
  // the check and generated an empty rule instead of failing the build — a
  // hole in the one guarantee this plugin exists to provide. Verified against
  // a real Tailwind v4 build, which now exits 1.
  it("rejects an axis value that only exists on Object.prototype", () => {
    assert.throws(() => cfUiAxes({ composition: { form: "toString" } }), /toString/);
  });

  it("rejects a composition name that only exists on Object.prototype", () => {
    assert.throws(() => cfUiAxes({ composition: "hasOwnProperty" }), /hasOwnProperty/);
  });

  it("rejects a value set keyed on __proto__", () => {
    // JSON.parse makes __proto__ a genuine own property, unlike a literal.
    const hostile = JSON.parse('{"form":{"__proto__":{"--cf-radius":"0"}}}');
    assert.throws(() => cfUiAxes({ valueSets: hostile }), /__proto__/);
  });
});

describe("plugin shape", () => {
  it("exposes a handler when imported directly with no options", () => {
    assert.equal(typeof cfUiAxes.handler, "function");
  });

  it("is also callable as a factory", () => {
    const plugin = cfUiAxes({ composition: "console" });
    assert.equal(typeof plugin.handler, "function");
  });

  it("carries a config object, per Tailwind's plugin contract", () => {
    assert.equal(typeof cfUiAxes({}).config, "object");
  });

  // Regression: without this marker Tailwind rejects `@plugin "..." { ... }`
  // with "does not accept options". A CSS-first consumer then cannot pass a
  // composition at all, so the plugin only ever validates the default
  // composition — which always passes. The build error would be silently
  // inert for the idiomatic v4 setup. Verified against Tailwind v4.3.3.
  it("is marked as accepting options, so the CSS-first path can pass them", () => {
    assert.equal(cfUiAxes.__isOptionsFunction, true);
  });

  it("needs no tailwindcss import to construct", () => {
    // The file is vendored into consuming apps; a bare import of
    // `tailwindcss/plugin` would make it unloadable outside a resolved
    // node_modules tree, which is exactly where a vendored file lives.
    const source = readFileSync(
      fileURLToPath(
        new URL("../../src/cf_ui/static/cf_ui/cf_ui_tailwind_plugin.mjs", import.meta.url),
      ),
      "utf-8",
    );
    assert.doesNotMatch(source, /from\s+["']tailwindcss/);
  });
});

describe("generated CSS", () => {
  const base = runHandler(cfUiAxes({}));

  it("emits a block per axis value", () => {
    assert.ok(base['[data-accent="azure"]'], "no azure block");
    assert.ok(base['[data-surface="plain"]'], "no plain surface block");
    assert.ok(base['[data-form="soft"]'], "no soft form block");
  });

  it("emits dark declarations under a data-theme selector", () => {
    const dark = base['[data-theme="dark"][data-accent="azure"]'];
    assert.ok(dark, "no dark azure block");
    assert.notEqual(dark["--cf-accent"], base['[data-accent="azure"]']["--cf-accent"]);
  });

  it("emits the Tailwind theme aliases alongside the cf tokens", () => {
    assert.equal(base['[data-accent="azure"]']["--color-primary"], "var(--cf-accent)");
  });

  it("emits the wide-gamut layer from the same definition", () => {
    const media = base["@media (color-gamut: p3)"];
    assert.ok(media, "no p3 layer");
    assert.match(media['[data-accent="azure"]']["--cf-accent"], /^oklch\(/);
  });

  it("omits a p3 block for a value that declares none", () => {
    const media = base["@media (color-gamut: p3)"];
    assert.equal(media['[data-accent="slate"]'], undefined);
  });

  it("serializes to CSS text as well, for inspection", () => {
    const css = buildAxisCss();
    assert.match(css, /\[data-accent="azure"\]\s*\{/);
    assert.match(css, /@media \(color-gamut: p3\)/);
  });
});

describe("consumer value sets", () => {
  const brand = {
    accent: {
      brand: {
        light: {
          "--cf-accent": "#7c3aed",
          "--cf-accent-content": "#ffffff",
          "--cf-accent-strong": "#5b21b6",
        },
        dark: {
          "--cf-accent": "#c4b5fd",
          "--cf-accent-content": "#2e1065",
          "--cf-accent-strong": "#ddd6fe",
        },
      },
    },
  };

  it("accepts an app's own value set and lets the composition use it", () => {
    const base = runHandler(cfUiAxes({ valueSets: brand, composition: { accent: "brand" } }));
    assert.equal(base['[data-accent="brand"]']["--cf-accent"], "#7c3aed");
  });

  it("extends by default — the shipped values survive", () => {
    const base = runHandler(cfUiAxes({ valueSets: brand }));
    assert.ok(base['[data-accent="azure"]'], "extend mode dropped a shipped value");
  });

  it("replace mode drops the shipped values for that axis only", () => {
    const options = { valueSets: brand, valueSetsMode: "replace", composition: { accent: "brand" } };
    const base = runHandler(cfUiAxes(options));
    assert.equal(base['[data-accent="azure"]'], undefined);
    assert.ok(base['[data-surface="plain"]'], "replace leaked into an untouched axis");
  });

  it("makes a shipped value unknown after replace — so the build still fails", () => {
    assert.throws(
      () => cfUiAxes({ valueSets: brand, valueSetsMode: "replace", composition: "console" }),
      /azure/,
    );
  });

  it("rejects a mode-keyed value missing a mode", () => {
    const half = { accent: { half: { light: { "--cf-accent": "#000000" } } } };
    assert.throws(() => cfUiAxes({ valueSets: half }), /dark/);
  });

  it("rejects a token that is not a custom property", () => {
    const bad = { form: { edgy: { radius: "0" } } };
    assert.throws(() => cfUiAxes({ valueSets: bad }), /--/);
  });

  it("rejects an invalid value name", () => {
    const bad = { form: { "Not Valid": { "--cf-radius": "0" } } };
    assert.throws(() => cfUiAxes({ valueSets: bad }), /Not Valid/);
  });

  it("rejects an unknown axis in a value set", () => {
    assert.throws(() => cfUiAxes({ valueSets: { flavor: { vanilla: {} } } }), /flavor/);
  });

  it("rejects a token value that would break out of its declaration", () => {
    // Consumer value sets are interpolated straight into generated CSS. A
    // value carrying `;` or `}` writes rules the app never declared.
    const bad = { form: { evil: { "--cf-radius": "0; } body { display: none" } } };
    assert.throws(() => cfUiAxes({ valueSets: bad }), /--cf-radius/);
  });

  it("does not mutate the shipped definition", () => {
    // A composition is required here: `replace` has just removed the default
    // composition's `slate`, and the plugin is right to reject that.
    cfUiAxes({ valueSets: brand, valueSetsMode: "replace", composition: { accent: "brand" } });
    const fresh = loadDefinition();
    assert.ok(fresh.valueSets.accent.azure, "the shipped definition was mutated");
  });
});

describe("contrast report", () => {
  it("covers every accent x surface x mode", () => {
    const rows = contrastReport(DEFINITION.valueSets, DEFINITION.contrastPairs);
    const accents = Object.keys(DEFINITION.valueSets.accent).length;
    const surfaces = Object.keys(DEFINITION.valueSets.surface).length;
    assert.equal(rows.length, accents * surfaces * DEFINITION.modes.length);
  });

  it("reports the shipped set as clean", () => {
    const rows = contrastReport(DEFINITION.valueSets, DEFINITION.contrastPairs);
    assert.deepEqual(
      rows.filter((row) => row.failures.length),
      [],
    );
  });

  it("flags a combination that fails AA", () => {
    const sets = mergeValueSets(DEFINITION, {
      accent: {
        faint: {
          light: {
            "--cf-accent": "#eeeeee",
            "--cf-accent-content": "#ffffff",
            "--cf-accent-strong": "#f5f5f5",
          },
          dark: {
            "--cf-accent": "#eeeeee",
            "--cf-accent-content": "#ffffff",
            "--cf-accent-strong": "#f5f5f5",
          },
        },
      },
    });
    const rows = contrastReport(sets, DEFINITION.contrastPairs);
    const faint = rows.filter((row) => row.accent === "faint" && row.failures.length);
    assert.ok(faint.length, "an unreadable accent produced no failures");
    assert.match(faint[0].failures[0], /--cf-accent-content on --cf-accent/);
  });

  it("warns rather than throwing — the build error is for unknown values", () => {
    const warnings = [];
    const original = console.warn;
    console.warn = (message) => warnings.push(String(message));
    try {
      const faint = {
        accent: {
          faint: {
            light: {
              "--cf-accent": "#eeeeee",
              "--cf-accent-content": "#ffffff",
              "--cf-accent-strong": "#f5f5f5",
            },
            dark: {
              "--cf-accent": "#eeeeee",
              "--cf-accent-content": "#ffffff",
              "--cf-accent-strong": "#f5f5f5",
            },
          },
        },
      };
      assert.doesNotThrow(() => cfUiAxes({ valueSets: faint, contrastReport: true }));
      assert.ok(
        warnings.some((line) => /faint/.test(line)),
        "the failing combination was never surfaced",
      );
    } finally {
      console.warn = original;
    }
  });

  it("is off by default, so an existing build does not start shouting", () => {
    const warnings = [];
    const original = console.warn;
    console.warn = (message) => warnings.push(String(message));
    try {
      cfUiAxes({});
      assert.deepEqual(warnings, []);
    } finally {
      console.warn = original;
    }
  });

  it("computes a known WCAG ratio correctly", () => {
    // Black on white is 21:1 by definition; if this drifts the whole report
    // is decorative.
    const rows = contrastReport(
      {
        accent: { a: { light: { "--cf-fg": "#000000" }, dark: { "--cf-fg": "#000000" } } },
        surface: { s: { light: { "--cf-bg": "#ffffff" }, dark: { "--cf-bg": "#ffffff" } } },
      },
      [{ foreground: "--cf-fg", background: "--cf-bg", minimum: 21 }],
    );
    assert.deepEqual(rows[0].failures, []);
  });
});

describe("resolveComposition", () => {
  it("defaults to the shipped default composition", () => {
    const resolved = resolveComposition(DEFINITION, null, DEFINITION.valueSets);
    assert.deepEqual(resolved, DEFINITION.compositions.default);
  });

  it("layers a partial mapping over the default", () => {
    const resolved = resolveComposition(DEFINITION, { accent: "azure" }, DEFINITION.valueSets);
    assert.equal(resolved.accent, "azure");
    assert.equal(resolved.surface, DEFINITION.compositions.default.surface);
  });
});

describe("buildAxisBase", () => {
  it("is exported for consumers not using the plugin form", () => {
    const base = buildAxisBase(DEFINITION.valueSets);
    assert.ok(base['[data-accent="slate"]']);
  });
});

// --- issue #20 --------------------------------------------------------------

describe("unsafe token values (#20 §1)", () => {
  const UNSAFE = [
    "0; } body { display: none",
    "red; color: blue",
    "}",
    "{",
    "red /* c",
    "red */",
    "</style><script>alert(1)</script>",
    "<",
  ];

  for (const value of UNSAFE) {
    it(`rejects ${JSON.stringify(value)}`, () => {
      assert.throws(
        () => mergeValueSets(DEFINITION, { form: { probe: { "--cf-radius": value } } }),
        /unsafe value/,
      );
    });
  }

  it("rejects '<' so a value cannot escape the <style> element", () => {
    // Added in #20 to match the Python gate; the original rule allowed it.
    assert.throws(
      () => mergeValueSets(DEFINITION, { form: { probe: { "--cf-radius": "</style>" } } }),
      /unsafe value/,
    );
  });

  it("still accepts a shadow value carrying slashes and parentheses", () => {
    const merged = mergeValueSets(DEFINITION, {
      form: { probe: { "--cf-radius": "0 1px 2px rgb(0 0 0 / 0.08)" } },
    });
    assert.equal(merged.form.probe["--cf-radius"], "0 1px 2px rgb(0 0 0 / 0.08)");
  });
});

describe("the exported generators validate by default (#20 §4)", () => {
  const BAD_NAME = { form: { probe: { "cf-radius": "0" } } };
  const BAD_VALUE = { form: { probe: { "--cf-radius": "0; } html {" } } };

  it("buildAxisBase rejects a token name that is not a custom property", () => {
    assert.throws(() => buildAxisBase(BAD_NAME), /custom propert/);
  });

  it("buildAxisBase rejects an unsafe token value", () => {
    assert.throws(() => buildAxisBase(BAD_VALUE), /unsafe value/);
  });

  it("buildAxisCss rejects the same input", () => {
    assert.throws(() => buildAxisCss(BAD_VALUE), /unsafe value/);
  });

  it("buildAxisBase rejects an invalid axis value name", () => {
    assert.throws(() => buildAxisBase({ form: { "Not Valid": { "--cf-radius": "0" } } }), /Not Valid/);
  });

  it("the opt-out is explicit, and still generates", () => {
    const base = buildAxisBase(BAD_VALUE, undefined, { validate: false });
    assert.equal(base['[data-form="probe"]']["--cf-radius"], "0; } html {");
  });

  it("the opt-out does not change what valid input generates", () => {
    const checked = buildAxisBase(DEFINITION.valueSets, DEFINITION);
    const unchecked = buildAxisBase(DEFINITION.valueSets, DEFINITION, { validate: false });
    assert.deepEqual(unchecked, checked);
  });

  it("validates the shipped defaults without complaint", () => {
    assert.ok(buildAxisBase()['[data-accent="slate"]']);
  });
});

describe("the p3 lightness invariant (#20 §3)", () => {
  it("passes for the shipped value sets", () => {
    assert.deepEqual(p3LightnessFailures(DEFINITION.valueSets, DEFINITION), []);
  });

  it("flags an override whose lightness drifts from the base", () => {
    const drifted = structuredClone(DEFINITION.valueSets);
    drifted.accent.azure.p3.light["--cf-accent"] = "oklch(72.0% 0.137 242.7)";
    const failures = p3LightnessFailures(drifted, DEFINITION);
    assert.equal(failures.length, 1);
    assert.match(failures[0], /azure/);
    assert.match(failures[0], /--cf-accent/);
  });

  it("tolerates the rounding in an authored one-decimal value", () => {
    const rounded = structuredClone(DEFINITION.valueSets);
    // The measured base is 49.998%; the authored 50.0% must stay legal.
    rounded.accent.azure.p3.light["--cf-accent"] = "oklch(50.0% 0.137 242.7)";
    assert.deepEqual(p3LightnessFailures(rounded, DEFINITION), []);
  });

  it("flags a p3 override of a token the base never declared", () => {
    const orphan = structuredClone(DEFINITION.valueSets);
    orphan.accent.azure.p3.light["--cf-nonexistent"] = "oklch(50% 0.1 240)";
    assert.match(p3LightnessFailures(orphan, DEFINITION).join("\n"), /--cf-nonexistent/);
  });

  it("flags a p3 value that is not oklch rather than skipping it", () => {
    const bad = structuredClone(DEFINITION.valueSets);
    bad.accent.azure.p3.light["--cf-accent"] = "#0369a1";
    assert.equal(p3LightnessFailures(bad, DEFINITION).length, 1);
  });

  it("measures oklab lightness against known anchors", () => {
    assert.ok(Math.abs(oklabLightness("#000000") - 0) < 0.001);
    assert.ok(Math.abs(oklabLightness("#ffffff") - 1) < 0.001);
    assert.ok(Math.abs(oklabLightness("#0369a1") - 0.5) < 0.002);
  });
});

describe("the --spacing alias is gone (#20 §2)", () => {
  it("no longer aliases Tailwind's spacing base unit", () => {
    assert.equal(DEFINITION.aliases["--cf-spacing"], undefined);
    const base = buildAxisBase();
    assert.equal(base['[data-density="compact"]']["--spacing"], undefined);
  });

  it("still emits the cf-ui token itself", () => {
    const base = buildAxisBase();
    assert.equal(base['[data-density="compact"]']["--cf-spacing"], "0.2rem");
  });

  it("keeps the namespaced color aliases", () => {
    const base = buildAxisBase();
    assert.equal(base['[data-accent="azure"]']["--color-primary"], "var(--cf-accent)");
  });
});
