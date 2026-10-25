(() => {
  const key = "iota4web-theme";
  const modes = ["system", "light", "dark"];
  const labels = { system: "跟随系统", light: "浅色", dark: "深色" };
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  function readMode(fallback = "system") {
    try {
      const saved = localStorage.getItem(key);
      return modes.includes(saved) ? saved : "system";
    } catch { return fallback; }
  }
  let mode = readMode();

  function apply() {
    const theme = mode === "system" ? (system.matches ? "dark" : "light") : mode;
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.themeMode = mode;
    document.querySelector('meta[name="theme-color"]').content = theme === "dark" ? "#252526" : "#ffffff";
    const button = document.getElementById("theme-toggle");
    if (button) {
      const description = `外观：${labels[mode]}（当前${labels[theme]}）`;
      document.getElementById("theme-label").textContent = labels[mode];
      document.getElementById("theme-icon").setAttribute("href", `#theme-${mode}`);
      button.setAttribute("aria-label", description);
      document.querySelectorAll('[name="appearance"]').forEach((input) => {
        input.checked = input.value === mode;
      });
    }
  }

  apply(); // Apply the saved/system theme before the stylesheet is rendered.
  system.addEventListener("change", apply);
  window.addEventListener("storage", (event) => {
    if (event.key === key || event.key === null) {
      mode = readMode(mode);
      apply();
    }
  });
  window.addEventListener("pageshow", () => {
    mode = readMode(mode);
    apply();
  });
  document.addEventListener("DOMContentLoaded", () => {
    apply();
    const picker = document.getElementById("theme-picker");
    const toggle = document.getElementById("theme-toggle");
    document.querySelectorAll('[name="appearance"]').forEach((input) => {
      input.addEventListener("change", () => {
        mode = input.value;
        try {
          if (mode === "system") localStorage.removeItem(key);
          else localStorage.setItem(key, mode);
        } catch {}
        apply();
        picker.open = false;
        toggle.focus();
      });
    });
    picker.addEventListener("click", (event) => {
      if (event.target.closest(".theme-option")?.querySelector("input")?.checked) {
        picker.open = false;
        toggle.focus();
      }
    });
    document.addEventListener("click", (event) => {
      if (!picker.contains(event.target)) picker.open = false;
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && picker.open) {
        picker.open = false;
        toggle.focus();
      }
    });
  });
})();
