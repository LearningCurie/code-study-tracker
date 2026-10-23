(function () {
  "use strict";
  const DATA = JSON.parse(document.getElementById("tracker-data").textContent);
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = h => /^https:\/\//.test(h) || /^\.\//.test(h) ? h : "#";
  const A = (h, t, c) => `<a${c ? ` class="${c}"` : ""} href="${esc(safeUrl(h))}" target="_blank" rel="noopener">${esc(t)}</a>`;
  const LAB = ["", ...DATA.statuses];
  const M = new Map();
  let fv = "all";

  $("ttl").textContent = DATA.title;
  $("sub").textContent = DATA.subtitle;
  $("howh").textContent = DATA.howTitle;
  $("q").placeholder = DATA.searchHint;
  // DATA.how is trusted build output that may contain <b> emphasis.
  $("how").innerHTML = DATA.how.map(h => `<li>${h}</li>`).join("");
  $("kit").innerHTML = `<h2>${esc(DATA.kit.title)}</h2>` + DATA.kit.groups.map(g => `<h3>${esc(g.h)}</h3><ul>${g.links.map(l => `<li>${A(l.h, l.t)}</li>`).join("")}</ul>`).join("");
  $("seg").setAttribute("aria-label", DATA.filter.label);
  $("seg").innerHTML = ["all", ...DATA.filter.values].map(v => `<button type="button" data-v="${esc(v)}" aria-pressed="${v === "all"}">${v === "all" ? "All" : esc(v)}</button>`).join("");
  $("flt").innerHTML = `<option value="all">Any status</option><option value="0">Not started</option>` + DATA.statuses.map((s, i) => `<option value="${i + 1}">${esc(s)}</option>`).join("");

  const row = it => `<li class="it" data-id="${esc(it.id)}" data-f="${esc(it.f || "")}" data-s="${esc((it.n ? it.n + " " : "") + it.t).toLowerCase()}"><div class="pt">${it.n ? `<span class="nb">${esc(it.n)}</span>` : ""}${A(it.h, it.t, "pn")}${it.links && it.links.length ? `<span class="lk">${it.links.map(l => A(l.h, l.t)).join("")}</span>` : ""}${it.d ? `<p class="d">${esc(it.d)}</p>` : ""}</div><span class="bs">${[1, 2, 3].map(c => `<button type="button" class="b b${c}" data-c="${c}" aria-pressed="false">${esc(LAB[c])}</button>`).join("")}</span></li>`;
  const sec = s => `<div${s.wide ? ' class="py"' : ""}><h3>${esc(s.h)}</h3>${s.items ? `<ul>${s.items.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : `<p>${esc(s.text)}</p>`}</div>`;
  const resl = (h, ls) => ls && ls.length ? `<div><h3>${esc(h)}</h3><ul>${ls.map(l => `<li>${A(l.h, l.t)}</li>`).join("")}</ul></div>` : "";
  $("mods").innerHTML = DATA.modules.map((m, i) => `<details class="mod" id="m-${esc(m.key)}" data-k="${esc(m.key)}"><summary><span class="mn">${i + 1}</span><h2>${esc(m.name)}</h2><span class="mc"></span>${m.why ? `<p class="why">${esc(m.why)}</p>` : ""}<span class="mb"><b></b></span></summary><div class="learn"><div class="lg">${m.learn.map(sec).join("")}</div><div class="res">${resl(DATA.readLabel, m.read)}${resl(DATA.watchLabel, m.watch)}</div></div><div class="apply">${m.groups.map(g => `<section class="grp"><h3 class="gh">${esc(g.name)} <span class="n"></span>${g.note ? `<span class="gd">${esc(g.note)}</span>` : ""}</h3><ul class="items">${g.items.map(row).join("")}</ul></section>`).join("")}<p class="empty" hidden>Nothing here matches the current filters.</p></div></details>`).join("");
  $("rail").innerHTML = DATA.modules.map((m, i) => `<li><a href="#m-${esc(m.key)}" data-k="${esc(m.key)}"><span class="rn">${i + 1}</span><span class="rt">${esc(m.name)}</span><span class="rc"></span><span class="rb"><b></b></span></a></li>`).join("");
  $("jump").innerHTML = `<option value="">Jump to topic</option>` + DATA.modules.map((m, i) => `<option value="${esc(m.key)}">${i + 1}. ${esc(m.name)}</option>`).join("");

  const items = [...document.querySelectorAll(".it")];
  const total = items.length;
  const rail = [...document.querySelectorAll("#rail li")];
  const mods = [...document.querySelectorAll(".mod")];

  function paint() {
    const f = $("flt").value, q = $("q").value.trim().toLowerCase();
    items.forEach(li => {
      const s = M.get(li.dataset.id) || 0;
      li.querySelectorAll(".b").forEach(x => x.setAttribute("aria-pressed", +x.dataset.c === s));
      li.hidden = !((fv === "all" || li.dataset.f === fv) && (f === "all" || +f === s) && (!q || li.dataset.s.includes(q)));
    });
    mods.forEach((d, i) => {
      const li = [...d.querySelectorAll(".it")], vis = li.filter(x => !x.hidden).length;
      const done = li.filter(x => M.get(x.dataset.id) === 1).length, pct = li.length ? done / li.length * 100 : 0;
      d.querySelectorAll(".grp").forEach(g => {
        const gl = [...g.querySelectorAll(".it")];
        g.hidden = gl.every(x => x.hidden);
        g.querySelector(".n").textContent = gl.filter(x => M.get(x.dataset.id) === 1).length + "/" + gl.length;
      });
      d.querySelector(".mc").textContent = done + "/" + li.length;
      d.querySelector(".mb b").style.width = pct + "%";
      d.querySelector(".empty").hidden = vis > 0;
      const filtered = fv !== "all" || f !== "all" || q;
      d.hidden = !!filtered && vis === 0;
      if (q && vis) d.open = true;
      const r = rail[i];
      r.querySelector(".rc").textContent = done + "/" + li.length;
      r.querySelector(".rb b").style.width = pct + "%";
      r.classList.toggle("dim", d.hidden);
      r.classList.toggle("done", li.length > 0 && done === li.length);
    });
    const c = [0, 0, 0, 0];
    items.forEach(li => c[M.get(li.dataset.id) || 0]++);
    $("fill").style.width = c[1] / total * 100 + "%";
    const other = items.filter(x => !DATA.filter.values.includes(x.dataset.f));
    $("stats").innerHTML = `<span><b>${c[1]}</b> of ${total} ${esc(DATA.statuses[0].toLowerCase())}</span>` +
      DATA.filter.values.map(v => {
        const l = items.filter(x => x.dataset.f === v);
        return `<span>${esc(v)} <b>${l.filter(x => M.get(x.dataset.id) === 1).length}</b>/${l.length}</span>`;
      }).join("") +
      (DATA.otherLabel ? `<span>${esc(DATA.otherLabel)} <b>${other.filter(x => M.get(x.dataset.id) === 1).length}</b>/${other.length}</span>` : "") +
      `<span>${esc(DATA.statuses[1])} <b>${c[2]}</b></span><span>${esc(DATA.statuses[2])} <b>${c[3]}</b></span>`;
  }

  function rememberTopic(d) {
    try { localStorage.setItem("study-last:" + DATA.storageKey, d.querySelector("h2").textContent.slice(0, 120)); } catch (e) { /* optional */ }
  }
  function openMod(k) {
    const d = $("m-" + k);
    if (d) { d.open = true; d.scrollIntoView({ block: "start" }); }
  }

  $("mods").addEventListener("click", e => {
    const b = e.target.closest(".b");
    if (!b) return;
    const id = b.closest(".it").dataset.id, c = +b.dataset.c;
    progress.set(id, M.get(id) === c ? 0 : c);
  });
  mods.forEach(d => d.addEventListener("toggle", () => { if (d.open) rememberTopic(d); }));
  $("seg").addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b) return;
    fv = b.dataset.v;
    $("seg").querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b));
    paint();
  });
  $("flt").addEventListener("change", paint);
  $("q").addEventListener("input", paint);
  $("rail").addEventListener("click", e => {
    const a = e.target.closest("a");
    if (!a) return;
    e.preventDefault();
    openMod(a.dataset.k);
  });
  $("jump").addEventListener("change", e => { if (e.target.value) openMod(e.target.value); e.target.value = ""; });
  $("tog").addEventListener("click", () => {
    const open = !mods.every(d => d.open);
    mods.forEach(d => { d.open = open; });
    $("tog").textContent = open ? "Collapse all" : "Expand all";
  });
  $("next").addEventListener("click", () => {
    const it = items.find(li => !M.has(li.dataset.id) && (fv === "all" || li.dataset.f === fv));
    if (!it) return;
    it.closest(".mod").open = true;
    if (it.hidden) { $("flt").value = "all"; $("q").value = ""; paint(); }
    it.scrollIntoView({ block: "center" });
    it.classList.remove("flash");
    void it.offsetWidth;
    it.classList.add("flash");
    it.querySelector(".pn").focus({ preventScroll: true });
  });

  const progress = StudyProgress.mount({
    storageKey: DATA.storageKey,
    ids: items.map(li => li.dataset.id),
    onChange(entries) {
      M.clear();
      Object.entries(entries).forEach(([id, e]) => { if (e.status) M.set(id, e.status); });
      paint();
    }
  });
  const first = items.find(li => !M.has(li.dataset.id));
  (first ? first.closest(".mod") : mods[0]).open = true;
})();
