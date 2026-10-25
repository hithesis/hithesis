const test = require("node:test");
const assert = require("node:assert/strict");
const { TEMPLATES, catalogFromFiles, templateNames, templateLabel, optionEnabled, reconcileSelection,
  validateDevBuild, validateManual, downloadURL } = require("../script.js");

const all = { languages: ["zh", "en"],
  campuses: ["harbin", "shenzhen", "weihai"], types: ["bachelor", "master", "doctor", "postdoc"],
  stages: ["opening", "midterm", "final"] };

function manifest() {
  const build = "dev-20261024-aaaaaaaaaaaa-123-1";
  return { schema: 2, repository: "hithesis/hithesis", branch: "dev", version: "v3.2b",
    label: "v3.2b-dev.1024", date: "1024", published_on: "2026-10-24", commit: "a".repeat(40),
    source_commit: "a".repeat(40), build_id: build, download_snapshot_commit: "d".repeat(40),
    download_base: `https://raw.githubusercontent.com/hithesis/hithesis/${"d".repeat(40)}/dev-downloads/`,
    release_url: `https://hithesis.site/dev-builds/${build}/`,
    run_url: "https://github.com/hithesis/hithesis/actions/runs/123",
    report: { filename: "DEV_UPDATE.pdf", url: `https://hithesis.site/dev-builds/${build}/DEV_UPDATE.pdf`,
      sha256: "c".repeat(64) },
    files: { ...Object.fromEntries([...templateNames(all), "hithesis-examples"].map((name) =>
      [name + ".zip", { sha256: "b".repeat(64), size: 100 }])),
      "DEV_UPDATE.pdf": { sha256: "c".repeat(64), size: 2000 } } };
}

test("all website choices match the 42 supported template variants", () => {
  const names = templateNames(all);
  assert.equal(names.length, 42);
  assert.equal(new Set(names).size, 42);
  assert(!names.includes("reports-shenzhen-doctor-midterm"));
  assert(!names.includes("reports-harbin-postdoc-opening"));
  assert(names.includes("reportplus-shenzhen-doctor-midterm"));
});

test("language and final stage select the correct thesis archive", () => {
  const selection = { languages: ["en"], campuses: ["harbin"], types: ["master"], stages: ["final"] };
  assert.deepEqual(templateNames(selection), ["english-harbin-master"]);
  assert.deepEqual(templateNames({ ...selection, stages: [] }), []);
  assert.deepEqual(templateNames({ ...selection, languages: [] }), []);
});

test("Shenzhen doctoral midterm is an ordinary combination, not an independent family", () => {
  assert.deepEqual(templateNames({ languages: ["zh"], campuses: ["shenzhen"], types: ["doctor"], stages: ["midterm"] }),
    ["reportplus-shenzhen-doctor-midterm"]);
  assert.deepEqual(templateNames({ languages: ["zh"], campuses: ["harbin"], types: ["doctor"], stages: ["midterm"] }),
    ["reports-harbin-doctor-midterm"]);
  assert.deepEqual(templateNames({ languages: ["zh"], campuses: [], types: [], stages: [] }), []);
});

test("download cards show readable document types without exposing a reportplus category", () => {
  assert.equal(templateLabel("reportplus-shenzhen-doctor-midterm"), "中文 · 深圳 · 博士中期报告");
  assert.equal(templateLabel("english-harbin-postdoc"), "英文 · 哈尔滨 · 博士后研究报告");
  assert.equal(templateLabel("chinese-weihai-master"), "中文 · 威海 · 硕士论文");
});

test("postdoc requires no stage and clears/disables every stage choice", () => {
  const selected = { languages: ["zh"], campuses: ["harbin"], types: ["postdoc"], stages: ["final", "midterm"] };
  const reconciled = reconcileSelection(selected);
  assert.deepEqual(reconciled.stages, []);
  assert.deepEqual(templateNames(reconciled), ["chinese-harbin-postdoc"]);
  for (const stage of all.stages) assert.equal(optionEnabled("stage", stage, reconciled), false);
  // A previous final selection must not trap the user outside the postdoc type.
  assert.equal(optionEnabled("type", "postdoc", { ...selected, types: ["doctor"], stages: ["final"] }), true);
  assert.deepEqual(selected.stages, ["final", "midterm"]); // No mutation of the caller's state.
});

test("English reports are disabled according to the actual stable/dev packages", () => {
  const selected = { languages: ["en"], campuses: ["shenzhen"], types: ["doctor"], stages: [] };
  assert.equal(optionEnabled("stage", "final", selected), true);
  assert.equal(optionEnabled("stage", "opening", selected), false);
  assert.equal(optionEnabled("stage", "midterm", selected), false);
  const report = { ...selected, languages: ["zh", "en"], stages: ["midterm"] };
  assert.equal(optionEnabled("language", "en", report), false);
  assert.deepEqual(reconcileSelection(report).languages, ["zh"]);
});

