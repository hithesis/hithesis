(() => {
  const home = document.body.dataset.page === "home";
  const version = new URL(location.href).searchParams.get("version");
  if (home && (version === "dev" || version === "stable")) {
    location.replace("./download.html" + location.search + location.hash);
  }
  function replace(selector, markup) {
    const target = document.querySelector(selector);
    if (!target) return;
    target.insertAdjacentHTML("beforebegin", markup);
    target.remove();
  }
  const close = (label, id = "") => `<button class="button-quiet icon-button" type="button" ${id ? `id="${id}"` : ""} data-dialog-close aria-label="${label}"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><use href="#ui-close"/></svg></button>`;

  // Fluent UI WeatherSunny20Regular / WeatherMoon20Regular (MIT), also used by editor.
  replace("[data-site-header]", `
    <svg class="icon-definitions" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
      <symbol id="theme-light" viewBox="0 0 20 20"><path fill="currentColor" d="M10 2c.28 0 .5.22.5.5v1a.5.5 0 0 1-1 0v-1c0-.28.22-.5.5-.5m0 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8m0-1a3 3 0 1 1 0-6 3 3 0 0 1 0 6m7.5-2.5a.5.5 0 0 0 0-1h-1a.5.5 0 0 0 0 1zM10 16c.28 0 .5.22.5.5v1a.5.5 0 0 1-1 0v-1c0-.28.22-.5.5-.5m-6.5-5.5a.5.5 0 0 0 0-1H2.46a.5.5 0 0 0 0 1zm.65-6.35c.2-.2.5-.2.7 0l1 1a.5.5 0 1 1-.7.7l-1-1a.5.5 0 0 1 0-.7m.7 11.7a.5.5 0 0 1-.7-.7l1-1a.5.5 0 0 1 .7.7zm11-11.7a.5.5 0 0 0-.7 0l-1 1a.5.5 0 0 0 .7.7l1-1a.5.5 0 0 0 0-.7m-.7 11.7a.5.5 0 0 0 .7-.7l-1-1a.5.5 0 0 0-.7.7z"/></symbol>
      <symbol id="theme-dark" viewBox="0 0 20 20"><path fill="currentColor" d="M15.5 13.5A6.98 6.98 0 0 1 4 14.39c2.83-1.09 4.56-2.42 5.6-4.4 1.04-2 1.33-4.16.75-6.9q1.36.17 2.58.87a7 7 0 0 1 2.55 9.54M5.45 16.92A7.98 7.98 0 1 0 9.88 2.04a.6.6 0 0 0-.61.73c.69 2.82.43 4.88-.55 6.76-.94 1.78-2.55 3.03-5.55 4.1a.6.6 0 0 0-.3.9 8 8 0 0 0 2.59 2.39"/></symbol>
      <symbol id="theme-system" viewBox="0 0 20 20"><rect x="2.5" y="3.5" width="15" height="10" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M7 16.5h6m-3-3v3" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></symbol>
      <symbol id="ui-close" viewBox="0 0 24 24"><path d="m6 6 12 12M6 18 18 6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></symbol>
    </svg>
    <header class="site-header">
      <div class="container masthead">
        <a class="brand" href="./" aria-label="hi!Thesis 首页"><span class="brand-copy"><strong class="wordmark">h<span class="wordmark-pair"><span class="wordmark-i">i</span><span class="wordmark-bang" aria-hidden="true">!</span></span>Thesis</strong><span>哈尔滨工业大学学位论文模板</span></span></a>
        <nav class="site-nav" aria-label="网站导航">
          <a href="./" ${home ? 'class="active" aria-current="page"' : ""}>首页</a>
          <details class="nav-group ${home ? "" : "active"}" id="templates-menu" data-menu>
            <summary ${home ? "" : 'aria-current="page"'}>模板下载 <span class="menu-chevron" aria-hidden="true"></span></summary>
            <div class="popup-surface nav-popover">
              <a href="./download.html" ${home ? "" : 'aria-current="page"'}>LaTeX 模板</a>
              <button class="nav-disabled" type="button" disabled>Typst 模板 <span>暂未开放</span></button>
            </div>
          </details>
          <details class="nav-group" id="github-menu" data-menu>
            <summary>GitHub <span class="menu-chevron" aria-hidden="true"></span></summary>
            <div class="popup-surface nav-popover">
              <a href="https://github.com/hithesis/hithesis" target="_blank" rel="noopener">项目主页 <span aria-hidden="true">↗</span></a>
              <a href="https://github.com/hithesis/hithesis/issues/new/choose" target="_blank" rel="noopener">问题反馈 <span aria-hidden="true">↗</span></a>
              <a href="https://github.com/hithesis/hithesis/pulls" target="_blank" rel="noopener">参与贡献 <span aria-hidden="true">↗</span></a>
              <a href="https://github.com/hithesis/hithesis/releases" target="_blank" rel="noopener">正式发布 <span aria-hidden="true">↗</span></a>
            </div>
          </details>
          <a id="qq-join" href="https://qm.qq.com/q/BqA2wyvwfS" target="_blank" rel="noopener" data-dialog-open="qq-dialog" aria-haspopup="dialog">加入 QQ 群 <span aria-hidden="true">↗</span></a>
        </nav>
        <div class="header-tools">
          <a class="editor-entry" id="editor-open" href="./editor/" aria-haspopup="dialog">在线编辑 <span class="beta-badge">测试版</span></a>
          <details class="theme-picker" id="theme-picker" data-menu>
            <summary class="button-quiet theme-toggle" id="theme-toggle" aria-label="外观：跟随系统" title="外观：浅色 / 深色 / 跟随系统"><svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><use id="theme-icon" href="#theme-system"/></svg><span class="sr-only" id="theme-label">跟随系统</span></summary>
            <div class="popup-surface theme-options" role="radiogroup" aria-label="外观">
              <label class="theme-option"><input type="radio" name="appearance" value="light"><svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><use href="#theme-light"/></svg><span>浅色</span></label>
              <label class="theme-option"><input type="radio" name="appearance" value="dark"><svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><use href="#theme-dark"/></svg><span>深色</span></label>
              <label class="theme-option"><input type="radio" name="appearance" value="system" checked><svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><use href="#theme-system"/></svg><span>跟随系统</span></label>
            </div>
          </details>
        </div>
      </div>
    </header>`);

  const notices = document.querySelector("[data-community-links]");
  if (notices) notices.innerHTML = `
    <button class="recruit-notice donation-notice" id="contributors-open" type="button" aria-haspopup="dialog" aria-label="查看贡献者与捐赠二维码"><span class="recruit-title">贡献者</span><span class="ad-label">捐赠</span></button>
    <a class="recruit-notice" href="https://dustincys.github.io/cn/2025/03/jobad/" target="_blank" rel="noopener"><span class="recruit-title">初砚硕课题组招生</span><span class="ad-label">广告</span><span aria-hidden="true">↗</span></a>`;

  replace("[data-site-dialogs]", `
    <dialog class="popup-surface site-dialog contributors-dialog" id="contributors-dialog" aria-labelledby="contributors-heading" aria-describedby="contributors-note">
      <div class="dialog-top"><div class="dialog-heading"><h2 id="contributors-heading">贡献者</h2>${close("关闭贡献者名单", "contributors-close")}</div><p class="dialog-note" id="contributors-note">按 GitHub 提交次数排序</p></div>
      <div class="dialog-body" tabindex="0" role="region" aria-label="贡献者名单"><p id="contributors-status" role="status">正在读取名单…</p><ul class="contributors-list" id="contributors-list" aria-label="GitHub 贡献者"></ul></div>
      <div class="dialog-footer"><a href="https://github.com/hithesis/hithesis/graphs/contributors" target="_blank" rel="noopener">完整贡献记录 ↗</a></div>
    </dialog>
    <dialog class="popup-surface site-dialog editor-dialog" id="editor-dialog" aria-labelledby="editor-heading" aria-describedby="editor-warning">
      <div class="dialog-top"><div class="dialog-heading"><h2 id="editor-heading">在线编辑器 <span class="beta-badge">测试版</span></h2>${close("关闭编辑器提示")}</div></div>
      <div class="dialog-body editor-warning" id="editor-warning"><p>这是一个还在试验中的在线编辑器，可以当作排版玩具体验。</p><p><strong>请勿用于正式论文写作、提交或生产使用。</strong></p><p class="dialog-note">进入后，请继续阅读编辑器自己的使用协议。</p></div>
      <div class="dialog-footer dialog-actions"><button class="button secondary" type="button" data-dialog-close autofocus>返回下载</button><a class="button primary" id="editor-continue" href="./editor/">了解，进入测试版</a></div>
    </dialog>
    <dialog class="popup-surface site-dialog" id="qq-dialog" aria-labelledby="qq-heading">
      <div class="dialog-top"><div class="dialog-heading"><h2 id="qq-heading">加入 hiThesis QQ 群</h2>${close("关闭 QQ 群二维码")}</div></div>
      <div class="dialog-body qr-body"><img class="qr-code" id="qq-qr" src="./assets/community/qq-group.svg" width="216" height="216" alt="QQ 群 259959600 的进群二维码"><label class="group-number">群号 <input id="qq-group-number" value="259959600" readonly aria-label="QQ 群号"></label><p class="dialog-note" id="qq-copy-status" role="status">使用 QQ 扫码，或打开官方进群链接</p></div>
      <div class="dialog-footer dialog-actions"><button class="button secondary" id="qq-copy" type="button">复制群号</button><a class="button primary" id="qq-open" href="https://qm.qq.com/q/BqA2wyvwfS" target="_blank" rel="noopener">打开 QQ 加群 ↗</a></div>
    </dialog>
    <dialog class="popup-surface site-dialog" id="coffee-dialog" aria-labelledby="coffee-heading" aria-describedby="coffee-recipient">
      <div class="dialog-top"><div class="dialog-heading"><h2 id="coffee-heading">请他喝咖啡</h2>${close("关闭捐赠二维码")}</div><p class="dialog-note" id="coffee-recipient"></p></div>
      <div class="dialog-body qr-body"><div class="payment-methods" id="coffee-methods" role="radiogroup" aria-label="捐赠方式"></div><a class="donation-preview" id="coffee-image-link" target="_blank" rel="noopener" aria-busy="false"><span class="qr-placeholder" id="coffee-loading" hidden>正在载入二维码…</span><img class="qr-code donation-code" id="coffee-qr" width="240" height="240" alt="捐赠二维码" decoding="async"></a><p class="dialog-note" id="coffee-status" role="status">点击二维码可查看大图</p></div>
      <div class="dialog-footer"><a id="coffee-source" target="_blank" rel="noopener">README 中的捐赠信息 ↗</a></div>
    </dialog>`);
})();
