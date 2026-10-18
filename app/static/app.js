const $ = (id) => document.getElementById(id);
const keyInput = $("api-key");
keyInput.value = localStorage.getItem("apiKey") || "";
$("alias-prefix").textContent = location.host + "/";

let allLinks = [];

/* ---------- Утилиты ---------- */

const ICONS = {
  copy: '<svg viewBox="0 0 24 24"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>',
  trash: '<svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>',
  chart: '<svg viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/></svg>',
};

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const stripProto = (u) => u.replace(/^https?:\/\//, "");
const nf = new Intl.NumberFormat("ru-RU");
const rtf = new Intl.RelativeTimeFormat("ru", { numeric: "auto" });

function timeAgo(iso) {
  const sec = (new Date(iso) - Date.now()) / 1000;
  const units = [["year", 31536000], ["month", 2592000], ["week", 604800], ["day", 86400], ["hour", 3600], ["minute", 60]];
  for (const [unit, s] of units) {
    if (Math.abs(sec) >= s) return rtf.format(Math.round(sec / s), unit);
  }
  return "только что";
}

function hostOf(url) {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return "?"; }
}

function headers() {
  const h = { "Content-Type": "application/json" };
  if (keyInput.value) h["X-API-Key"] = keyInput.value;
  return h;
}

let toastTimer;
function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 1800);
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // Clipboard API недоступен по http в локальной сети — запасной вариант
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    document.execCommand("copy"); ta.remove();
  }
  toast("Скопировано в буфер обмена");
}

function showError(msg) {
  $("error").textContent = msg;
  $("error").classList.toggle("hidden", !msg);
}

async function errorText(res) {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail.map((d) => d.msg.replace(/^Value error, /, "")).join("; ");
  } catch {}
  return `Ошибка ${res.status}`;
}

/* ---------- Данные ---------- */

async function loadStats() {
  const res = await fetch("/api/stats", { headers: headers() });
  if (!res.ok) { $("stat-links").textContent = "—"; $("stat-clicks").textContent = "—"; return; }
  const s = await res.json();
  $("stat-links").textContent = nf.format(s.links);
  $("stat-clicks").textContent = nf.format(s.clicks);
}

async function loadLinks() {
  loadStats();
  const res = await fetch("/api/links", { headers: headers() });
  if (!res.ok) {
    allLinks = [];
    render(res.status === 401 ? "Введите API-ключ, чтобы увидеть ссылки" : await errorText(res));
    return;
  }
  allLinks = await res.json();
  render();
}

function render(emptyMessage) {
  const q = $("search").value.trim().toLowerCase();
  const links = q
    ? allLinks.filter((l) => l.code.toLowerCase().includes(q) || l.url.toLowerCase().includes(q))
    : allLinks;

  $("links").innerHTML = links.map((l, i) => `
    <li class="link-item" style="animation-delay:${Math.min(i, 10) * 25}ms">
      <span class="favicon">${esc(hostOf(l.url)[0] || "?")}</span>
      <div class="link-main">
        <a class="link-short" href="${esc(l.short_url)}" target="_blank" rel="noopener">${esc(stripProto(l.short_url))}</a>
        <span class="link-orig" title="${esc(l.url)}">${esc(stripProto(l.url))}</span>
      </div>
      <div class="link-meta">
        <span class="clicks" title="Переходов">${ICONS.chart}${nf.format(l.clicks)}</span>
        <span class="time" title="${esc(new Date(l.created_at).toLocaleString("ru-RU"))}">${esc(timeAgo(l.created_at))}</span>
        <div class="row-actions">
          <button class="row-btn" data-copy="${esc(l.short_url)}" title="Копировать">${ICONS.copy}</button>
          <button class="row-btn del" data-del="${esc(l.code)}" title="Удалить">${ICONS.trash}</button>
        </div>
      </div>
    </li>`).join("");

  const isEmpty = links.length === 0;
  $("empty").classList.toggle("hidden", !isEmpty);
  $("empty-text").textContent = emptyMessage || (q ? "Ничего не найдено" : "Здесь появятся ваши ссылки");
}

/* ---------- События ---------- */

$("links").addEventListener("click", async (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  if (btn.dataset.copy) return copy(btn.dataset.copy);
  if (btn.dataset.del) {
    const code = btn.dataset.del;
    if (!confirm(`Удалить ссылку /${code}?`)) return;
    const r = await fetch(`/api/links/${encodeURIComponent(code)}`, { method: "DELETE", headers: headers() });
    if (!r.ok) return toast(await errorText(r));
    toast("Ссылка удалена");
    loadLinks();
  }
});

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("");
  localStorage.setItem("apiKey", keyInput.value);
  const btn = $("submit");
  btn.disabled = true; btn.classList.add("loading");
  try {
    const body = { url: $("url").value, alias: $("alias").value || null };
    const res = await fetch("/api/links", { method: "POST", headers: headers(), body: JSON.stringify(body) });
    if (!res.ok) return showError(await errorText(res));
    const link = await res.json();
    $("short").href = $("open").href = link.short_url;
    $("short").textContent = stripProto(link.short_url);
    $("copy").dataset.url = link.short_url;
    $("original").textContent = "→ " + link.url;
    const result = $("result");
    result.classList.add("hidden"); void result.offsetWidth; // перезапуск анимации
    result.classList.remove("hidden");
    $("url").value = ""; $("alias").value = "";
    loadLinks();
  } catch {
    showError("Сервер недоступен");
  } finally {
    btn.disabled = false; btn.classList.remove("loading");
  }
});

$("copy").addEventListener("click", () => copy($("copy").dataset.url));

$("toggle-alias").addEventListener("click", () => {
  const row = $("alias-row");
  const show = row.classList.contains("hidden");
  row.classList.toggle("hidden", !show);
  $("toggle-alias").classList.toggle("active", show);
  if (show) $("alias").focus(); else $("alias").value = "";
});

$("search").addEventListener("input", () => render());

keyInput.addEventListener("change", () => { localStorage.setItem("apiKey", keyInput.value); loadLinks(); });

$("theme").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("theme", next);
  document.querySelector('meta[name="theme-color"]').content = next === "dark" ? "#08090f" : "#f5f6fb";
});

/* ---------- Старт ---------- */

fetch("/health")
  .then((r) => r.json())
  .then((h) => $("key-row").classList.toggle("hidden", !h.auth_required))
  .finally(loadLinks);

// Обновляем относительное время и счётчики раз в минуту
setInterval(loadLinks, 60000);
