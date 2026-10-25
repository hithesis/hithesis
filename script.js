const REPO = "https://github.com/hithesis/hithesis";
const STABLE_BASE = REPO + "/releases/latest/download/";
let devBuild = null;
let devState = "loading";

const OPTIONS = {
  language: ["zh", "en"],
  campus: ["harbin", "weihai", "shenzhen"],
  type: ["doctor", "master", "bachelor", "postdoc"],
  stage: ["opening", "midterm", "final"],
};
const SELECTION_KEYS = { language: "languages", campus: "campuses", type: "types", stage: "stages" };

// UI dimensions are independent of legacy class/package names. A null stage
// means "not applicable", rather than calling a postdoc report a final thesis.
const TEMPLATES = [];
for (const campus of OPTIONS.campus) {
  for (const type of OPTIONS.type) {
    for (const language of OPTIONS.language) {
      TEMPLATES.push({ language, campus, type, stage: type === "postdoc" ? null : "final",
        name: `${language === "zh" ? "chinese" : "english"}-${campus}-${type}` });
    }
    if (type === "postdoc") continue;
    for (const stage of ["opening", "midterm"]) {
      const name = campus === "shenzhen" && type === "doctor" && stage === "midterm" ?
        "reportplus-shenzhen-doctor-midterm" : `reports-${campus}-${type}-${stage}`;
      TEMPLATES.push({ language: "zh", campus, type, stage, name });
    }
  }
}
let stableTemplates = TEMPLATES;
let stableCombinedAvailable = true;

function catalogFromFiles(files) {
  const available = new Set(files);
  return TEMPLATES.filter((t) => available.has(t.name + ".zip"));
}

function normalizeSelection(selection) {
  return Object.fromEntries(Object.entries(SELECTION_KEYS).map(([group, key]) =>
    [key, OPTIONS[group].filter((value) => (selection[key] || []).includes(value))]));
}

function matches(template, selection) {
  return Object.entries(SELECTION_KEYS).every(([group, key]) =>
    (group === "stage" && template.stage === null) ||
    !selection[key].length || selection[key].includes(template[group]));
}

function optionEnabled(group, value, selection, catalog = TEMPLATES) {
  const candidate = { ...normalizeSelection(selection), [SELECTION_KEYS[group]]: [value] };
  // A postdoc row cannot make a stage look applicable, but stage choices must
  // never prevent switching to a type that does not have a stage.
  return catalog.some((t) => t[group] === value && matches(t, candidate));
}

function reconcileSelection(selection, catalog = TEMPLATES) {
  const result = normalizeSelection(selection);
  let changed;
  do {
    changed = false;
    for (const [group, key] of Object.entries(SELECTION_KEYS)) {
      const remaining = result[key].filter((value) => optionEnabled(group, value, result, catalog));
      if (remaining.length !== result[key].length) changed = true;
      result[key] = remaining;
    }
  } while (changed);
  return result;
}

function selected(group) {
  return Array.from(document.querySelectorAll(
    `[data-group="${group}"] input:checked`
  )).map((i) => i.value);
}

function templateNames(selection, catalog = TEMPLATES) {
  const s = normalizeSelection(selection);
  if (!s.languages.length || !s.campuses.length || !s.types.length) return [];
  return catalog.filter((t) => matches(t, s) && (t.stage === null || s.stages.includes(t.stage)))
    .map((t) => t.name).sort();
}

const LABELS = {
  language: { zh: "中文", en: "英文" },
  campus: { harbin: "哈尔滨", weihai: "威海", shenzhen: "深圳" },
  type: { bachelor: "本科", master: "硕士", doctor: "博士", postdoc: "博士后" },
  stage: { opening: "开题", midterm: "中期", final: "终稿" },
};

function templateLabel(name) {
  const t = TEMPLATES.find((template) => template.name === name);
  if (!t) return name;
  const document = t.type === "postdoc" ? "博士后研究报告" :
    LABELS.type[t.type] + (t.stage === "final" ? "论文" : LABELS.stage[t.stage] + "报告");
  return [LABELS.language[t.language], LABELS.campus[t.campus], document].join(" · ");
}

function selection() {
  return Object.fromEntries(Object.entries(SELECTION_KEYS).map(([group, key]) => [key, selected(group)]));
}

function activeCatalog() {
  if (channel() === "dev") return devBuild ? catalogFromFiles(Object.keys(devBuild.files)) : TEMPLATES;
  return stableTemplates;
}

function compute() {
  if (channel() === "dev" && devState !== "ready") return [];
  return templateNames(selection(), activeCatalog());
}

