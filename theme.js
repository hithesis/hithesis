(() => {
  const key = "hithesis-theme";
  const modes = ["system", "light", "dark"];
  const labels = { system: "自动", light: "浅色", dark: "深色" };
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  let mode = "system";
  try {
    const saved = localStorage.getItem(key);
    if (modes.includes(saved)) mode = saved;
  } catch {} // Private browsing may disallow persistent storage.

  function apply() {
    const theme = mode === "system" ? (system.matches ? "dark" : "light") : mode;
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.themeMode = mode;
    document.querySelector('meta[name="theme-color"]').content = theme === "dark" ? "#18262e" : "#ffffff";
    const button = document.getElementById("theme-toggle");
    if (button) {
      const next = modes[(modes.indexOf(mode) + 1) % modes.length];
      const description = `外观：${mode === "system" ? "跟随系统" : labels[mode]}（当前${labels[theme]}），点击切换为${labels[next]}`;
      document.getElementById("theme-label").textContent = labels[mode];
      button.setAttribute("aria-label", description);
      button.title = description;
    }
  }

  apply(); // Apply the saved/system theme before the stylesheet is rendered.
  system.addEventListener("change", apply);
  window.addEventListener("storage", (event) => {
    if (event.key === key || event.key === null) {
      mode = modes.includes(event.newValue) ? event.newValue : "system";
      apply();
    }
  });
  document.addEventListener("DOMContentLoaded", () => {
    apply();
    document.getElementById("theme-toggle").addEventListener("click", () => {
      mode = modes[(modes.indexOf(mode) + 1) % modes.length];
      try { localStorage.setItem(key, mode); } catch {}
      apply();
    });
  });
})();
