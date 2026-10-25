(() => {
  const menus = [...document.querySelectorAll("[data-menu]")];
  menus.forEach((menu) => {
    menu.addEventListener("toggle", () => {
      if (menu.open) menus.forEach((other) => { if (other !== menu) other.open = false; });
    });
  });
  document.addEventListener("click", (event) => {
    menus.forEach((menu) => { if (!menu.contains(event.target)) menu.open = false; });
    const trigger = event.target.closest("[data-dialog-open]");
    if (trigger) {
      const dialog = document.getElementById(trigger.dataset.dialogOpen);
      if (dialog && !dialog.open) dialog.showModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    menus.forEach((menu) => {
      if (menu.open) {
        menu.open = false;
        menu.querySelector("summary").focus();
      }
    });
  });
  document.querySelectorAll(".site-dialog").forEach((dialog) => {
    dialog.querySelectorAll("[data-dialog-close]").forEach((button) => {
      button.addEventListener("click", () => dialog.close());
    });
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right ||
          event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    });
  });

  const key = "hithesis-editor-preview-ack-v1";
  const entry = document.getElementById("editor-open");
  const dialog = document.getElementById("editor-dialog");
  let acknowledged = false;
  try { acknowledged = localStorage.getItem(key) === "yes"; } catch {}

  function openEditor(event) {
    if (acknowledged) return;
    if (event.type === "auxclick" && event.button !== 1) return;
    event.preventDefault();
    if (!dialog.open) dialog.showModal();
  }
  entry.addEventListener("click", openEditor);
  entry.addEventListener("auxclick", openEditor);
  document.getElementById("editor-continue").addEventListener("click", () => {
    acknowledged = true;
    try { localStorage.setItem(key, "yes"); } catch {}
  });
})();
