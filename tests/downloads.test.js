const test = require("node:test");
const assert = require("node:assert/strict");
const { templateNames, validateDevBuild, downloadURL } = require("../script.js");

const all = { families: ["chinese", "english", "reports", "reportplus"],
  campuses: ["harbin", "shenzhen", "weihai"], types: ["bachelor", "master", "doctor", "postdoc"],
  stages: ["opening", "midterm"] };

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
