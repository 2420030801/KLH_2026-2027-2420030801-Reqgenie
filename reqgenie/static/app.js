/* ReqGenie front end: plain JavaScript, no build step. */
mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral" });

const SAMPLE = [
  "We need an online shop where customers can search products and pay by UPI.",
  "Customers must be able to add items to a cart and track their orders.",
  "Admin must manage product stock.",
  "Customers could write reviews and ratings.",
].join("\n");

const $ = (id) => document.getElementById(id);
const state = { projectId: null, version: null };

function esc(value) {
  return String(value).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function say(text, isError = false) {
  const el = $("message");
  el.textContent = text;
  el.className = isError ? "error" : "";
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { const body = await res.json(); detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail); } catch (e) { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

function postJson(path, body) {
  return api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

/* ---------- rendering ---------- */

function renderStories(stories) {
  if (!stories.length) { $("tab-stories").innerHTML = '<p class="empty">No stories.</p>'; return; }
  $("tab-stories").innerHTML = stories.map((s) => `
    <article class="story">
      <div class="top"><span class="id">${esc(s.id)}</span>
        <span class="badge ${esc(s.priority.replace("'", ""))}">${esc(s.priority)}</span></div>
      <p>${esc(s.text)}</p>
      <ul>${s.criteria.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>
    </article>`).join("");
}

async function renderDiagrams(diagrams) {
  const titles = { use_case: "Use case diagram", class: "Class diagram", sequence: "Sequence diagram" };
  const box = $("tab-diagrams");
  box.innerHTML = "";
  let i = 0;
  for (const [key, title] of Object.entries(titles)) {
    const wrap = document.createElement("div");
    wrap.className = "diagram";
    const h = document.createElement("h3");
    h.textContent = title;
    wrap.appendChild(h);
    const holder = document.createElement("div");
    wrap.appendChild(holder);
    box.appendChild(wrap);
    try {
      const { svg } = await mermaid.render(`d${Date.now()}_${i++}`, diagrams[key]);
      holder.innerHTML = svg;
    } catch (err) {
      const pre = document.createElement("pre");
      pre.textContent = diagrams[key];
      holder.appendChild(pre);
    }
  }
}

function renderChanges(changes, summary) {
  const chips = Object.entries(summary)
    .map(([k, v]) => `<span class="badge ${k}">${esc(k)}: ${v}</span>`).join("");
  const items = changes.map((c) => `
    <div class="change">
      <span class="badge ${esc(c.status)}">${esc(c.status)}</span>
      <div>${esc(c.requirement)}</div>
      ${c.previous ? `<div class="prev">${esc(c.previous)}</div>` : ""}
      ${c.stories.length ? `<div class="ids">Stories: ${esc(c.stories.join(", "))}</div>` : ""}
    </div>`).join("");
  $("tab-changes").innerHTML = `<div class="summary">${chips}</div>${items}`;
}

function setExportLinks() {
  const base = `/api/projects/${state.projectId}/export`;
  $("export-md").href = `${base}?format=md&version=${state.version}`;
  $("export-csv").href = `${base}?format=csv&version=${state.version}`;
  $("export-md").hidden = false;
  $("export-csv").hidden = false;
}

async function showResult(res) {
  state.projectId = res.project_id;
  state.version = res.version;
  $("update").disabled = false;
  $("name").value = res.name;
  renderStories(res.stories);
  renderChanges(res.changes, res.summary);
  setExportLinks();
  await renderDiagrams(res.diagrams);
  await loadVersions();
  await loadProjects();
}

/* ---------- data loading ---------- */

async function loadProjects() {
  const list = await api("/api/projects");
  const select = $("projects");
  select.innerHTML = '<option value="">New project</option>' + list.map((p) =>
    `<option value="${p.id}" ${p.id === state.projectId ? "selected" : ""}>${esc(p.name)} (v${p.latest_version})</option>`).join("");
}

async function loadVersions() {
  const list = await api(`/api/projects/${state.projectId}/versions`);
  const select = $("versions");
  select.disabled = false;
  select.innerHTML = list.map((v) =>
    `<option value="${v.version}" ${v.version === state.version ? "selected" : ""}>Version ${v.version}</option>`).join("");
}

/* ---------- actions ---------- */

async function run(label, fn) {
  say(label + "...");
  try { await fn(); say("Done."); } catch (err) { say(err.message, true); }
}

$("generate").addEventListener("click", () => run("Generating", async () => {
  const name = $("name").value.trim() || "Untitled project";
  await showResult(await postJson("/api/projects", { name, text: $("text").value }));
}));

$("update").addEventListener("click", () => run("Updating", async () => {
  await showResult(await postJson(`/api/projects/${state.projectId}/update`, { text: $("text").value }));
}));

$("sample").addEventListener("click", () => { $("text").value = SAMPLE; if (!$("name").value) $("name").value = "Online shop"; });

$("projects").addEventListener("change", (e) => {
  const id = Number(e.target.value);
  if (!id) { state.projectId = null; state.version = null; $("update").disabled = true; return; }
  state.projectId = id;
  run("Loading", async () => {
    const res = await api(`/api/projects/${id}/versions`);
    const latest = res[res.length - 1].version;
    const data = await api(`/api/projects/${id}/versions/${latest}`);
    $("text").value = (await api(`/api/projects/${id}/versions/${latest}`)).requirements.join("\n");
    await showResult(data);
  });
});

$("versions").addEventListener("change", (e) => run("Loading version", async () => {
  const data = await api(`/api/projects/${state.projectId}/versions/${e.target.value}`);
  $("text").value = data.requirements.join("\n");
  await showResult(data);
}));

document.querySelectorAll(".tab").forEach((btn) => btn.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b === btn));
  for (const name of ["stories", "diagrams", "changes"]) $(`tab-${name}`).hidden = name !== btn.dataset.tab;
}));

loadProjects().catch(() => { /* first run: no projects yet */ });
