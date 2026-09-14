import { api, getToken, setToken } from "./api.js";

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

function toast(msg, type = "ok") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

let currentUser = null;

async function refreshMe() {
  const t = getToken();
  if (!t) {
    currentUser = null;
    return null;
  }
  try {
    currentUser = await api("/api/auth/me");
    return currentUser;
  } catch {
    setToken(null);
    currentUser = null;
    return null;
  }
}

function showView(name) {
  $$("[data-view]").forEach((v) => v.classList.add("hidden"));
  const el = document.querySelector(`[data-view="${name}"]`);
  if (el) el.classList.remove("hidden");
  $$(".tab").forEach((t) => t.classList.remove("active"));
  const tab = document.querySelector(`[data-tab="${name}"]`);
  if (tab) tab.classList.add("active");
}

async function loadFormations() {
  const list = $("#formations-list");
  list.innerHTML = "<p class='muted'>Chargement…</p>";
  try {
    const rows = await api("/api/formations");
    list.innerHTML = rows.length
      ? `<table><thead><tr><th>Code</th><th>Titre</th><th>Durée</th></tr></thead><tbody>${rows
          .map(
            (f) =>
              `<tr><td><code>${escapeHtml(f.code)}</code></td><td>${escapeHtml(f.title)}</td><td>${f.duration_semesters} sem.</td></tr>`
          )
          .join("")}</tbody></table>`
      : "<p>Aucune formation.</p>";
  } catch (e) {
    list.innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

async function loadHoraires() {
  const list = $("#horaires-list");
  const q = $("#horaire-filter")?.value?.trim() || "";
  list.innerHTML = "<p>Chargement…</p>";
  try {
    const qs = q ? `?q=${encodeURIComponent(q)}` : "";
    const rows = await api(`/api/horaires${qs}`);
    list.innerHTML = rows.length
      ? `<table><thead><tr><th>Module</th><th>Jour</th><th>Horaire</th><th>Salle</th></tr></thead><tbody>${rows
          .map(
            (h) =>
              `<tr><td>${escapeHtml(h.module_name)} <span class="badge">${escapeHtml(h.module_code)}</span></td><td>${escapeHtml(h.day_of_week)}</td><td>${h.start_time.slice(0, 5)}–${h.end_time.slice(0, 5)}</td><td>${escapeHtml(h.room || "—")}</td></tr>`
          )
          .join("")}</tbody></table>`
      : "<p>Aucun créneau.</p>";
  } catch (e) {
    list.innerHTML = `<p>${escapeHtml(e.message)}</p>`;
  }
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function appendChat(role, text) {
  const log = $("#chat-log");
  const div = document.createElement("div");
  div.className = `msg ${role === "user" ? "msg-user" : "msg-bot"}`;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function sendChat() {
  const input = $("#chat-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  appendChat("user", text);
  const recEl = $("#chat-recommendations");
  recEl.innerHTML = "";
  try {
    const res = await api("/api/chat/ask", { method: "POST", body: { message: text } });
    appendChat("bot", res.answer);
    let extra = "";
    if (res.sources?.length) {
      extra += `<div class="recommendations"><strong>Sources (RAG)</strong><ul>${res.sources
        .map((s) => `<li>${escapeHtml(s)}</li>`)
        .join("")}</ul></div>`;
    }
    if (res.recommendations?.length) {
      extra += `<div class="recommendations"><strong>Suggestions</strong><ul>${res.recommendations
        .map((r) => `<li>${escapeHtml(r)}</li>`)
        .join("")}</ul></div>`;
    }
    recEl.innerHTML = extra;
  } catch (e) {
    appendChat("bot", "Erreur : " + e.message);
    toast(e.message, "error");
  }
}

/* ——— Admin ——— */

async function loadAdminUsers() {
  const body = $("#admin-users-body");
  body.innerHTML = "";
  try {
    const users = await api("/api/admin/users");
    users.forEach((u) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${u.id}</td><td>${escapeHtml(u.email)}</td><td>${escapeHtml(u.full_name)}</td><td><span class="badge ${u.role === "admin" ? "badge-admin" : ""}">${u.role}</span></td><td>${u.is_active ? "oui" : "non"}</td><td></td>`;
      const td = tr.querySelector("td:last-child");
      const sel = document.createElement("select");
      [["student", "étudiant"], ["admin", "admin"]].forEach(([v, l]) => {
        const o = document.createElement("option");
        o.value = v;
        o.textContent = l;
        if (u.role === v) o.selected = true;
        sel.appendChild(o);
      });
      sel.addEventListener("change", async () => {
        try {
          await api(`/api/admin/users/${u.id}`, {
            method: "PATCH",
            body: { role: sel.value },
          });
          toast("Rôle mis à jour");
        } catch (e) {
          toast(e.message, "error");
        }
      });
      td.appendChild(sel);
      body.appendChild(tr);
    });
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadAdminStats() {
  const el = $("#admin-stats");
  try {
    const s = await api("/api/admin/stats/chat");
    const intents = Object.entries(s.by_intent || {})
      .map(([k, v]) => `${k}: ${v}`)
      .join(" · ");
    el.innerHTML = `<p>Messages total : <strong>${s.total_messages}</strong></p><p>7 derniers jours : <strong>${s.last_7_days}</strong></p><p>Par intention : ${escapeHtml(intents || "—")}</p>`;
  } catch (e) {
    el.textContent = e.message;
  }
}

async function reindexRag() {
  try {
    const r = await api("/api/admin/rag/reindex", { method: "POST" });
    toast(`RAG : ${r.indexed_chunks} passages indexés`);
  } catch (e) {
    toast(e.message, "error");
  }
}

async function submitFormation(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = {
    code: fd.get("code"),
    title: fd.get("title"),
    description: fd.get("description") || "",
    duration_semesters: parseInt(fd.get("duration_semesters"), 10) || 6,
  };
  try {
    await api("/api/formations", { method: "POST", body });
    toast("Formation créée");
    e.target.reset();
    loadFormations();
    loadAdminFormations();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function loadAdminFormations() {
  const sel = $("#horaire-formation-id");
  if (!sel) return;
  const rows = await api("/api/formations");
  sel.innerHTML = '<option value="">—</option>' + rows.map((f) => `<option value="${f.id}">${escapeHtml(f.code)}</option>`).join("");
}

async function submitHoraire(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const fid = fd.get("formation_id");
  const body = {
    module_code: fd.get("module_code"),
    module_name: fd.get("module_name"),
    day_of_week: fd.get("day_of_week"),
    start_time: fd.get("start_time") + ":00",
    end_time: fd.get("end_time") + ":00",
    room: fd.get("room") || "",
    teacher: fd.get("teacher") || "",
    formation_id: fid ? parseInt(fid, 10) : null,
  };
  try {
    await api("/api/horaires", { method: "POST", body });
    toast("Horaire ajouté");
    e.target.reset();
    loadHoraires();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function submitInfo(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const body = {
    category: fd.get("category"),
    title: fd.get("title"),
    content: fd.get("content"),
  };
  try {
    await api("/api/infos", { method: "POST", body });
    toast("Information publiée");
    e.target.reset();
  } catch (err) {
    toast(err.message, "error");
  }
}

function bindUI() {
  $("#btn-login")?.addEventListener("click", () => showView("login"));
  $("#btn-register")?.addEventListener("click", () => showView("register"));

  $("#form-login")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const res = await api("/api/auth/login", {
        method: "POST",
        body: { email: fd.get("email"), password: fd.get("password") },
      });
      setToken(res.access_token);
      await refreshMe();
      toast("Connexion réussie");
      showApp();
    } catch (err) {
      toast(err.message, "error");
    }
  });

  $("#form-register")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api("/api/auth/register", {
        method: "POST",
        body: {
          email: fd.get("email"),
          password: fd.get("password"),
          full_name: fd.get("full_name"),
        },
      });
      toast("Compte créé — connectez-vous");
      showView("login");
    } catch (err) {
      toast(err.message, "error");
    }
  });

  $("#btn-logout")?.addEventListener("click", () => {
    setToken(null);
    currentUser = null;
    updateHeader();
    showView("login");
    toast("Déconnecté");
  });

  $$(".tab").forEach((t) =>
    t.addEventListener("click", () => {
      const v = t.getAttribute("data-tab");
      if (v === "formations") loadFormations();
      if (v === "horaires") loadHoraires();
      if (v === "chat") $("#chat-input")?.focus();
      showView(v);
    })
  );

  $("#horaire-filter-btn")?.addEventListener("click", loadHoraires);
  $("#chat-send")?.addEventListener("click", sendChat);
  $("#chat-input")?.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      sendChat();
    }
  });

  $("#btn-admin")?.addEventListener("click", async () => {
    showView("admin");
    loadAdminUsers();
    loadAdminStats();
    await loadAdminFormations();
  });

  $("#admin-back")?.addEventListener("click", () => showView("formations"));

  $("#form-admin-formation")?.addEventListener("submit", submitFormation);
  $("#form-admin-horaire")?.addEventListener("submit", submitHoraire);
  $("#form-admin-info")?.addEventListener("submit", submitInfo);
  $("#admin-rag-reindex")?.addEventListener("click", reindexRag);
}

function updateHeader() {
  const pill = $("#user-pill");
  const adminBtn = $("#btn-admin");
  const btnLogin = $("#btn-login");
  const btnRegister = $("#btn-register");
  const btnLogout = $("#btn-logout");
  if (!pill) return;
  if (currentUser) {
    pill.textContent = `${currentUser.full_name} (${currentUser.email})`;
    pill.classList.remove("hidden");
    btnLogout?.classList.remove("hidden");
    btnLogin?.classList.add("hidden");
    btnRegister?.classList.add("hidden");
    adminBtn?.classList.toggle("hidden", currentUser.role !== "admin");
  } else {
    pill.textContent = "";
    pill.classList.add("hidden");
    btnLogout?.classList.add("hidden");
    btnLogin?.classList.remove("hidden");
    btnRegister?.classList.remove("hidden");
    adminBtn?.classList.add("hidden");
  }
}

function showApp() {
  updateHeader();
  showView("formations");
  loadFormations();
}

async function init() {
  bindUI();
  await refreshMe();
  if (currentUser) {
    showApp();
  } else {
    showView("login");
  }
}

init();
