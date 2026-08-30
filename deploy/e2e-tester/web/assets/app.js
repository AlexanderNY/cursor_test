const state = {
  sites: [],
  credentials: [],
  scenarios: [],
  runs: [],
  discoveries: [],
  selectedRunId: null,
  selectedDiscoveryId: null,
  discoveryPoll: null,
  pollTimer: null,
};

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 3500);
}

async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (res.status === 204) return null;
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const detail = data?.detail || data || res.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.tab === name);
  });
  document.querySelectorAll(".panel").forEach((p) => {
    p.classList.toggle("active", p.id === `tab-${name}`);
  });
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

document.getElementById("cred-type").addEventListener("change", (e) => {
  const isJwt = e.target.value === "jwt";
  document.getElementById("cred-password-fields").classList.toggle("hidden", isJwt);
  document.getElementById("cred-jwt-fields").classList.toggle("hidden", !isJwt);
});

function fillSiteSelects() {
  const opts = state.sites
    .map((s) => `<option value="${s.id}">#${s.id} ${s.name} · ${s.base_url}</option>`)
    .join("");
  const specs = [
    ["scenario-site-select", "— from JSON site / none —"],
    ["run-site-select", "— scenario / JSON default —"],
    ["upload-site-select", "— auto / none —"],
    ["builder-site-select", "— создать / обновить по имени —"],
    ["discovery-site-select", "— указать URL вручную —"],
  ];
  for (const [id, first] of specs) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.innerHTML = `<option value="">${first}</option>` + opts;
  }
}

function fillCredSelects() {
  const opts = state.credentials
    .map((c) => `<option value="${c.id}">${c.name} (${c.cred_type})</option>`)
    .join("");
  const specs = [
    ["scenario-cred-select", "— none —"],
    ["run-cred-select", "— scenario default —"],
    ["upload-cred-select", "— none —"],
    ["builder-cred-select", "— создать из полей ниже —"],
    ["discovery-cred-select", "— none —"],
  ];
  for (const [id, first] of specs) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.innerHTML = `<option value="">${first}</option>` + opts;
  }
}

function fillScenarioSelect() {
  const el = document.getElementById("run-scenario-select");
  el.innerHTML = state.scenarios
    .map(
      (s) =>
        `<option value="${s.id}">#${s.id} ${s.name} [v${s.schema_version || 1} ${s.format}]</option>`
    )
    .join("");
}

function renderResultTree(nodes, depth = 0) {
  if (!nodes || !nodes.length) return "";
  return nodes
    .map((n) => {
      const err = n.error ? `<div class="tree-error">${escapeHtml(n.error)}</div>` : "";
      const kids = renderResultTree(n.children || [], depth + 1);
      return `
        <div class="tree-node" style="margin-left:${depth * 14}px">
          <span class="tree-type">${escapeHtml(n.node_type)}</span>
          <span>${escapeHtml(n.title || n.key || "")}</span>
          <span class="badge ${n.status}">${escapeHtml(n.status)}</span>
          ${n.duration_ms != null ? `<span class="meta">${n.duration_ms} ms</span>` : ""}
          ${err}
          ${kids}
        </div>`;
    })
    .join("");
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function loadSites() {
  state.sites = await api("/api/sites");
  fillSiteSelects();
  const list = document.getElementById("site-list");
  list.innerHTML = state.sites
    .map(
      (s) => `
      <div class="item">
        <div>
          <strong>#${s.id} ${escapeHtml(s.name)}</strong>
          <div class="meta">${escapeHtml(s.base_url)}</div>
        </div>
        <div class="item-actions">
          <button type="button" class="danger" data-del-site="${s.id}">Delete</button>
        </div>
      </div>`
    )
    .join("");
  list.querySelectorAll("[data-del-site]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`/api/sites/${btn.dataset.delSite}`, { method: "DELETE" });
      toast("Site deleted");
      await loadSites();
    });
  });
}

