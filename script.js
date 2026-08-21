const BASE = "https://github.com/hithesis/hithesis/releases/latest/download/";

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
function compute() {
  const families = selected("family");
  const campuses = selected("campus");
  const types    = selected("type");
  const stages   = selected("stage");
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

function render() {
  const names = compute();
  document.getElementById("count").textContent = names.length;
  document.getElementById("list").innerHTML =
    names.map((n) => `<li>${n}.zip</li>`).join("");
  // Highlight the checked state on each label.
  document.querySelectorAll("label.opt").forEach((l) => {
    l.classList.toggle("checked", l.querySelector("input").checked);
  });
}

function downloadOne(name) {
  const a = document.createElement("a");
  a.href = BASE + name + ".zip";
  a.download = name + ".zip";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function downloadSelected() {
  const names = compute();
  if (!names.length) { alert("请先勾选需要的模板。"); return; }
  let i = 0;
  (function next() {
    if (i >= names.length) return;
    downloadOne(names[i++]);
    setTimeout(next, 400);
  })();
}

document.getElementById("download").addEventListener("click", downloadSelected);
document.getElementById("download-all").addEventListener("click", () =>
  downloadOne("hithesis-examples"));
document.getElementById("clear").addEventListener("click", () => {
  document.querySelectorAll("input[type=checkbox]").forEach((i) => (i.checked = false));
  render();
});
document.querySelectorAll("input[type=checkbox]").forEach((i) =>
  i.addEventListener("change", render));

render();
