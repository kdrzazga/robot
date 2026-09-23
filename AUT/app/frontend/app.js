/* ============================================================
   CONFIG – matches the two FastAPI services
   Customer DB (app/main.py, port 8000):
     POST /token                form username, password
                                -> {access_token, token_type}; role is in the JWT
     GET  /persons              -> [ {id, name, last_name, tax_id, address: {...}}, ... ]
     PUT  /persons/{id}         body {name, last_name, tax_id, address_id}  (admin only)
     GET  /addresses            -> [ {id, street, city, zip_code, country}, ... ]
     PUT  /addresses/{id}       body = full row  (admin only)
   TaxInformation (tax_app/main.py, port 8001) – accepts the same token:
     GET  /taxes                -> [ {id, name, last_name, tax_id, tax_amount}, ... ]
     PUT  /taxes/{id}           body = full row  (admin only)
   The page may be served from anywhere (backend /ui/, disk, PyCharm's
   built-in server); both services allow CORS, so always use full URLs.
   Open index.html?mock=1 to run without a backend.
   ============================================================ */
const CONFIG = {
  services: {
    customers: "http://127.0.0.1:8000",
    tax: "http://127.0.0.1:8001",
  },
  endpoints: {
    login:   { service: "customers", path: "/token" },
    person:  { service: "customers", path: "/persons" },
    address: { service: "customers", path: "/addresses" },
    tax:     { service: "tax",       path: "/taxes" },
  },
  idField: "id",
  useMock: new URLSearchParams(location.search).has("mock"),
};

/* Turns an API record into a flat, editable table row. */
const TO_ROW = {
  person: ({ address, ...person }) => ({ ...person, address_id: address ? address.id : person.address_id }),
  address: address => address,
  tax: tax => tax,
};

/* Reads the claims from a JWT without verifying it (the server does that). */
function decodeJwt(token) {
  const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(atob(payload));
}

/* ---------- Mock backend (only used with ?mock=1) ---------- */
const MOCK = {
  users: { admin: { password: "admin", role: "admin" }, user: { password: "user", role: "user" } },
  person: [
    { id: 1, name: "John", last_name: "Smith", tax_id: "TAX-1001", address_id: 1 },
    { id: 2, name: "Anna", last_name: "Kowalska", tax_id: "TAX-1002", address_id: 2 },
  ],
  address: [
    { id: 1, street: "1 Main St", city: "Warsaw", zip_code: "00-001", country: "Poland" },
    { id: 2, street: "22 Oak Ave", city: "Krakow", zip_code: "30-002", country: "Poland" },
  ],
  tax: [
    { id: 1, name: "John", last_name: "Smith", tax_id: "TAX-1001", tax_amount: 1250 },
    { id: 2, name: "Anna", last_name: "Kowalska", tax_id: "TAX-1002", tax_amount: 980.5 },
  ],
};
async function mockRequest(path, { method = "GET", body } = {}) {
  await new Promise(r => setTimeout(r, 150));
  if (path === CONFIG.endpoints.login.path) {
    const form = new URLSearchParams(body);
    const u = MOCK.users[form.get("username")];
    if (!u || u.password !== form.get("password")) throw new ApiError(401, "Wrong username or password.");
    const claims = btoa(JSON.stringify({ sub: form.get("username"), role: u.role }));
    return { access_token: "mock." + claims + ".mock", token_type: "bearer" };
  }
  const data = body ? JSON.parse(body) : null;
  for (const key of ["person", "address", "tax"]) {
    const base = CONFIG.endpoints[key].path;
    if (path === base && method === "GET") return structuredClone(MOCK[key]);
    if (path.startsWith(base + "/") && method === "PUT") {
      if (state.role !== "admin") throw new ApiError(403, "Only admins can edit.");
      const id = path.slice(base.length + 1);
      const i = MOCK[key].findIndex(r => String(r[CONFIG.idField]) === id);
      if (i < 0) throw new ApiError(404, "Row not found.");
      MOCK[key][i] = data;
      return data;
    }
  }
  throw new ApiError(404, "Unknown endpoint " + path);
}

