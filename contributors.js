import { contributorProfile, openCoffee, preloadDonationImages } from "./community.js?v=campus-26";

(() => {
  const dialog = document.getElementById("contributors-dialog");
  const status = document.getElementById("contributors-status");
  const list = document.getElementById("contributors-list");
  let loaded = false;
  let loading = false;

  async function load() {
    if (loaded || loading) return;
    loading = true;
    status.hidden = false;
    status.textContent = "正在读取名单…";
    try {
      const response = await fetch("https://api.github.com/repos/hithesis/hithesis/contributors?per_page=100", {
        signal: AbortSignal.timeout(10000),
      });
      if (!response.ok) throw new Error("Contributor list unavailable");
      const data = await response.json();
      if (!Array.isArray(data)) throw new Error("Invalid contributor list");
      const contributors = data.filter((person) =>
        typeof person.login === "string" && /^[a-z\d-]+(?:\[bot\])?$/i.test(person.login) &&
        Number.isSafeInteger(person.id) && person.id > 0 &&
        Number.isSafeInteger(person.contributions) && person.contributions > 0
      ).sort((a, b) => b.contributions - a.contributions);
      if (!contributors.length) throw new Error("Empty contributor list");
      list.replaceChildren(...contributors.map((person) => {
        const item = document.createElement("li");
        const profile = document.createElement("a");
        profile.href = typeof person.html_url === "string" && person.html_url.startsWith("https://github.com/") ?
          person.html_url : `https://github.com/${encodeURIComponent(person.login)}`;
        profile.target = "_blank";
        profile.rel = "noopener";
        const avatar = document.createElement("img");
        avatar.src = typeof person.avatar_url === "string" && person.avatar_url.startsWith("https://avatars.githubusercontent.com/") ?
          person.avatar_url : `https://avatars.githubusercontent.com/u/${person.id}?s=64`;
        avatar.alt = "";
        avatar.width = 28;
        avatar.height = 28;
        avatar.loading = "lazy";
        const name = document.createElement("span");
        name.className = "contributor-name";
        const login = document.createElement("span");
        login.className = "contributor-login";
        login.textContent = person.login;
        name.append(login);
        const details = contributorProfile(person.login);
        if (details?.name) {
          const realName = document.createElement("span");
          realName.className = "contributor-real-name";
          realName.textContent = `（${details.name}）`;
          name.append(realName);
        }
        profile.append(avatar, name);
        const actions = document.createElement("div");
        actions.className = "contributor-actions";
        const count = document.createElement("span");
        count.className = "commit-count";
        count.textContent = `${person.contributions.toLocaleString("zh-CN")} 次提交`;
        actions.append(count);
        if (details?.donations.length) {
          const coffee = document.createElement("button");
          coffee.className = "button-quiet coffee-button";
          coffee.type = "button";
          coffee.textContent = "请他喝咖啡";
          coffee.setAttribute("aria-label", `请 ${person.login}（${details.name}）喝咖啡`);
          coffee.setAttribute("aria-haspopup", "dialog");
          coffee.addEventListener("click", () => openCoffee(person.login));
          actions.append(coffee);
        }
        item.append(profile, actions);
        return item;
      }));
      loaded = true;
      status.hidden = true;
    } catch {
      status.textContent = "暂时无法载入名单，请查看 GitHub 完整贡献记录。";
    } finally {
      loading = false;
    }
  }

  document.getElementById("contributors-open").addEventListener("click", () => {
    preloadDonationImages();
    dialog.showModal();
    load();
  });
})();