test("mixed postdoc/degree downloads apply stages only to the other degrees", () => {
  const selected = { languages: ["zh"], campuses: ["harbin"], types: ["postdoc", "doctor"], stages: ["opening"] };
  assert.deepEqual(templateNames(selected), ["chinese-harbin-postdoc", "reports-harbin-doctor-opening"]);
  assert.equal(optionEnabled("stage", "opening", selected), true);
});

test("empty selections leave applicable options available but download nothing", () => {
  assert.deepEqual(templateNames({}), []);
  assert.equal(optionEnabled("language", "en", {}), true);
  assert.equal(optionEnabled("type", "postdoc", {}), true);
  for (const stage of all.stages) assert.equal(optionEnabled("stage", stage, {}), true);
});

test("each packaged template is reachable through the four visible dimensions", () => {
  for (const template of TEMPLATES) {
    const selected = { languages: [template.language], campuses: [template.campus],
      types: [template.type], stages: template.stage === null ? [] : [template.stage] };
    assert.deepEqual(templateNames(selected), [template.name]);
    const stable = reconcileSelection(selected);
    assert.deepEqual(reconcileSelection(stable), stable);
    assert.deepEqual(templateNames(stable), [template.name]);
  }
  const published = require("../dev.json");
  assert.deepEqual(catalogFromFiles(Object.keys(published.files)).map((t) => t.name).sort(), templateNames(all));
});

test("version-specific catalogs disable missing combinations and remove stale selections", () => {
  const subset = catalogFromFiles(["chinese-harbin-doctor.zip", "hithesis-ctan.zip", "unrelated.zip"]);
  assert.equal(subset.length, 1);
  assert.equal(optionEnabled("language", "en", {}, subset), false);
  assert.equal(optionEnabled("campus", "shenzhen", {}, subset), false);
  assert.equal(optionEnabled("stage", "midterm", {}, subset), false);
  const selected = { languages: ["zh", "en"], campuses: ["harbin"], types: ["doctor"], stages: ["final"] };
  assert.deepEqual(reconcileSelection(selected, subset).languages, ["zh"]);
  assert.deepEqual(templateNames(selected, subset), ["chinese-harbin-doctor"]);
});

test("stable links remain usable without API or preview metadata", () => {
  assert.equal(downloadURL("chinese-harbin-doctor", "stable", null),
    "https://github.com/hithesis/hithesis/releases/latest/download/chinese-harbin-doctor.zip");
  assert.throws(() => downloadURL("hithesis-examples", "dev", null));
});

test("dated versions use the exact preview assets", () => {
  const build = validateDevBuild(manifest());
  assert.equal(downloadURL("hithesis-examples", "dev", build), build.download_base + "hithesis-examples.zip");
  for (const name of templateNames(all)) assert(downloadURL(name, "dev", build).startsWith(build.download_base));
});

test("incomplete or misidentified previews are not offered for download", () => {
  for (const modify of [
    (m) => { m.label = "1024"; },
    (m) => { m.published_on = "2026-10-25"; },
    (m) => { m.repository = "other/repository"; },
    (m) => { m.download_base = "https://example.com/"; },
    (m) => { delete m.files["chinese-harbin-doctor.zip"]; },
    (m) => { delete m.report; },
    (m) => { delete m.files["DEV_UPDATE.pdf"]; },
    (m) => { m.files["DEV_UPDATE.pdf"].sha256 = "d".repeat(64); },
  ]) {
    const build = manifest(); modify(build);
    assert.throws(() => validateDevBuild(build));
  }
});

test("backfilled and future manuals are tied to the selected build", () => {
  const metadata = require("../dev-manual.json");
  const build = require(`../dev-builds/${metadata.build_id}/dev.json`);
  assert.equal(validateManual(metadata, build).filename, "hithesis.pdf");
  const future = structuredClone(build);
  future.manual = structuredClone(metadata.manual);
  future.files[future.manual.filename] = { sha256: future.manual.sha256, size: future.manual.size };
  assert.equal(validateManual(future, future).url, future.release_url + "hithesis.pdf");
});

test("a changelog PDF or another build's manual cannot be shown as the user manual", () => {
  const original = require("../dev-manual.json");
  const build = require(`../dev-builds/${original.build_id}/dev.json`);
  for (const modify of [
    (m) => { m.build_id += "-other"; },
    (m) => { m.source_commit = "0".repeat(40); },
    (m) => { m.manual.filename = "DEV_UPDATE.pdf"; },
    (m) => { m.manual.url = "https://example.com/manual.pdf"; },
    (m) => { m.manual.pages = 0; },
    (m) => { m.manual.sha256 = "invalid"; },
  ]) {
    const metadata = structuredClone(original);
    modify(metadata);
    assert.throws(() => validateManual(metadata, build));
  }
  const altered = structuredClone(build);
  altered.files["hithesis.pdf"] = { sha256: "0".repeat(64), size: original.manual.size };
  assert.throws(() => validateManual(original, altered));
});
