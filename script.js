const REPO = "https://github.com/hithesis/hithesis";
const STABLE_BASE = REPO + "/releases/latest/download/";
let devBuild = null;
let devState = "loading";

// Which types each family accepts; reportplus is fixed (single template).
const FAMILY = {
  chinese:    { types: ["doctor", "master", "bachelor", "postdoc"], stage: false },
  english:    { types: ["doctor", "master", "bachelor", "postdoc"], stage: false },
  reports:    { types: ["doctor", "master", "bachelor"],            stage: true  },
  reportplus: null,
};

function selected(group) {
  return Array.from(document.querySelectorAll(
    `[data-group="${group}"] input:checked`
  )).map((i) => i.value);
}

// Cartesian product of the checked groups, filtered to valid templates
// (mirrors the packaging script in make_release_pkg.sh).
function templateNames({ families, campuses, types, stages }) {
  const names = new Set();

  for (const f of families) {
    if (f === "reportplus") {
      names.add("reportplus-shenzhen-doctor-midterm");
      continue;
    }
    const info = FAMILY[f];
    for (const c of campuses) {
      for (const t of types) {
        if (!info.types.includes(t)) continue;
        if (info.stage) {
          for (const s of stages) {
            // hithesisart does not support doctor+midterm+shenzhen.
            if (t === "doctor" && s === "midterm" && c === "shenzhen") continue;
            names.add(`reports-${c}-${t}-${s}`);
          }
        } else {
          names.add(`${f}-${c}-${t}`);
        }
      }
    }
  }
  return Array.from(names).sort();
}

function compute() {
  return templateNames({ families: selected("family"), campuses: selected("campus"),
    types: selected("type"), stages: selected("stage") });
}

function validateDevBuild(data) {
  if (data.schema !== 2 || data.repository !== "hithesis/hithesis" || data.branch !== "dev" ||
      !/^v\d+\.\d+[a-z]?$/.test(data.version) || !/^\d{4}$/.test(data.date) ||
      data.label !== `${data.version}-dev.${data.date}` ||
      !/^[0-9a-f]{40}$/.test(data.commit) ||
      !/^dev-\d{8}-[0-9a-f]{12}-\d+-\d+$/.test(data.build_id) ||
      !/^[0-9a-f]{40}$/.test(data.source_commit) ||
      !/^[0-9a-f]{40}$/.test(data.download_snapshot_commit) ||
      !/^\d{4}-\d{2}-\d{2}$/.test(data.published_on) ||
      data.published_on.slice(5).replace("-", "") !== data.date ||
      data.download_base !== `https://raw.githubusercontent.com/hithesis/hithesis/${data.download_snapshot_commit}/dev-downloads/` ||
      data.release_url !== `https://hithesis.site/dev-builds/${data.build_id}/` ||
      !/^https:\/\/github\.com\/hithesis\/hithesis\/actions\/runs\/\d+$/.test(data.run_url)) {
    throw new Error("Invalid dev download metadata");
  }
  const names = templateNames({ families: Object.keys(FAMILY), campuses: ["harbin", "shenzhen", "weihai"],
    types: ["bachelor", "master", "doctor", "postdoc"], stages: ["opening", "midterm"] });
  for (const name of [...names, "hithesis-examples"]) {
    const file = data.files && data.files[name + ".zip"];
    if (!file || !/^[0-9a-f]{64}$/.test(file.sha256) || !Number.isSafeInteger(file.size) || file.size <= 0) {
      throw new Error("Incomplete dev download assets");
    }
  }
  const report = data.report;
  const pdf = data.files["DEV_UPDATE.pdf"];
  if (!report || report.filename !== "DEV_UPDATE.pdf" ||
      report.url !== data.release_url + "DEV_UPDATE.pdf" ||
      !/^[0-9a-f]{64}$/.test(report.sha256) || !pdf || pdf.sha256 !== report.sha256 ||
      !Number.isSafeInteger(pdf.size) || pdf.size < 1024) {
    throw new Error("Dev update PDF is missing or mismatched");
  }
  return data;
}

function downloadURL(name, channel, build) {
  if (channel === "dev") {
    if (!build || !build.files[name + ".zip"]) throw new Error("Dev download unavailable");
    return build.download_base + name + ".zip";
  }
  return STABLE_BASE + name + ".zip";
}

function channel() {
  return document.querySelector('[name="version"]:checked').value;
}