async function loadCredentials() {
  state.credentials = await api("/api/credentials");
  fillCredSelects();
  const list = document.getElementById("cred-list");
  list.innerHTML = state.credentials
    .map(
      (c) => `
      <div class="item">
        <div>
          <strong>${escapeHtml(c.name)}</strong>
          <div class="meta">${c.cred_type}${c.meta ? " · " + escapeHtml(c.meta) : ""}</div>
        </div>
        <div class="item-actions">
          <button type="button" class="danger" data-del-cred="${c.id}">Delete</button>
        </div>
      </div>`
    )
    .join("");
  list.querySelectorAll("[data-del-cred]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`/api/credentials/${btn.dataset.delCred}`, { method: "DELETE" });
      toast("Credential deleted");
      await loadCredentials();
    });
  });
}

async function loadScenarios() {
  state.scenarios = await api("/api/scenarios");
  fillScenarioSelect();
  const list = document.getElementById("scenario-list");
  list.innerHTML = state.scenarios
    .map(
      (s) => `
      <div class="item">
        <div>
          <strong>#${s.id} ${escapeHtml(s.name)}</strong>
          <div class="meta">v${s.schema_version || 1} ${s.format}${
            s.site_id ? " · site #" + s.site_id : ""
          }${s.credentials_id ? " · cred #" + s.credentials_id : ""}</div>
        </div>
        <div class="item-actions">
          <button type="button" class="secondary" data-load-src="${s.id}">Edit source</button>
          <button type="button" class="danger" data-del-sc="${s.id}">Delete</button>
        </div>
      </div>`
    )
    .join("");
  list.querySelectorAll("[data-del-sc]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`/api/scenarios/${btn.dataset.delSc}`, { method: "DELETE" });
      toast("Scenario deleted");
      await loadScenarios();
    });
  });
  list.querySelectorAll("[data-load-src]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const s = state.scenarios.find((x) => String(x.id) === btn.dataset.loadSrc);
      if (!s) return;
      const form = document.getElementById("scenario-form");
      form.name.value = s.name;
      form.format.value = s.format;
      form.source.value = s.source;
      form.credentials_id.value = s.credentials_id || "";
      form.site_id.value = s.site_id || "";
      switchTab("scenarios");
    });
  });
}

function renderRunDetail(run) {
  const badge = document.getElementById("run-status");
  badge.textContent = run.status;
  badge.className = `badge ${run.status}`;

  const actions = document.getElementById("run-report-actions");
  const htmlLink = document.getElementById("run-report-html");
  const zipLink = document.getElementById("run-report-zip");
  if (run.status === "passed" || run.status === "failed") {
    actions.classList.remove("hidden");
    htmlLink.href = `/api/runs/${run.id}/report.html`;
    zipLink.href = `/api/runs/${run.id}/report.zip`;
  } else {
    actions.classList.add("hidden");
  }

  const sum = run.summary || {};
  document.getElementById("run-summary").innerHTML = `
    <div class="summary-card"><strong>${sum.sections_passed || 0}</strong>sec ok</div>
    <div class="summary-card"><strong>${sum.sections_failed || 0}</strong>sec fail</div>
    <div class="summary-card"><strong>${sum.actions_passed || 0}</strong>act ok</div>
    <div class="summary-card"><strong>${sum.actions_failed || 0}</strong>act fail</div>
    <div class="summary-card"><strong>${sum.actions_skipped || 0}</strong>skipped</div>
    <div class="summary-card meta">${escapeHtml(run.base_url_snapshot || "—")}</div>
  `;

  document.getElementById("run-tree").innerHTML =
    renderResultTree(run.results || []) || '<p class="muted">No tree results yet.</p>';

  const logs = document.getElementById("run-logs");
  logs.textContent = (run.events || [])
    .map((e) => `[${e.ts}] ${e.level.toUpperCase()} ${e.message}`)
    .join("\n");
  const arts = document.getElementById("run-artifacts");
  arts.innerHTML = (run.artifacts || [])
    .map(
      (a) => `
      <a href="${a.url}" target="_blank" rel="noopener">
        <img src="${a.url}" alt="${escapeHtml(a.step_name || a.path)}" />
      </a>`
    )
    .join("");
}

