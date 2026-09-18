"use strict";
const $ = (id) => document.getElementById(id);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (x) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        x
      ],
  );
const needs = {
  water: "Su",
  food: "Gıda",
  shelter: "Barınma",
  diapers: "Bebek bezi",
  other: "Diğer",
};
const statuses = {
  open: "Açık",
  in_progress: "İşlemde",
  fulfilled: "Karşılandı",
};
const languages = { tr: "Türkçe", en: "İngilizce", el: "Yunanca" };
const flagLabels = {
  quantity_conflict: "Miktarlar çelişiyor",
  unit_mismatch_or_unknown: "Birimler farklı veya eksik",
  unknown_event_time: "Olay zamanı eksik",
  possible_repost: "Eski mesajın tekrarı olabilir",
  fulfilled_need_requires_review: "Karşılanmış ihtiyaç: tekrar kontrol et",
};
const actionLabels = {
  event_created: "İhtiyaç kaydı oluşturuldu",
  report_linked: "Rapor bağlandı",
  report_split: "Rapor ayrı bir kayda taşındı",
  report_removed_by_split: "Rapor bu kayıttan ayrıldı",
  status_changed: "İhtiyaç durumu güncellendi",
};
const state = {
  token: "",
  epoch: 0,
  view: 0,
  tab: "reports",
  reports: [],
  events: [],
  selected: null,
  event: null,
  busy: false,
};
const date = (value) =>
  value
    ? new Intl.DateTimeFormat("tr-TR", {
        dateStyle: "short",
        timeStyle: "short",
      }).format(new Date(value))
    : "Bilinmiyor";
const badge = (status) =>
  `<span class="badge ${esc(status)}">${esc(statuses[status] || status)}</span>`;
const empty = (title, text) =>
  `<div class="empty"><div class="empty-symbol" aria-hidden="true">◎</div><h2>${esc(title)}</h2><p>${esc(text)}</p></div>`;