function renderVersion() {
  const development = channel() === "dev";
  const ready = !development || devState === "ready";
  document.getElementById("download").disabled = !ready;
  document.getElementById("download-all").disabled = !ready;
  document.getElementById("version-details").hidden = !development || !ready;
  const status = document.getElementById("version-status");
  if (!development) {
    status.textContent = "稳定版来自最新正式发布。";
  } else if (devState === "loading") {
    status.textContent = "正在读取最新通过测试的 dev 构建…";
  } else if (devState === "missing") {
    status.textContent = "尚未发布开发版下载包，可先选择稳定版。";
  } else if (!ready) {
    status.textContent = "暂时无法读取开发版信息，请稍后刷新或选择稳定版。";
  } else {
    status.textContent = `开发版 ${devBuild.label}，来自 dev 分支通过测试的构建。`;
    document.getElementById("build-date").textContent = `发布于 ${devBuild.published_on}（北京时间）`;
    const commit = document.getElementById("build-commit");
    commit.textContent = `提交 ${devBuild.source_commit.slice(0, 12)}`;
    commit.href = `${REPO}/commit/${devBuild.source_commit}`;
    document.getElementById("build-run").href = devBuild.run_url;
    document.getElementById("build-release").href = devBuild.release_url;
    document.getElementById("build-report").href = devBuild.report.url;
  }
}

function render() {
  const names = compute();
  document.getElementById("count").textContent = names.length;
  document.getElementById("list").innerHTML =
    names.map((n) => `<li>${n}.zip</li>`).join("");
  // Highlight the checked state on each label.
  document.querySelectorAll("label.opt").forEach((l) => {
    l.classList.toggle("checked", l.querySelector("input").checked);
  });
  renderVersion();
}

function downloadOne(name, version = channel(), build = devBuild) {
  const a = document.createElement("a");
  a.href = downloadURL(name, version, build);
  a.download = name + ".zip";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function downloadSelected() {
  const names = compute();
  if (!names.length) { alert("请先勾选需要的模板。"); return; }
  let i = 0;
  // Pin the whole batch to one build, even if the version selector changes.
  const version = channel();
  const build = devBuild;
  (function next() {
    if (i >= names.length) return;
    downloadOne(names[i++], version, build);
    setTimeout(next, 400);
  })();
}

async function loadVersions() {
  try {
    const response = await fetch("./dev.json", { cache: "no-store", signal: AbortSignal.timeout(10000) });
    if (response.status === 404) {
      devState = "missing";
    } else {
      if (!response.ok) throw new Error("Dev metadata request failed");
      devBuild = validateDevBuild(await response.json());
      devState = "ready";
    }
  } catch {
    devState = "error";
  }
  document.getElementById("dev-label").textContent = devBuild ? devBuild.label :
    (devState === "missing" ? "尚未发布" : "暂不可用");
  render();
}

function initialize() {
  const requested = new URL(window.location.href).searchParams.get("version");
  if (requested === "dev") document.querySelector('[name="version"][value="dev"]').checked = true;
  document.getElementById("download").addEventListener("click", downloadSelected);
  document.getElementById("download-all").addEventListener("click", () =>
    downloadOne("hithesis-examples"));
  document.getElementById("clear").addEventListener("click", () => {
    document.querySelectorAll("input[type=checkbox]").forEach((i) => (i.checked = false));
    render();
  });
  document.querySelectorAll("input[type=checkbox]").forEach((i) =>
    i.addEventListener("change", render));
  document.querySelectorAll('[name="version"]').forEach((i) => i.addEventListener("change", () => {
    const url = new URL(window.location.href);
    if (channel() === "dev") url.searchParams.set("version", "dev");
    else url.searchParams.delete("version");
    window.history.replaceState(null, "", url);
    render();
  }));

  render();
  loadVersions();
  fetch("https://api.github.com/repos/hithesis/hithesis/releases/latest", { signal: AbortSignal.timeout(10000) })
    .then((r) => { if (!r.ok) throw new Error("Release metadata unavailable"); return r.json(); })
    .then((r) => { if (/^v\d+\.\d+[a-z]?$/.test(r.tag_name)) document.getElementById("stable-label").textContent = r.tag_name; })
    .catch(() => {}); // Stable download links do not depend on the API request.
}

if (typeof document !== "undefined") initialize();
if (typeof module !== "undefined") module.exports = { templateNames, validateDevBuild, downloadURL };