async function selectRun(runId) {
  state.selectedRunId = runId;
  const run = await api(`/api/runs/${runId}`);
  renderRunDetail(run);
  if (state.pollTimer) clearInterval(state.pollTimer);
  if (run.status === "queued" || run.status === "running") {
    state.pollTimer = setInterval(async () => {
      const fresh = await api(`/api/runs/${runId}`);
      renderRunDetail(fresh);
      if (fresh.status === "passed" || fresh.status === "failed") {
        clearInterval(state.pollTimer);
        state.pollTimer = null;
        await loadRuns();
      }
    }, 1500);
  }
}

async function loadRuns() {
  state.runs = await api("/api/runs");
  const list = document.getElementById("run-list");
  list.innerHTML = state.runs
    .map(
      (r) => `
      <div class="item">
        <div>
          <strong>#${r.id}</strong>
          <div class="meta">scenario ${r.scenario_id}${
            r.site_id ? " · site " + r.site_id : ""
          } · ${r.status}</div>
        </div>
        <div class="item-actions">
          <button type="button" class="secondary" data-open-run="${r.id}">Open</button>
        </div>
      </div>`
    )
    .join("");
  list.querySelectorAll("[data-open-run]").forEach((btn) => {
    btn.addEventListener("click", () => selectRun(Number(btn.dataset.openRun)));
  });
  if (state.selectedRunId) {
    const still = state.runs.find((r) => r.id === state.selectedRunId);
    if (still) renderRunDetail(still);
  }
}

document.getElementById("site-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  let meta = fd.get("meta");
  meta = meta && String(meta).trim() ? String(meta).trim() : null;
  if (meta) {
    try {
      meta = JSON.parse(meta);
    } catch {
      toast("Meta must be valid JSON");
      return;
    }
  }
  const body = {
    name: fd.get("name"),
    base_url: fd.get("base_url"),
    meta,
  };
  try {
    await api("/api/sites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    e.target.reset();
    toast("Site saved");
    await loadSites();
  } catch (err) {
    toast(err.message);
  }
});

document.getElementById("cred-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = {
    name: fd.get("name"),
    cred_type: fd.get("cred_type"),
    meta: fd.get("meta") || null,
  };
  if (body.cred_type === "password") {
    body.username = fd.get("username");
    body.password = fd.get("password");
  } else {
    body.access_token = fd.get("access_token");
    body.refresh_token = fd.get("refresh_token") || null;
  }
  try {
    await api("/api/credentials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    e.target.reset();
    document.getElementById("cred-type").dispatchEvent(new Event("change"));
    toast("Credential saved");
    await loadCredentials();
  } catch (err) {
    toast(err.message);
  }
});

document.getElementById("scenario-file").addEventListener("change", async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  const text = await file.text();
  document.getElementById("scenario-source").value = text;
  const form = document.getElementById("scenario-form");
  if (!form.name.value) form.name.value = file.name;
  const lower = file.name.toLowerCase();
  if (lower.endsWith(".py")) form.format.value = "playwright_py";
  else if (lower.endsWith(".json")) form.format.value = "json";
  else form.format.value = "yaml";
});

document.getElementById("scenario-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const credentialsId = fd.get("credentials_id");
  const siteId = fd.get("site_id");
  const body = {
    name: fd.get("name"),
    format: fd.get("format"),
    source: fd.get("source"),
    credentials_id: credentialsId ? Number(credentialsId) : null,
    site_id: siteId ? Number(siteId) : null,
  };
  try {
    await api("/api/scenarios", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    toast("Scenario saved");
    await loadScenarios();
  } catch (err) {
    toast(err.message);
  }
});

document.getElementById("upload-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const file = fd.get("file");
  if (!file || !file.size) {
    toast("Выберите файл");
    return;
  }
  const body = new FormData();
  body.append("file", file);
  if (fd.get("name")) body.append("name", fd.get("name"));
  if (fd.get("site_id")) body.append("site_id", fd.get("site_id"));
  if (fd.get("credentials_id")) body.append("credentials_id", fd.get("credentials_id"));
  try {
    const saved = await api("/api/scenarios/upload", { method: "POST", body });
    toast(`Uploaded #${saved.id} ${saved.name}`);
    e.target.reset();
    await loadScenarios();
    await loadSites();
    await loadCredentials();
  } catch (err) {
    toast(err.message);
  }
});

