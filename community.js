import { COMMUNITY } from "./community-data.js?v=campus-26";

export { COMMUNITY };

const imageCache = new Map();
let imageRequest = 0;

function cachedImage(source, priority = "low") {
  if (imageCache.has(source)) {
    const cached = imageCache.get(source);
    if (priority === "high") cached.image.fetchPriority = "high";
    return cached;
  }
  const image = new Image();
  image.decoding = "async";
  image.fetchPriority = priority;
  const ready = new Promise((resolve, reject) => {
    image.onload = () => resolve(image);
    image.onerror = () => { imageCache.delete(source); reject(new Error("QR image unavailable")); };
  });
  const cached = { image, ready };
  imageCache.set(source, cached);
  image.src = source;
  return cached;
}

export function preloadDonationImages() {
  return Promise.allSettled(Object.values(COMMUNITY.contributors)
    .flatMap(person => person.donations.map(method => cachedImage(method.image).ready)));
}

export function contributorProfile(login) {
  return Object.entries(COMMUNITY.contributors).find(([name]) => name.toLowerCase() === login.toLowerCase())?.[1];
}

export function openCoffee(login) {
  const person = contributorProfile(login);
  if (!person?.donations.length) return;
  const dialog = document.getElementById("coffee-dialog");
  const image = document.getElementById("coffee-qr");
  const link = document.getElementById("coffee-image-link");
  const status = document.getElementById("coffee-status");
  const loading = document.getElementById("coffee-loading");
  document.getElementById("coffee-recipient").textContent = `${login}（${person.name}）`;
  document.getElementById("coffee-source").href = COMMUNITY.sources.donations;
  function show(method) {
    const request = ++imageRequest;
    const cached = cachedImage(method.image, "high");
    image.alt = `${person.name}的${method.label}捐赠二维码`;
    link.href = method.image;
    link.setAttribute("aria-busy", "true");
    image.hidden = true;
    loading.hidden = false;
    loading.textContent = "正在载入二维码…";
    status.textContent = `${method.label} · 点击二维码区域可查看大图`;
    image.src = method.image;
    function showReady() {
      if (request !== imageRequest) return;
      image.hidden = false;
      loading.hidden = true;
      link.setAttribute("aria-busy", "false");
    }
    if (cached.image.complete && cached.image.naturalWidth > 0) showReady();
    else cached.ready.then(showReady).catch(() => {
      if (request !== imageRequest) return;
      loading.textContent = "二维码暂时无法加载，点击查看大图";
      link.setAttribute("aria-busy", "false");
    });
  }
  const methods = document.getElementById("coffee-methods");
  methods.hidden = person.donations.length < 2;
  methods.replaceChildren(...person.donations.map((method, index) => {
    const label = document.createElement("label");
    label.className = "payment-method";
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "coffee-method";
    input.value = String(index);
    input.checked = index === 0;
    input.addEventListener("change", () => { if (input.checked) show(method); });
    const text = document.createElement("span");
    text.textContent = method.label;
    label.append(input, text);
    return label;
  }));
  show(person.donations[0]);
  if (!dialog.open) dialog.showModal();
}

if (typeof document !== "undefined") {
  const group = COMMUNITY.group;
  document.getElementById("qq-join").href = group.joinURL;
  document.getElementById("qq-open").href = group.joinURL;
  document.getElementById("qq-qr").src = group.qrImage;
  const number = document.getElementById("qq-group-number");
  number.value = group.number;
  document.getElementById("qq-copy").addEventListener("click", async () => {
    const status = document.getElementById("qq-copy-status");
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(group.number);
      status.textContent = "群号已复制";
    } catch {
      number.focus();
      number.select();
      status.textContent = "请复制已选中的群号";
    }
  });
}