function renderOptions() {
  const catalog = activeCatalog();
  const s = reconcileSelection(selection(), catalog);
  for (const [group, key] of Object.entries(SELECTION_KEYS)) {
    document.querySelectorAll(`[data-group="${group}"] input`).forEach((input) => {
      input.checked = s[key].includes(input.value);
      input.disabled = !optionEnabled(group, input.value, s, catalog);
      const label = input.closest("label");
      label.classList.toggle("disabled", input.disabled);
      label.title = input.disabled ? (group === "stage" && s.types.length === 1 && s.types[0] === "postdoc" ?
        "博士后不分阶段" : "此组合暂无模板") : "";
    });
  }
  const postdocOnly = s.types.length === 1 && s.types[0] === "postdoc";
  document.getElementById("stage-panel").classList.toggle("inapplicable", postdocOnly);
  const hint = document.getElementById("stage-hint");
  hint.textContent = s.types.includes("postdoc") ? "博士后不分阶段。" : "";
  hint.hidden = !hint.textContent;
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
  const names = TEMPLATES.map((t) => t.name);
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
  document.getElementById("download").disabled = !ready || compute().length === 0;
  document.getElementById("download-all").disabled = !ready || (!development && !stableCombinedAvailable);
  document.getElementById("version-details").hidden = !development || !ready;
  const status = document.getElementById("version-status");
  status.hidden = !development || ready;
  const info = document.querySelector(".version-info");
  info.hidden = !development;
  if (!development) info.open = false;
  if (!development) {
    status.textContent = "";
  } else if (devState === "loading") {
    status.textContent = "正在读取开发版…";
  } else if (devState === "missing") {
    status.textContent = "暂无开发版。";
  } else if (!ready) {
    status.textContent = "开发版信息暂时无法读取，请稍后刷新。";
  } else {
    status.textContent = "";
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
  renderOptions();
  const names = compute();
  document.getElementById("count").textContent = names.length;
  document.getElementById("download-count").textContent = names.length;
  document.getElementById("download").setAttribute("aria-label", `下载选中的 ${names.length} 份模板`);
  document.getElementById("empty-state").hidden = names.length > 0;
  document.getElementById("list").replaceChildren(...names.map((name) => {
    const item = document.createElement("li");
    const title = document.createElement("span");
    title.className = "template-name";
    title.textContent = templateLabel(name);
    const filename = document.createElement("code");
    filename.className = "template-file";
    filename.textContent = name + ".zip";
    item.append(title, filename);
    return item;
  }));
  const s = selection();
  const summary = Object.entries(SELECTION_KEYS).map(([group, key]) =>
    s[key].map((value) => LABELS[group][value]).join("、")).filter(Boolean);
  document.getElementById("clear").disabled = !summary.length;
  document.getElementById("selection-summary").textContent = summary.join(" / ");
  document.getElementById("selection-summary").hidden = !summary.length;
  document.getElementById("action-summary").textContent =
    `已匹配 ${names.length} 份模板 · ${channel() === "dev" ? "开发版" : "稳定版"}`;
  const complete = s.languages.length && s.campuses.length && s.types.length;
  const prompt = names.length ? "" : complete && !s.types.includes("postdoc") && !s.stages.length ? "请选择阶段。" : "请选择模板。";
  document.getElementById("selection-status").textContent = names.length ? `已选 ${names.length} 份模板` : prompt;
  document.querySelector("#empty-state p").textContent = prompt;
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
  const versionInfo = document.querySelector(".version-info");
  document.addEventListener("click", (event) => {
    if (!versionInfo.contains(event.target)) versionInfo.open = false;
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && versionInfo.open) {
      versionInfo.open = false;
      versionInfo.querySelector("summary").focus();
    }
  });
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
    .then((r) => {
      if (!/^v\d+\.\d+[a-z]?$/.test(r.tag_name)) return;
      document.getElementById("stable-label").textContent = r.tag_name;
      if (Array.isArray(r.assets)) {
        const files = r.assets.map((asset) => asset.name);
        stableTemplates = catalogFromFiles(files);
        stableCombinedAvailable = files.includes("hithesis-examples.zip");
        render();
      }
    })
    .catch(() => {}); // Stable download links do not depend on the API request.
}

if (typeof document !== "undefined") initialize();
if (typeof module !== "undefined") module.exports = {
  TEMPLATES, catalogFromFiles, templateNames, templateLabel, optionEnabled, reconcileSelection, validateDevBuild, downloadURL,
};