/* ---------- Builder ---------- */

const builderState = { pages: [] };

function emptyPage() {
  return { title: "", path: "", assert_text: "", buttons: [] };
}

function emptyButton() {
  return { text: "", selector: "", wait_ms: 1000, assert_text: "" };
}

function renderBuilderPages() {
  const root = document.getElementById("builder-pages");
  if (!builderState.pages.length) {
    builderState.pages.push(emptyPage());
  }
  root.innerHTML = builderState.pages
    .map((page, pi) => {
      const buttons = (page.buttons || [])
        .map(
          (btn, bi) => `
        <div class="btn-row" data-page="${pi}" data-btn="${bi}">
          <input data-f="text" placeholder="Текст кнопки" value="${escapeHtml(btn.text || "")}" />
          <input data-f="selector" placeholder="или CSS selector" value="${escapeHtml(btn.selector || "")}" />
          <input data-f="wait_ms" type="number" placeholder="wait ms" value="${btn.wait_ms ?? 1000}" />
          <input data-f="assert_text" placeholder="assert text после клика" value="${escapeHtml(btn.assert_text || "")}" />
          <button type="button" class="danger" data-rm-btn>×</button>
        </div>`
        )
        .join("");
      return `
      <div class="page-card" data-page="${pi}">
        <div class="page-grid">
          <input data-f="title" placeholder="Название раздела" value="${escapeHtml(page.title || "")}" />
          <input data-f="path" placeholder="/brands" value="${escapeHtml(page.path || "")}" />
          <input data-f="assert_text" placeholder="Текст на странице (assert)" value="${escapeHtml(page.assert_text || "")}" />
          <button type="button" class="danger" data-rm-page>Удалить раздел</button>
        </div>
        <div class="buttons-block">
          <div class="muted">Кнопки в разделе</div>
          ${buttons || '<div class="muted">Нет кнопок</div>'}
          <button type="button" class="secondary" data-add-btn>+ Кнопка</button>
        </div>
      </div>`;
    })
    .join("");

  root.querySelectorAll(".page-card").forEach((card) => {
    const pi = Number(card.dataset.page);
    card.querySelectorAll(".page-grid [data-f]").forEach((input) => {
      input.addEventListener("input", () => {
        builderState.pages[pi][input.dataset.f] = input.value;
      });
    });
    card.querySelector("[data-rm-page]")?.addEventListener("click", () => {
      builderState.pages.splice(pi, 1);
      renderBuilderPages();
    });
    card.querySelector("[data-add-btn]")?.addEventListener("click", () => {
      builderState.pages[pi].buttons = builderState.pages[pi].buttons || [];
      builderState.pages[pi].buttons.push(emptyButton());
      renderBuilderPages();
    });
    card.querySelectorAll(".btn-row").forEach((row) => {
      const bi = Number(row.dataset.btn);
      row.querySelectorAll("[data-f]").forEach((input) => {
        input.addEventListener("input", () => {
          const key = input.dataset.f;
          let val = input.value;
          if (key === "wait_ms") val = Number(val) || 0;
          builderState.pages[pi].buttons[bi][key] = val;
        });
      });
      row.querySelector("[data-rm-btn]")?.addEventListener("click", () => {
        builderState.pages[pi].buttons.splice(bi, 1);
        renderBuilderPages();
      });
    });
  });
}

