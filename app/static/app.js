const $ = (id) => document.getElementById(id);
const keyInput = $("api-key");
keyInput.value = localStorage.getItem("apiKey") || "";

function headers() {
  const h = { "Content-Type": "application/json" };
  if (keyInput.value) h["X-API-Key"] = keyInput.value;
  return h;
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
  } catch (_) {}
  return `Ошибка ${res.status}`;
}

async function loadLinks() {
  const res = await fetch("/api/links", { headers: headers() });
  const tbody = $("links");
  tbody.innerHTML = "";
  if (!res.ok) {
    $("empty").textContent = res.status === 401 ? "Введите API-ключ, чтобы увидеть ссылки." : await errorText(res);
    $("empty").classList.remove("hidden");
    return;
  }
  const links = await res.json();
  $("empty").textContent = "Пока нет ни одной ссылки.";
  $("empty").classList.toggle("hidden", links.length > 0);
  for (const link of links) {
    const tr = document.createElement("tr");

    const short = document.createElement("td");
    const a = document.createElement("a");
    a.href = link.short_url; a.target = "_blank"; a.rel = "noopener";
    a.textContent = link.short_url.replace(/^https?:\/\//, "");
    short.appendChild(a);

    const orig = document.createElement("td");
    orig.textContent = link.url; orig.title = link.url;

    const clicks = document.createElement("td");
    clicks.textContent = link.clicks;

    const actions = document.createElement("td");
    const del = document.createElement("button");
    del.className = "danger"; del.textContent = "✕"; del.title = "Удалить";
    del.onclick = async () => {
      if (!confirm(`Удалить ${link.short_url}?`)) return;
      const r = await fetch(`/api/links/${encodeURIComponent(link.code)}`, { method: "DELETE", headers: headers() });
      if (!r.ok) alert(await errorText(r));
      loadLinks();
    };
    actions.appendChild(del);

    tr.append(short, orig, clicks, actions);
    tbody.appendChild(tr);
  }
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("");
  localStorage.setItem("apiKey", keyInput.value);
  const body = { url: $("url").value, alias: $("alias").value || null };
  const res = await fetch("/api/links", { method: "POST", headers: headers(), body: JSON.stringify(body) });
  if (!res.ok) {
    showError(await errorText(res));
    return;
  }
  const link = await res.json();
  $("short").href = link.short_url;
  $("short").textContent = link.short_url;
  $("result").classList.remove("hidden");
  $("url").value = "";
  $("alias").value = "";
  loadLinks();
});

$("copy").addEventListener("click", async () => {
  const text = $("short").textContent;
  try {
    await navigator.clipboard.writeText(text);
  } catch (_) {
    // Clipboard API недоступен по http в локальной сети — запасной вариант
    const ta = document.createElement("textarea");
    ta.value = text; document.body.appendChild(ta); ta.select();
    document.execCommand("copy"); ta.remove();
  }
  $("copy").textContent = "Скопировано!";
  setTimeout(() => ($("copy").textContent = "Копировать"), 1500);
});

$("refresh").addEventListener("click", loadLinks);
keyInput.addEventListener("change", () => { localStorage.setItem("apiKey", keyInput.value); loadLinks(); });

fetch("/health").then((r) => r.json()).then((h) => {
  $("key-row").classList.toggle("hidden", !h.auth_required);
  loadLinks();
});
