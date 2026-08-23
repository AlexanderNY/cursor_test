const state = {
  credentials: [],
  scenarios: [],
  runs: [],
  selectedRunId: null,
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

function fillCredSelects() {
  const opts = state.credentials
    .map((c) => `<option value="${c.id}">${c.name} (${c.cred_type})</option>`)
    .join("");
  for (const id of ["scenario-cred-select", "run-cred-select"]) {
    const el = document.getElementById(id);
    const first = id === "run-cred-select" ? "— scenario default —" : "— none —";
    el.innerHTML = `<option value="">${first}</option>` + opts;
  }
}

function fillScenarioSelect() {
  const el = document.getElementById("run-scenario-select");
  el.innerHTML = state.scenarios
    .map((s) => `<option value="${s.id}">#${s.id} ${s.name} [${s.format}]</option>`)
    .join("");
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
          <strong>${c.name}</strong>
          <div class="meta">${c.cred_type}${c.meta ? " · " + c.meta : ""}</div>
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
          <strong>#${s.id} ${s.name}</strong>
          <div class="meta">${s.format}${s.credentials_id ? " · cred #" + s.credentials_id : ""}</div>
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
      switchTab("scenarios");
    });
  });
}

function renderRunDetail(run) {
  const badge = document.getElementById("run-status");
  badge.textContent = run.status;
  badge.className = `badge ${run.status}`;
  const logs = document.getElementById("run-logs");
  logs.textContent = (run.events || [])
    .map((e) => `[${e.ts}] ${e.level.toUpperCase()} ${e.message}`)
    .join("\n");
  const arts = document.getElementById("run-artifacts");
  arts.innerHTML = (run.artifacts || [])
    .map(
      (a) => `
      <a href="${a.url}" target="_blank" rel="noopener">
        <img src="${a.url}" alt="${a.step_name || a.path}" />
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
          <div class="meta">scenario ${r.scenario_id} · ${r.status}</div>
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
  const body = {
    name: fd.get("name"),
    format: fd.get("format"),
    source: fd.get("source"),
    credentials_id: credentialsId ? Number(credentialsId) : null,
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

document.getElementById("run-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const credentialsId = fd.get("credentials_id");
  const body = {
    scenario_id: Number(fd.get("scenario_id")),
    credentials_id: credentialsId ? Number(credentialsId) : null,
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
      `UI target: ${health.target_ui_url} · API: ${health.target_api_url}`;
  } catch {
    document.getElementById("health-line").textContent = "API unavailable";
  }
  await loadCredentials();
  await loadScenarios();
  await loadRuns();
}

boot();