function collectBuilderConfig() {
  const form = document.getElementById("builder-form");
  const fd = new FormData(form);
  const loginEnabled = document.getElementById("builder-login-enabled").checked;
  const credentialsId = fd.get("credentials_id");
  const siteId = fd.get("site_id");
  const username = String(fd.get("username") || "").trim();
  const password = String(fd.get("password") || "");
  const pages = builderState.pages
    .filter((p) => (p.path || "").trim())
    .map((p) => ({
      title: (p.title || p.path || "page").trim(),
      path: p.path.trim(),
      assert_text: (p.assert_text || "").trim() || null,
      screenshot: true,
      buttons: (p.buttons || [])
        .filter((b) => (b.text || "").trim() || (b.selector || "").trim())
        .map((b) => ({
          text: (b.text || "").trim() || null,
          selector: (b.selector || "").trim() || null,
          wait_ms: Number(b.wait_ms) || 1000,
          assert_text: (b.assert_text || "").trim() || null,
        })),
    }));

  return {
    name: String(fd.get("name") || "").trim(),
    site_name: String(fd.get("site_name") || "").trim() || null,
    base_url: String(fd.get("base_url") || "").trim(),
    site_id: siteId ? Number(siteId) : null,
    credentials_id: credentialsId ? Number(credentialsId) : null,
    create_credential: !credentialsId && !!username && !!password,
    credential_name: String(fd.get("credential_name") || "").trim() || null,
    username: username || null,
    password: password || null,
    timeout_ms: Number(fd.get("timeout_ms")) || 30000,
    login: {
      enabled: loginEnabled,
      path: String(fd.get("login_path") || "/sign-in"),
      username_selector: String(fd.get("user_sel") || ""),
      password_selector: String(fd.get("pass_sel") || ""),
      submit_selector: String(fd.get("submit_sel") || ""),
      success_url_contains: String(fd.get("success_url") || "").trim() || null,
      success_text: String(fd.get("success_text") || "").trim() || null,
    },
    pages,
  };
}

document.getElementById("builder-add-page").addEventListener("click", () => {
  builderState.pages.push(emptyPage());
  renderBuilderPages();
});

document.getElementById("builder-login-enabled").addEventListener("change", (e) => {
  document.getElementById("builder-login-fields").classList.toggle("hidden", !e.target.checked);
});

document.getElementById("builder-preview").addEventListener("click", async () => {
  try {
    const cfg = collectBuilderConfig();
    const res = await api("/api/scenarios/preview-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cfg),
    });
    document.getElementById("builder-preview-source").value = res.source;
    toast("Preview ready");
  } catch (err) {
    toast(err.message);
  }
});

document.getElementById("builder-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const cfg = collectBuilderConfig();
    if (!cfg.name || !cfg.base_url) {
      toast("Укажите имя и base URL");
      return;
    }
    if (cfg.login.enabled && !cfg.credentials_id && !(cfg.username && cfg.password)) {
      toast("Нужен credential или username/password");
      return;
    }
    const saved = await api("/api/scenarios/from-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cfg),
    });
    document.getElementById("builder-preview-source").value = saved.source;
    toast(`Scenario #${saved.id} saved`);
    await loadSites();
    await loadCredentials();
    await loadScenarios();
  } catch (err) {
    toast(err.message);
  }
});

/* ---------- Discovery ---------- */

function discoveryFilters() {
  return {
    link: document.getElementById("filter-link")?.checked !== false,
    nav: document.getElementById("filter-nav")?.checked !== false,
    button: document.getElementById("filter-button")?.checked !== false,
    input: document.getElementById("filter-input")?.checked !== false,
  };
}