/* ---------- API layer ---------- */
class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
/* Calls `endpoint` (an entry of CONFIG.endpoints), optionally with a sub-path like "/42". */
async function api(endpoint, subPath = "", options = {}) {
  const path = endpoint.path + subPath;
  if (CONFIG.useMock) return mockRequest(path, options);
  const serviceUrl = CONFIG.services[endpoint.service];
  // URLSearchParams bodies get their form content type from fetch itself.
  const headers = typeof options.body === "string" ? { "Content-Type": "application/json" } : {};
  if (state.token) headers.Authorization = "Bearer " + state.token;
  let res;
  try {
    res = await fetch(serviceUrl + path, { ...options, headers });
  } catch {
    throw new ApiError(0, "Can't reach the server at " + serviceUrl + ".");
  }
  const text = await res.text();
  let payload = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    throw new ApiError(res.status, "Unexpected non-JSON response from " + res.url + " (HTTP " + res.status + ").");
  }
  if (!res.ok) {
    let msg = (payload && (payload.message || payload.detail || payload.error)) || res.statusText;
    // FastAPI validation errors (422) come as a list of {loc, msg}.
    if (Array.isArray(msg)) msg = msg.map(e => e.loc.at(-1) + ": " + e.msg).join("; ");
    throw new ApiError(res.status, msg);
  }
  return payload;
}

/* ---------- State ---------- */
const state = {
  token: null, role: null, username: null,
  tabs: {
    person:  { rows: [], dirty: new Map() },
    address: { rows: [], dirty: new Map() },
    tax:     { rows: [], dirty: new Map() },
  },
};
const isAdmin = () => state.role === "admin";
const $ = id => document.getElementById(id);

/* ---------- Login ---------- */
const dialog = $("login-dialog");
dialog.addEventListener("cancel", e => e.preventDefault()); // can't close with Esc

function showLogin(message = "") {
  $("login-form").reset();
  $("login-error").textContent = message;
  $("mock-note").hidden = !CONFIG.useMock;
  $("app").hidden = true;
  $("session").hidden = true;
  if (!dialog.open) dialog.showModal();
  $("username").focus();
}

$("login-form").addEventListener("submit", async e => {
  e.preventDefault();
  const username = $("username").value.trim();
  const password = $("password").value;
  if (!username || !password) {
    $("login-error").textContent = "Enter your username and password.";
    return;
  }
  $("login-btn").disabled = true;
  $("login-error").textContent = "";
  try {
    const res = await api(CONFIG.endpoints.login, "", {
      method: "POST", body: new URLSearchParams({ username, password }),
    });
    state.token = res.access_token;
    state.role = String(decodeJwt(res.access_token).role || "user").toLowerCase();
    state.username = username;
    dialog.close();
    startSession();
  } catch (err) {
    $("login-error").textContent = err.status === 401 ? "Wrong username or password." : err.message;
  } finally {
    $("login-btn").disabled = false;
  }
});

function startSession() {
  $("current-user").textContent = state.username;
  $("current-role").textContent = state.role;
  $("current-role").dataset.role = state.role;
  $("session").hidden = false;
  document.querySelectorAll(".admin-only").forEach(el => (el.hidden = !isAdmin()));
  $("app").hidden = false;
  selectTab("person");
  tabs.forEach(loadTab);
}

$("logout-btn").addEventListener("click", () => logout());
function logout(message) {
  state.token = state.role = state.username = null;
  for (const [name, t] of Object.entries(state.tabs)) {
    t.rows = [];
    t.dirty.clear();
    $(name + "-table").innerHTML = "";
  }
  showLogin(message);
}

/* ---------- Tabs ---------- */
const tabs = ["person", "address", "tax"];
function selectTab(name) {
  for (const t of tabs) {
    const active = t === name;
    $("tab-" + t).setAttribute("aria-selected", active);
    $("tab-" + t).tabIndex = active ? 0 : -1;
    $("panel-" + t).hidden = !active;
  }
}
tabs.forEach((t, i) => {
  $("tab-" + t).addEventListener("click", () => selectTab(t));
  $("tab-" + t).addEventListener("keydown", e => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
    selectTab(next);
    $("tab-" + next).focus();
  });
  $(t + "-reload").addEventListener("click", () => loadTab(t));
  $(t + "-save").addEventListener("click", () => saveTab(t));
});