function notice(text, error = false) {
  $("notice").textContent = text;
  $("notice").className = error ? "error" : "";
  $("notice").hidden = false;
}
function clearSession() {
  state.epoch++;
  state.view++;
  state.token = "";
  state.reports = [];
  state.events = [];
  state.selected = null;
  state.event = null;
  $("token").value = "";
  $("dashboard").hidden = true;
  $("logout").hidden = true;
  $("login-view").hidden = false;
  $("record-list").replaceChildren();
  $("detail").replaceChildren();
  $("report-dialog").close();
  $("report-form").reset();
}
async function api(path, method = "GET", body) {
  const epoch = state.epoch;
  const res = await fetch(path, {
    method,
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${state.token}`,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (epoch !== state.epoch) throw new Error("Oturum değişti.");
  const data = await res.json();
  if (res.status === 401) {
    clearSession();
    throw new Error(
      "Erişim anahtarı geçersiz veya oturum sona erdi. Yeniden giriş yap.",
    );
  }
  if (!res.ok) {
    const known = {
      "Report already linked":
        "Bu rapor başka bir işlemle bağlanmış. Listeyi yenile.",
      "Event changed; refresh before deciding":
        "Kayıt başka bir işlemle güncellendi. Yenile ve kararını tekrar kontrol et.",
      "Quantity and unit must be supplied together":
        "Miktar ve birimi birlikte doldur.",
      "Reported time must not be in the future":
        "Olay zamanı gelecekte olamaz.",
      "Evidence report must be linked to this event":
        "Seçilen kanıt artık bu kayda bağlı değil. Listeyi yenile.",
      "Record not found": "Kayıt bulunamadı. Listeyi yenile.",
    };
    throw new Error(
      known[data.detail] ||
        (res.status === 422
          ? "Alanları kontrol et. Zorunlu alanları doldur; miktar ve birimi birlikte gir."
          : `İşlem tamamlanamadı (${res.status}). Listeyi yenileyip tekrar dene.`),
    );
  }
  return data;
}
function lock(on) {
  state.busy = on;
  $("workspace").setAttribute("aria-busy", String(on));
  document.querySelectorAll("button").forEach((b) => {
    if (on) {
      b.dataset.disabledBefore = String(b.disabled);
      b.disabled = true;
    } else {
      b.disabled = b.dataset.disabledBefore === "true";
      delete b.dataset.disabledBefore;
    }
  });
}
async function run(fn, errorId = null) {
  if (state.busy) return;
  lock(true);
  try {
    await fn();
  } catch (e) {
    const message =
      e instanceof TypeError
        ? "Sunucuya ulaşılamadı. Bağlantını kontrol edip tekrar dene."
        : e.message;
    if (errorId && $("report-dialog").open) {
      $(errorId).textContent = message;
      $(errorId).hidden = false;
    } else notice(message, true);
  } finally {
    lock(false);
  }
}
async function all(path) {
  let result = [],
    offset = 0;
  while (true) {
    const page = await api(`${path}?limit=500&offset=${offset}`);
    result.push(...page);
    if (page.length < 500) return result;
    offset += page.length;
  }
}
async function load() {
  const [reports, events] = await Promise.all([
    all("/reports"),
    all("/events"),
  ]);
  state.reports = reports;
  state.events = events;
  $("pending-count").textContent = reports.filter((r) => !r.event_id).length;
  $("active-count").textContent = events.filter(
    (e) => e.status !== "fulfilled",
  ).length;
  $("closed-count").textContent = events.filter(
    (e) => e.status === "fulfilled",
  ).length;
  renderList();
}
function setTab(tab) {
  state.tab = tab;
  state.selected = null;
  state.event = null;
  state.view++;
  $("reports-tab").setAttribute("aria-pressed", String(tab === "reports"));
  $("events-tab").setAttribute("aria-pressed", String(tab === "events"));
  $("filter").innerHTML =
    tab === "reports"
      ? '<option value="pending">İnceleme bekleyen</option><option value="all">Tüm raporlar</option>'
      : '<option value="all">Tüm ihtiyaçlar</option><option value="open">Açık</option><option value="in_progress">İşlemde</option><option value="fulfilled">Karşılandı</option>';
  $("search").value = "";
  renderList();
  $("detail").innerHTML = empty(
    "Bir kayıt seç",
    "Kaynakları ve karar geçmişini burada inceleyebilirsin.",
  );
}
function renderList() {
  const query = $("search").value.toLocaleLowerCase("tr");
  const filter = $("filter").value;
  const isReport = state.tab === "reports";
  let rows = (isReport ? state.reports : state.events).filter((r) =>
    `${r.location} ${r.text || ""} ${needs[r.need]}`
      .toLocaleLowerCase("tr")
      .includes(query),
  );
  rows = rows.filter((r) =>
    isReport
      ? filter !== "pending" || !r.event_id
      : filter === "all" || r.status === filter,
  );
  $("record-list").innerHTML = rows.length
    ? rows
        .slice()
        .reverse()
        .map(
          (r) =>
            `<button class="record" data-select="${esc(r.id)}" aria-current="${state.selected === r.id}"><div class="record-top"><span class="badge">${esc(needs[r.need])}</span>${isReport ? `<span class="small">${esc(languages[r.language])}</span>` : badge(r.status)}</div><strong>${esc(r.location)}</strong><p>${esc(isReport ? r.text : `${statuses[r.status]} · İhtiyaç kaydı`)}</p><small>${isReport ? (r.event_id ? "Bağlandı" : "İnceleme bekliyor") : "Oluşturuldu"} · ${esc(date(isReport ? r.received_at : r.created_at))}</small></button>`,
        )
        .join("")
    : empty(
        "Kayıt bulunamadı",
        query
          ? "Arama veya filtreyi değiştirebilirsin."
          : isReport
            ? "Yeni rapor ekleyebilir veya tüm raporları görüntüleyebilirsin."
            : "Onayladığın ihtiyaç kayıtları burada görünecek.",
      );
}
function metadata(r) {
  return `<dl class="metadata"><div><dt>Kaynak</dt><dd>${esc(r.source)}</dd></div><div><dt>Bildirilen miktar</dt><dd>${r.quantity === null ? "Bilinmiyor" : `${esc(r.quantity)} ${esc(r.unit)}`}</dd></div><div><dt>Olay zamanı</dt><dd>${esc(date(r.reported_at))}</dd></div><div><dt>Alınma zamanı</dt><dd>${esc(date(r.received_at))}</dd></div></dl>`;
}
async function selectRecord(id) {
  state.selected = id;
  state.event = null;
  const view = ++state.view;
  renderList();
  $("detail").innerHTML = empty(
    "Kayıt yükleniyor",
    "Kaynaklar ve kararlar getiriliyor.",
  );
  try {
    if (state.tab === "events") {
      const event = await api(`/events/${id}`);
      if (view !== state.view) return;
      state.event = event;
      renderEvent(event);
    } else {
      const report = state.reports.find((r) => r.id === id);
      if (!report) return;
      const result = await api(`/reports/${id}/suggestions`);
      const candidates = await Promise.all(
        result.candidates.map(async (c) => ({
          ...c,
          event: await api(`/events/${c.event_id}`),
        })),
      );
      if (view !== state.view) return;
      renderReport(report, candidates);
    }
  } catch (e) {
    if (view === state.view) {
      $("detail").innerHTML = empty(
        "Kayıt açılamadı",
        "Yenile düğmesiyle tekrar deneyebilirsin.",
      );
      throw e;
    }
  }
}
function renderReport(r, candidates) {
  const sameNeed = state.events.filter((e) => e.need === r.need);
  $("detail").innerHTML =
    `<div class="detail-header"><div><span class="eyebrow">KAYNAK RAPOR</span><h2>${esc(r.location)} · ${esc(needs[r.need])}</h2><p class="small">${esc(languages[r.language])} · ${r.event_id ? "Bir ihtiyaç kaydına bağlı" : "Koordinatör kararı bekliyor"}</p></div><span class="badge">${esc(r.id.slice(0, 8))}</span></div><blockquote class="source" lang="${esc(r.language)}">${esc(r.text)}</blockquote>${metadata(r)}${r.event_id ? `<button class="secondary" data-event="${esc(r.event_id)}">Bağlı ihtiyaç kaydını aç</button><form id="split-form" class="decision-box"><h3>Yanlış bağlantıyı düzelt</h3><p class="small">Rapor ayrı, açık bir ihtiyaç kaydına taşınır. Önceki kararlar geçmişte kalır.</p><label for="split-reason">Ayırma gerekçesi</label><textarea id="split-reason" required minlength="3" maxlength="1000" rows="2"></textarea><div class="actions"><button class="secondary" type="submit">Raporu ayrı kayda taşı</button></div></form>` : `<h3 class="section-title">Benzer ihtiyaç kayıtları <span class="badge">${candidates.length}</span></h3><p class="small">Aynı konum ve ihtiyaç türüne sahip kayıtlar. Bağlamadan önce kaynakları karşılaştır.</p>${candidates.length ? candidates.map((c) => `<article class="candidate"><div class="record-top"><h3>${esc(c.event.location)} · ${esc(needs[c.event.need])}</h3>${badge(c.event.status)}</div><div class="flags">${c.flags.map((f) => `<span class="flag">${esc(flagLabels[f] || f)}</span>`).join("")}</div>${c.event.reports.map((source) => `<p class="evidence">${esc(languages[source.language])} · ${source.quantity === null ? "Miktar bilinmiyor" : `${esc(source.quantity)} ${esc(source.unit)}`} · ${esc(date(source.reported_at))}</p><blockquote class="source" lang="${esc(source.language)}">${esc(source.text)}</blockquote>`).join("")}<button class="secondary" type="button" data-candidate="${esc(c.event_id)}">Karar için bu kaydı seç</button></article>`).join("") : '<p class="small">Öneri bulunamadı. Ayrı bir ihtiyaç oluşturabilir veya konum adını doğrulayarak mevcut bir kayıt seçebilirsin.</p>'}<form id="decision-form" class="decision-box"><h3>Kararını kaydet</h3><label for="target-event">İşlem</label><select id="target-event"><option value="">Yeni, ayrı bir ihtiyaç oluştur</option>${sameNeed.map((e) => `<option value="${esc(e.id)}">Mevcut kayda bağla: ${esc(e.location)} · ${esc(statuses[e.status])} · ${esc(e.id.slice(0, 8))}</option>`).join("")}</select><label for="decision-reason">Karar gerekçesi</label><textarea id="decision-reason" required minlength="3" maxlength="1000" rows="2" placeholder="Hangi bilgiyi doğruladın?"></textarea><div class="actions"><button type="submit" class="primary">Kararı onayla ve kaydet</button></div><p class="small">Raporu bağlamak ihtiyaç durumunu otomatik değiştirmez.</p></form>`}`;
}
function renderEvent(e) {
  $("detail").innerHTML =
    `<div class="detail-header"><div><span class="eyebrow">İHTİYAÇ KAYDI</span><h2>${esc(e.location)} · ${esc(needs[e.need])}</h2><p class="small">${e.reports.length} kaynak rapor · Kayıt ${esc(e.id.slice(0, 8))}</p></div>${badge(e.status)}</div><h3>Bağlı kaynaklar</h3>${e.reports.length ? e.reports.map((r) => `<article class="source-card"><div class="record-top"><span class="badge">${esc(languages[r.language])}</span><span class="small">${esc(r.id.slice(0, 8))}</span></div><blockquote class="source" lang="${esc(r.language)}">${esc(r.text)}</blockquote>${metadata(r)}<button class="link-button" data-report="${esc(r.id)}">Raporu incele / bağlantıyı düzelt</button></article>`).join("") : '<p class="small">Bu kayda bağlı rapor kalmadı. Geçmiş kararlar aşağıda korunuyor.</p>'}${
      e.reports.length
        ? `<form id="status-form" class="decision-box"><h3>İhtiyaç durumunu güncelle</h3><label for="event-status">Yeni durum</label><select id="event-status">${Object.entries(
            statuses,
          )
            .map(
              ([k, v]) =>
                `<option value="${k}" ${k === e.status ? "selected" : ""}>${v}</option>`,
            )
            .join(
              "",
            )}</select><label for="evidence-report">Karara dayanak olan rapor</label><select id="evidence-report" required><option value="">Bir kaynak seç</option>${e.reports.map((r) => `<option value="${esc(r.id)}">${esc(r.id.slice(0, 8))} · ${esc(r.text.slice(0, 90))}</option>`).join("")}</select><label for="status-reason">Karar gerekçesi</label><textarea id="status-reason" required minlength="3" maxlength="1000" rows="2" placeholder="Örn. Teslimat kapsamı saha ekibiyle doğrulandı."></textarea><div class="actions"><button type="submit" class="primary">Durumu kaydet</button></div><p class="small">Yalnızca bu ihtiyaç türünün durumu değişir.</p></form>`
        : ""
    }<h3 class="section-title">Karar geçmişi</h3><ol class="history">${e.history
      .slice()
      .reverse()
      .map((h) => {
        let d = {};
        try {
          d = JSON.parse(h.details);
        } catch {}
        return `<li><strong>${esc(actionLabels[h.action] || h.action)}</strong><p>${esc(h.actor)}${d.before ? ` · ${esc(statuses[d.before])} → ${esc(statuses[d.after])}` : ""}</p><p>${esc(d.reason || "")}</p><time>${esc(date(h.timestamp))}</time></li>`;
      })
      .join("")}</ol>`;
}
async function openEvent(id) {
  setTab("events");
  await selectRecord(id);
}
$("login-form").addEventListener("submit", (e) => {
  e.preventDefault();
  run(async () => {
    state.token = $("token").value.trim();
    state.epoch++;
    await load();
    $("token").value = "";
    $("login-view").hidden = true;
    $("dashboard").hidden = false;
    $("logout").hidden = false;
    $("notice").hidden = true;
    setTab("reports");
  });
});
$("logout").addEventListener("click", () => {
  clearSession();
  notice("Oturum kapatıldı.");
  $("token").focus();
});
$("reports-tab").addEventListener("click", () => setTab("reports"));
$("events-tab").addEventListener("click", () => setTab("events"));
$("filter").addEventListener("change", renderList);
$("search").addEventListener("input", renderList);
$("record-list").addEventListener("click", (e) => {
  const b = e.target.closest("[data-select]");
  if (b) run(() => selectRecord(b.dataset.select));
});
$("refresh").addEventListener("click", () =>
  run(async () => {
    await load();
    if (state.selected) await selectRecord(state.selected);
    notice("Kayıtlar yenilendi.");
  }),
);
$("add-report").addEventListener("click", () => {
  $("form-error").hidden = true;
  $("report-dialog").showModal();
  $("report-text").focus();
});
$("close-dialog").addEventListener("click", () => $("report-dialog").close());
$("report-dialog").addEventListener("cancel", (e) => {
  if (state.busy) e.preventDefault();
});
$("report-form").addEventListener("submit", (e) => {
  e.preventDefault();
  run(async () => {
    const f = new FormData(e.target);
    const quantity = f.get("quantity").trim();
    const unit = f.get("unit").trim();
    if (Boolean(quantity) !== Boolean(unit))
      throw new Error(
        "Miktar ve birimi birlikte doldur veya ikisini de boş bırak.",
      );
    const timestamp = f.get("reported_at");
    const payload = {
      text: f.get("text"),
      language: f.get("language"),
      source: f.get("source"),
      location: f.get("location"),
      need: f.get("need"),
      quantity: quantity === "" ? null : Number(quantity),
      unit: unit || null,
      reported_at: timestamp ? new Date(timestamp).toISOString() : null,
    };
    const r = await api("/reports", "POST", payload);
    e.target.reset();
    $("report-dialog").close();
    await load();
    setTab("reports");
    await selectRecord(r.id);
    notice("Rapor kaydedildi. Kaynakları inceleyip karar verebilirsin.");
  }, "form-error");
});
$("detail").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.event) run(() => openEvent(b.dataset.event));
  if (b.dataset.report)
    run(async () => {
      setTab("reports");
      $("filter").value = "all";
      await selectRecord(b.dataset.report);
    });
  if (b.dataset.candidate) {
    $("target-event").value = b.dataset.candidate;
    $("decision-reason").focus();
  }
});
$("detail").addEventListener("submit", (e) => {
  e.preventDefault();
  const form = e.target;
  run(async () => {
    const id = state.selected;
    if (form.id === "decision-form") {
      const target = $("target-event").value;
      const reason = $("decision-reason").value.trim();
      if (reason.length < 3)
        throw new Error("Karar gerekçesini en az 3 karakterle yaz.");
      const event = await api(
        `/reports/${id}/${target ? "link" : "new-event"}`,
        "POST",
        { reason, ...(target ? { event_id: target } : {}) },
      );
      await load();
      await openEvent(event.id);
      notice("Karar kaydedildi.");
    } else if (form.id === "split-form") {
      const reason = $("split-reason").value.trim();
      if (reason.length < 3) throw new Error("Ayırma gerekçesini yaz.");
      const event = await api(`/reports/${id}/split`, "POST", { reason });
      await load();
      await openEvent(event.id);
      notice("Rapor ayrı bir ihtiyaç kaydına taşındı.");
    } else if (form.id === "status-form") {
      const event = state.event;
      const reason = $("status-reason").value.trim();
      if (reason.length < 3)
        throw new Error("Durum değişikliğinin gerekçesini yaz.");
      await api(`/events/${event.id}/status`, "PATCH", {
        status: $("event-status").value,
        evidence_report_id: $("evidence-report").value,
        expected_version: event.version,
        reason,
      });
      await load();
      await selectRecord(event.id);
      notice("İhtiyaç durumu ve karar geçmişi güncellendi.");
    }
  });
});