function renderDiscoveryDetail(disc) {
  const badge = document.getElementById("discovery-status");
  badge.textContent = disc.status;
  badge.className = `badge ${disc.status === "completed" ? "passed" : disc.status === "failed" ? "failed" : "running"}`;

  const sum = disc.summary || {};
  document.getElementById("discovery-summary").innerHTML = `
    <div class="summary-card"><strong>${sum.pages_visited || 0}</strong>pages</div>
    <div class="summary-card"><strong>${sum.links || 0}</strong>links</div>
    <div class="summary-card"><strong>${sum.buttons || 0}</strong>buttons</div>
    <div class="summary-card"><strong>${sum.items || (disc.items || []).length}</strong>items</div>
    <div class="summary-card meta">${escapeHtml(disc.base_url || "")}</div>
    ${disc.error_summary ? `<div class="summary-card" style="color:var(--fail)">${escapeHtml(disc.error_summary)}</div>` : ""}
  `;

  const actions = document.getElementById("discovery-actions");
  const filters = document.getElementById("discovery-filters");
  const done = disc.status === "completed" || disc.status === "failed";
  actions.style.display = done ? "flex" : "none";
  filters.style.display = done ? "flex" : "none";

  const f = discoveryFilters();
  const items = (disc.items || []).filter((it) => f[it.kind] !== false);
  const box = document.getElementById("discovery-items");
  box.innerHTML = items
    .map(
      (it) => `
    <label class="disc-item">
      <input type="checkbox" data-item-id="${it.id}" ${it.selected ? "checked" : ""} />
      <span class="badge">${escapeHtml(it.kind)}</span>
      <span class="disc-label">${escapeHtml(it.label || it.text || it.path || it.selector || "")}</span>
      <span class="meta">${escapeHtml(it.path || it.page_path || "")}</span>
    </label>`
    )
    .join("") || '<p class="muted">Нет элементов (ещё идёт обход или пусто).</p>';

  box.querySelectorAll("input[data-item-id]").forEach((cb) => {
    cb.addEventListener("change", async () => {
      try {
        await api(`/api/discoveries/${disc.id}/select`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ item_ids: [Number(cb.dataset.itemId)], selected: cb.checked }),
        });
      } catch (err) {
        toast(err.message);
      }
    });
  });
}

async function selectDiscovery(id) {
  state.selectedDiscoveryId = id;
  const disc = await api(`/api/discoveries/${id}`);
  renderDiscoveryDetail(disc);
  if (state.discoveryPoll) clearInterval(state.discoveryPoll);
  if (disc.status === "queued" || disc.status === "running") {
    state.discoveryPoll = setInterval(async () => {
      const fresh = await api(`/api/discoveries/${id}`);
      renderDiscoveryDetail(fresh);
      if (fresh.status === "completed" || fresh.status === "failed") {
        clearInterval(state.discoveryPoll);
        state.discoveryPoll = null;
        await loadDiscoveries();
      }
    }, 2000);
  }
}

async function loadDiscoveries() {
  state.discoveries = await api("/api/discoveries");
  const list = document.getElementById("discovery-list");
  list.innerHTML = state.discoveries
    .map(
      (d) => `
      <div class="item">
        <div>
          <strong>#${d.id}</strong>
          <div class="meta">${escapeHtml(d.base_url)} · ${d.status}</div>
        </div>
        <div class="item-actions">
          <button type="button" class="secondary" data-open-disc="${d.id}">Open</button>
          <button type="button" class="danger" data-del-disc="${d.id}">Del</button>
        </div>
      </div>`
    )
    .join("");
  list.querySelectorAll("[data-open-disc]").forEach((btn) => {
    btn.addEventListener("click", () => selectDiscovery(Number(btn.dataset.openDisc)));
  });
  list.querySelectorAll("[data-del-disc]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`/api/discoveries/${btn.dataset.delDisc}`, { method: "DELETE" });
      toast("Discovery deleted");
      await loadDiscoveries();
    });
  });
}

document.getElementById("discovery-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const siteId = fd.get("site_id");
  const credId = fd.get("credentials_id");
  const baseUrl = String(fd.get("base_url") || "").trim();
  const body = {
    site_id: siteId ? Number(siteId) : null,
    credentials_id: credId ? Number(credId) : null,
    base_url: baseUrl || null,
    max_pages: Number(fd.get("max_pages")) || 40,
    max_depth: Number(fd.get("max_depth")) || 3,
    same_origin_only: true,
    do_login: document.getElementById("discovery-do-login").checked,
  };
  if (!body.site_id && !body.base_url) {
    toast("Укажите site или base URL");
    return;
  }
  try {
    const disc = await api("/api/discoveries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    toast(`Discovery #${disc.id} queued`);
    await loadDiscoveries();
    await selectDiscovery(disc.id);
  } catch (err) {
    toast(err.message);
  }
});