/* ---------- Data ---------- */
function setStatus(tab, text, kind = "") {
  const el = $(tab + "-status");
  el.textContent = text;
  el.className = "status " + kind;
}

async function loadTab(tab) {
  const t = state.tabs[tab];
  if (t.dirty.size && !confirm("Discard unsaved changes in " + tab + "?")) return;
  setStatus(tab, "Loading…");
  try {
    t.rows = (await api(CONFIG.endpoints[tab])).map(TO_ROW[tab]);
    t.dirty.clear();
    renderTable(tab);
    setStatus(tab, t.rows.length + " rows");
  } catch (err) {
    if (err.status === 401) return logout("Your session expired. Log in again.");
    setStatus(tab, err.message, "error");
  }
}

function renderTable(tab) {
  const { rows } = state.tabs[tab];
  const table = $(tab + "-table");
  table.innerHTML = "";
  updateSaveButton(tab);

  if (!rows.length) {
    table.innerHTML = '<tbody><tr><td class="empty">No records found.</td></tr></tbody>';
    return;
  }

  const idField = CONFIG.idField;
  const columns = [idField, ...new Set(rows.flatMap(r => Object.keys(r)).filter(k => k !== idField))];

  const thead = table.createTHead().insertRow();
  columns.forEach(c => {
    const th = document.createElement("th");
    th.textContent = c;
    th.scope = "col";
    thead.appendChild(th);
  });

  const tbody = table.createTBody();
  rows.forEach(row => {
    const tr = tbody.insertRow();
    tr.dataset.id = row[idField];
    columns.forEach(col => {
      const td = tr.insertCell();
      td.dataset.field = col;
      td.textContent = row[col] ?? "";
      const editable = isAdmin() && col !== idField;
      td.setAttribute("contenteditable", editable ? "true" : "false");
      if (editable) {
        td.addEventListener("input", () => onCellEdit(tab, row, col, td));
        td.addEventListener("keydown", e => {
          if (e.key === "Enter") { e.preventDefault(); td.blur(); }
          if (e.key === "Escape") { td.textContent = row[col] ?? ""; onCellEdit(tab, row, col, td); td.blur(); }
        });
      }
    });
  });
}

function onCellEdit(tab, row, col, td) {
  const dirty = state.tabs[tab].dirty;
  const id = row[CONFIG.idField];
  const original = String(row[col] ?? "");
  const value = td.textContent;
  const changes = dirty.get(id) || {};
  if (value === original) delete changes[col]; else changes[col] = coerce(value, row[col]);
  td.classList.toggle("changed", value !== original);
  if (Object.keys(changes).length) dirty.set(id, changes); else dirty.delete(id);
  updateSaveButton(tab);
  setStatus(tab, dirty.size ? dirty.size + " row(s) changed" : "");
}

function coerce(text, original) {
  if (typeof original === "number" && text.trim() !== "" && !isNaN(Number(text))) return Number(text);
  if (typeof original === "boolean") return text.trim().toLowerCase() === "true";
  return text;
}

function updateSaveButton(tab) {
  $(tab + "-save").disabled = !isAdmin() || state.tabs[tab].dirty.size === 0;
}

async function saveTab(tab) {
  if (!isAdmin()) return;
  const t = state.tabs[tab];
  $(tab + "-save").disabled = true;
  setStatus(tab, "Saving…");
  const failed = [];
  for (const [id, changes] of t.dirty) {
    const row = t.rows.find(r => r[CONFIG.idField] === id);
    try {
      await api(CONFIG.endpoints[tab], "/" + encodeURIComponent(id), {
        method: "PUT", body: JSON.stringify({ ...row, ...changes }),
      });
    } catch (err) {
      if (err.status === 401) return logout("Your session expired. Log in again.");
      failed.push(id + " (" + err.message + ")");
    }
  }
  if (failed.length) {
    setStatus(tab, "Not saved: row " + failed.join(", "), "error");
    updateSaveButton(tab);
    return;
  }
  t.dirty.clear();
  await loadTab(tab);
  setStatus(tab, "Changes saved", "ok");
}

/* ---------- Start ---------- */
showLogin();