["filter-link", "filter-nav", "filter-button", "filter-input"].forEach((id) => {
  document.getElementById(id)?.addEventListener("change", async () => {
    if (!state.selectedDiscoveryId) return;
    const disc = await api(`/api/discoveries/${state.selectedDiscoveryId}`);
    renderDiscoveryDetail(disc);
  });
});

document.getElementById("discovery-select-all").addEventListener("click", async () => {
  if (!state.selectedDiscoveryId) return;
  const disc = await api(`/api/discoveries/${state.selectedDiscoveryId}/select-all`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected: true, item_ids: [] }),
  });
  renderDiscoveryDetail(disc);
});

document.getElementById("discovery-select-none").addEventListener("click", async () => {
  if (!state.selectedDiscoveryId) return;
  const disc = await api(`/api/discoveries/${state.selectedDiscoveryId}/select-all`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected: false, item_ids: [] }),
  });
  renderDiscoveryDetail(disc);
});

document.getElementById("discovery-to-builder").addEventListener("click", async () => {
  if (!state.selectedDiscoveryId) return;
  try {
    const cfg = await api(
      `/api/discoveries/${state.selectedDiscoveryId}/builder-config?selected_only=true`
    );
    const form = document.getElementById("builder-form");
    form.name.value = cfg.name || `discovery_${state.selectedDiscoveryId}`;
    form.base_url.value = cfg.base_url || "";
    if (cfg.site_id) form.site_id.value = String(cfg.site_id);
    if (cfg.credentials_id) form.credentials_id.value = String(cfg.credentials_id);
    document.getElementById("builder-login-enabled").checked = !!(cfg.login && cfg.login.enabled);
    document.getElementById("builder-login-fields").classList.toggle(
      "hidden",
      !document.getElementById("builder-login-enabled").checked
    );
    builderState.pages = (cfg.pages || []).map((p) => ({
      title: p.title || "",
      path: p.path || "",
      assert_text: p.assert_text || "",
      buttons: (p.buttons || []).map((b) => ({
        text: b.text || "",
        selector: b.selector || "",
        wait_ms: b.wait_ms || 1000,
        assert_text: b.assert_text || "",
      })),
    }));
    if (!builderState.pages.length) builderState.pages.push(emptyPage());
    renderBuilderPages();
    switchTab("builder");
    toast("Конфиг перенесён в Builder");
  } catch (err) {
    toast(err.message);
  }
});

document.getElementById("discovery-to-scenario").addEventListener("click", async () => {
  if (!state.selectedDiscoveryId) return;
  const name = prompt("Имя сценария", `discovery_${state.selectedDiscoveryId}_smoke`);
  if (!name) return;
  try {
    const saved = await api(`/api/discoveries/${state.selectedDiscoveryId}/to-scenario`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, include_login: true }),
    });
    toast(`Scenario #${saved.id} created`);
    await loadScenarios();
    switchTab("scenarios");
  } catch (err) {
    toast(err.message);
  }
});

document.getElementById("run-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const credentialsId = fd.get("credentials_id");
  const siteId = fd.get("site_id");
  const baseUrl = fd.get("base_url");
  const body = {
    scenario_id: Number(fd.get("scenario_id")),
    credentials_id: credentialsId ? Number(credentialsId) : null,
    site_id: siteId ? Number(siteId) : null,
    base_url: baseUrl && String(baseUrl).trim() ? String(baseUrl).trim() : null,
  };
  try {
    const run = await api("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    toast(`Run #${run.id} queued`);
    await loadRuns();
    await selectRun(run.id);
    switchTab("runs");
  } catch (err) {
    toast(err.message);
  }
});

async function boot() {
  try {
    const health = await api("/api/health");
    document.getElementById("health-line").textContent =
      `Default UI target: ${health.target_ui_url} · API: ${health.target_api_url}`;
  } catch {
    document.getElementById("health-line").textContent = "API unavailable";
  }
  renderBuilderPages();
  await loadSites();
  await loadCredentials();
  await loadScenarios();
  await loadRuns();
  await loadDiscoveries();
}

boot();
