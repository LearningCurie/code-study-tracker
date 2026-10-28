(function () {
  "use strict";
  const D = JSON.parse(document.getElementById("guide-data").textContent);
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = h => /^https:\/\//.test(h) || /^\.\//.test(h) ? h : "#";
  const A = (h, t, c) => `<a${c ? ` class="${c}"` : ""} href="${esc(safeUrl(h))}" target="_blank" rel="noopener">${esc(t)}</a>`;
  const KIND = { lesson: "Lesson", lab: "Lab", build: "Build" };
  const KINDS = { lesson: "Lessons", lab: "Labs", build: "Builds" };
  const STATUS = ["Not started", ...D.statuses];
  const anchor = id => "l-" + id.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
  const hm = m => m < 60 ? m + " min" : Math.floor(m / 60) + " h" + (m % 60 >= 5 ? " " + Math.round(m % 60 / 5) * 5 + " min" : "");
  const plural = (n, w) => n + " " + w + (n === 1 ? "" : "s");

  const M = new Map();
  let E = {};
  let kindFilter = "all";
  const order = [];
  const byId = new Map();
  D.modules.forEach((m, mi) => {
    const seen = { lesson: 0, lab: 0, build: 0 };
    m.items.forEach(it => {
      it.mi = mi;
      it.n = ++seen[it.k];
      it.pos = order.length;
      order.push(it);
      byId.set(it.id, it);
    });
  });
  const stageOf = mi => D.stages.findIndex(s => s.modules.includes(mi));

  $("ttl").textContent = D.title;
  $("sub").textContent = D.subtitle;
  $("q").placeholder = D.searchHint;
  // D.routine is trusted build output that may contain <b> emphasis.
  $("routine").innerHTML = D.routine.map(h => `<li>${h}</li>`).join("");
  $("seg").innerHTML = ["all", ...Object.keys(KIND)].map(v => `<button type="button" data-v="${v}" aria-pressed="${v === "all"}">${v === "all" ? "All" : KINDS[v]}</button>`).join("");
  $("flt").innerHTML = `<option value="all">Any status</option>` + STATUS.map((s, i) => `<option value="${i}">${esc(s)}</option>`).join("") + `<option value="r">${esc(D.statuses[1])} or ${esc(D.statuses[2].toLowerCase())}</option>`;

  $("stagemap").innerHTML = D.stages.map((s, si) => `<li><a href="#s-${esc(s.key)}" data-s="${si}"><span class="sn">Stage ${si + 1}</span><b>${esc(s.name)}</b><span class="sc"></span><span class="pb"><i></i></span></a></li>`).join("");

  const row = it => `<li class="it" id="${anchor(it.id)}" data-id="${esc(it.id)}" data-k="${it.k}" data-s="${esc((it.t + " " + it.g + " " + D.modules[it.mi].name).toLowerCase())}">` +
    `<button type="button" class="ck" aria-label="${esc("Mark done: " + it.t)}" aria-pressed="false"></button>` +
    `<details class="lz"><summary><span class="ih"><span class="ik">${KIND[it.k]} ${it.n}</span><span class="tt">${esc(it.t)}</span><span class="tm">${esc(it.tm)}</span></span><span class="g">${esc(it.g)}</span></summary><div class="lb"></div></details></li>`;

  const lists = (h, xs) => xs.length ? `<div><h4>${esc(h)}</h4><ul>${xs.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>` : "";
  const modMeta = m => {
    const c = k => m.items.filter(i => i.k === k).length;
    const mins = m.items.filter(i => i.k !== "build").reduce((a, i) => a + i.m, 0);
    return [c("lesson") && plural(c("lesson"), "lesson"), c("lab") && plural(c("lab"), "lab"), c("build") && plural(c("build"), "build"), mins && "~" + hm(mins) + " reading and labs"].filter(Boolean).join(" · ");
  };
  const group = (m, k) => {
    const its = m.items.filter(i => i.k === k);
    return its.length ? `<section class="grp" data-k="${k}"><h4 class="gh">${KINDS[k]} <span class="n"></span></h4><ol class="items">${its.map(row).join("")}</ol></section>` : "";
  };
  const module = (m, mi) => `<details class="mod" id="m-${esc(m.key)}" data-k="${esc(m.key)}"><summary><span class="mn">${mi + 1}</span><span class="mt"><h3>${esc(m.name)}</h3><span class="ms">${esc(m.summary)}</span><span class="mm">${esc(modMeta(m))}</span></span><span class="mc"></span><span class="pb"><i></i></span></summary>` +
    `<div class="mintro"><div class="why"><h4>Why it matters</h4><p>${esc(m.why)}</p></div><div class="mg">${lists("You will be able to", m.outcomes)}${lists("Pro habits", m.habits)}${lists("Common traps", m.traps)}</div></div>` +
    `<div class="apply">${group(m, "lesson")}${group(m, "lab")}${group(m, "build")}` +
    (m.further.length ? `<details class="further"><summary>Go further: optional courses, talks and long reads</summary><ul>${m.further.map(f => `<li><span class="fk">${esc(f.k)}</span>${A(f.h, f.t)}</li>`).join("")}</ul></details>` : "") +
    `<p class="empty" hidden>Nothing here matches the current filters.</p></div></details>`;

  $("mods").innerHTML = D.stages.map((s, si) => {
    const mins = s.modules.reduce((a, mi) => a + D.modules[mi].items.filter(i => i.k !== "build").reduce((b, i) => b + i.m, 0), 0);
    return `<section class="stage" id="s-${esc(s.key)}" data-s="${si}"><header class="sh"><p class="sk">Stage ${si + 1} · ${plural(s.modules.length, "module")} · ~${hm(mins)}</p><h2>${esc(s.name)}</h2><p>${esc(s.intro)}</p></header>${s.modules.map(mi => module(D.modules[mi], mi)).join("")}</section>`;
  }).join("");
  $("rail").innerHTML = D.stages.map((s, si) => `<li class="rs">Stage ${si + 1} · ${esc(s.short || s.name)}</li>` + s.modules.map(mi => `<li class="rm"><a href="#m-${esc(D.modules[mi].key)}" data-k="${esc(D.modules[mi].key)}"><span class="rn">${mi + 1}</span><span class="rt">${esc(D.modules[mi].name)}</span><span class="rc"></span><span class="rb"><b></b></span></a></li>`).join("")).join("");
  $("jump").innerHTML = `<option value="">Jump to module</option>` + D.stages.map((s, si) => `<optgroup label="Stage ${si + 1}: ${esc(s.name)}">${s.modules.map(mi => `<option value="${esc(D.modules[mi].key)}">${mi + 1}. ${esc(D.modules[mi].name)}</option>`).join("")}</optgroup>`).join("");

  const rows = [...document.querySelectorAll(".it")];
  const atlas = order.filter(it => it.k === "build" && /^Atlas\b/.test(it.t));
  if (atlas.length && D.atlas) {
    $("atlas").hidden = false;
    $("atlasDesc").textContent = D.atlas;
    $("atlasList").innerHTML = atlas.map(it => `<li data-id="${esc(it.id)}"><a href="#${anchor(it.id)}" data-id="${esc(it.id)}">${esc(it.t.replace(/^Atlas\s*/, ""))}</a> <span class="am">${esc(D.modules[it.mi].name)} · ${esc(it.tm)}</span></li>`).join("");
  }
  const rowOf = new Map(rows.map(li => [li.dataset.id, li]));
  const mods = [...document.querySelectorAll(".mod")];
  const stages = [...document.querySelectorAll(".stage")];
  const railMods = [...document.querySelectorAll("#rail .rm")];
  const mapStages = [...document.querySelectorAll("#stagemap li")];

  function body(it, lessonHtml) {
    const src = it.src.length ? `<aside class="src"><h4>${it.k === "build" ? "References" : "Go deeper (optional)"}</h4><ul>${it.src.map(s => `<li>${A(s.h, s.t)}${s.n ? `<span> · ${esc(s.n)}</span>` : ""}</li>`).join("")}</ul></aside>` : "";
    const next = it.k === "build" ? "Done, next" : "Done, next lesson";
    return `<div class="lc">${lessonHtml}</div>${src}<div class="lf"><button type="button" class="btn pri nx">${next} <span aria-hidden="true">&rarr;</span></button><button type="button" class="btn st" data-c="2" aria-pressed="false">Needs practice</button><button type="button" class="btn st" data-c="3" aria-pressed="false">Revisit later</button><button type="button" class="btn quiet cx">Close</button></div>`;
  }

  // Lesson bodies live in one script per module (D.contentDir/<key>.js) and are loaded on first use.
  const content = new Map();
  const loading = new Map();
  function absorb() {
    const q = window.guideContent || [];
    while (q.length) { const [k, b] = q.shift(); content.set(k, b); }
  }
  function loadModule(mi) {
    const m = D.modules[mi];
    absorb();
    if (content.has(m.key)) return Promise.resolve();
    if (!loading.has(m.key)) {
      loading.set(m.key, new Promise((resolve, reject) => {
        const s = document.createElement("script");
        s.src = `./${D.contentDir}/${encodeURIComponent(m.key)}.js?v=${encodeURIComponent(m.v)}`;
        s.onload = () => { absorb(); if (content.has(m.key)) resolve(); else reject(new Error("empty")); };
        s.onerror = () => { s.remove(); reject(new Error("failed")); };
        document.head.appendChild(s);
      }).catch(e => { loading.delete(m.key); throw e; }));
    }
    return loading.get(m.key);
  }
  function fill(li) {
    const it = byId.get(li.dataset.id), b = li.querySelector(".lb"), key = D.modules[it.mi].key;
    if (!b.dataset.ok) {
      if (content.has(key)) {
        // Lesson HTML is generated at build time by mdlite.py, which escapes all text and allows only https links.
        b.innerHTML = body(it, content.get(key)[it.id] || "");
        b.dataset.ok = "1";
      } else {
        b.innerHTML = '<p class="ld" role="status">Loading the lesson&hellip;</p>';
        loadModule(it.mi).then(() => fill(li), () => {
          b.innerHTML = '<p class="ld" role="alert">This lesson could not be loaded. Check your connection and <button type="button" class="linkish rt">try again</button>.</p>';
        });
        return;
      }
    }
    paintRow(li);
  }

  function visibleByFilters(li) {
    const f = $("flt").value, q = $("q").value.trim().toLowerCase(), s = M.get(li.dataset.id) || 0;
    const sOk = f === "all" || (f === "r" ? s === 2 || s === 3 : +f === s);
    return (kindFilter === "all" || li.dataset.k === kindFilter) && sOk && (!q || li.dataset.s.includes(q));
  }
  function paintRow(li) {
    const s = M.get(li.dataset.id) || 0;
    li.dataset.st = s;
    li.querySelector(".ck").setAttribute("aria-pressed", s === 1);
    li.querySelector(".ck").title = STATUS[s];
    li.querySelectorAll(".st").forEach(b => b.setAttribute("aria-pressed", +b.dataset.c === s));
    const nx = li.querySelector(".nx");
    if (nx) nx.firstChild.textContent = (s === 1 ? "Done ✓ · next" : (li.dataset.k === "build" ? "Done, next" : "Done, next lesson")) + " ";
  }

  function paint() {
    const filtered = kindFilter !== "all" || $("flt").value !== "all" || $("q").value.trim();
    rows.forEach(li => { paintRow(li); li.hidden = !visibleByFilters(li); });
    mods.forEach((d, i) => {
      const li = [...d.querySelectorAll(".it")], vis = li.filter(x => !x.hidden).length;
      const done = li.filter(x => M.get(x.dataset.id) === 1).length, pct = li.length ? done / li.length * 100 : 0;
      d.querySelectorAll(".grp").forEach(g => {
        const gl = [...g.querySelectorAll(".it")];
        g.hidden = gl.every(x => x.hidden);
        g.querySelector(".n").textContent = gl.filter(x => M.get(x.dataset.id) === 1).length + "/" + gl.length;
      });
      d.querySelector(".mc").textContent = done + "/" + li.length;
      d.querySelector(".pb i").style.width = pct + "%";
      d.querySelector(".empty").hidden = vis > 0;
      d.hidden = !!filtered && vis === 0;
      d.classList.toggle("done", li.length > 0 && done === li.length);
      if ($("q").value.trim() && vis) d.open = true;
      const r = railMods[i];
      r.querySelector(".rc").textContent = done + "/" + li.length;
      r.querySelector(".rb b").style.width = pct + "%";
      r.classList.toggle("dim", d.hidden);
      r.classList.toggle("done", li.length > 0 && done === li.length);
    });
    stages.forEach((s, si) => {
      s.hidden = [...s.querySelectorAll(".mod")].every(d => d.hidden);
      const its = D.stages[si].modules.flatMap(mi => D.modules[mi].items);
      const done = its.filter(i => M.get(i.id) === 1).length;
      const ms = mapStages[si];
      ms.querySelector(".sc").textContent = done + " of " + its.length + " done";
      ms.querySelector(".pb i").style.width = (its.length ? done / its.length * 100 : 0) + "%";
      ms.classList.toggle("done", its.length > 0 && done === its.length);
    });
    paintStats();
    paintQueue();
    if (atlas.length) {
      const done = atlas.filter(it => M.get(it.id) === 1).length;
      $("atlasCount").textContent = `${done} of ${atlas.length} milestones`;
      $("atlasFill").style.width = done / atlas.length * 100 + "%";
      $("atlasList").querySelectorAll("li").forEach(li => { li.dataset.st = M.get(li.dataset.id) || 0; });
    }
  }

  function paintStats() {
    const c = [0, 0, 0, 0];
    order.forEach(it => c[M.get(it.id) || 0]++);
    $("fill").style.width = c[1] / order.length * 100 + "%";
    const left = order.filter(it => it.k !== "build" && M.get(it.id) !== 1).reduce((a, it) => a + it.m, 0);
    $("stats").innerHTML = `<span><b>${c[1]}</b> of ${order.length} done</span>` +
      Object.keys(KIND).map(k => {
        const l = order.filter(it => it.k === k);
        return `<span>${KINDS[k]} <b>${l.filter(it => M.get(it.id) === 1).length}</b>/${l.length}</span>`;
      }).join("") +
      `<span>${esc(D.statuses[1])} <b>${c[2]}</b></span><span>${esc(D.statuses[2])} <b>${c[3]}</b></span><span>About <b>${hm(left)}</b> of reading and labs left</span>`;
  }

  function nextItems(n, after = -1) {
    const out = [];
    for (const it of order) {
      if (it.pos <= after || M.has(it.id)) continue;
      if (kindFilter !== "all" && it.k !== kindFilter) continue;
      out.push(it);
      if (out.length === n) break;
    }
    return out;
  }
  function paintQueue() {
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    const today = Object.entries(E).filter(([id, e]) => e.status === 1 && e.updatedAt >= start.getTime() && byId.has(id));
    const mins = today.reduce((a, [id]) => a + (byId.get(id).k === "build" ? 0 : byId.get(id).m), 0);
    $("today").textContent = today.length ? `Today you finished ${plural(today.length, "item")}${mins ? " (about " + hm(mins) + ")" : ""}. Nice work.` : "Nothing finished yet today. One lesson is a good start.";
    // Plan roughly 45 minutes: take items until the budget is used, always at least one.
    const plan = [];
    let budget = 0;
    for (const it of nextItems(6)) {
      if (plan.length && (budget + it.m > 50 || it.k === "build")) break;
      plan.push(it);
      budget += it.m;
    }
    $("queue").innerHTML = plan.length ? plan.map(it => `<li><a href="#${anchor(it.id)}" data-id="${esc(it.id)}"><span class="qk">${KIND[it.k]} · ${esc(it.tm)}</span><b>${esc(it.t)}</b><span class="qm">${esc(D.modules[it.mi].name)}</span></a></li>`).join("") : "<li>Everything is done. Revisit items marked Needs practice or Revisit.</li>";
    $("start").hidden = !plan.length;
    $("start").textContent = M.size ? "Continue" : "Start the first lesson";
    $("qtime").textContent = plan.length ? "About " + hm(budget) : "";
    const review = order.filter(it => M.get(it.id) === 2 || M.get(it.id) === 3).length;
    $("review").hidden = !review;
    $("review").textContent = `Review ${plural(review, "item")} marked ${D.statuses[1].toLowerCase()} or ${D.statuses[2].toLowerCase()}`;
  }

  function remember(m) {
    try { localStorage.setItem("study-last:" + D.storageKey, m.name.slice(0, 120)); } catch (e) { /* optional */ }
  }
  function openItem(id, focus = true) {
    const li = rowOf.get(id);
    if (!li) return;
    if (li.hidden) {
      $("flt").value = "all"; $("q").value = ""; kindFilter = "all";
      $("seg").querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x.dataset.v === "all"));
      paint();
    }
    li.closest(".mod").open = true;
    const d = li.querySelector(".lz");
    d.open = true;
    fill(li);
    li.scrollIntoView({ block: "start" });
    if (focus) li.querySelector("summary").focus({ preventScroll: true });
  }
  function openMod(k) {
    const d = $("m-" + k);
    if (d) { d.hidden = false; d.open = true; d.scrollIntoView({ block: "start" }); }
  }

  $("mods").addEventListener("toggle", e => {
    const t = e.target;
    if (t.classList.contains("lz")) {
      const li = t.closest(".it");
      if (t.open) {
        fill(li);
        // One lesson open at a time keeps each session focused.
        document.querySelectorAll(".lz[open]").forEach(o => { if (o !== t) o.open = false; });
        history.replaceState(null, "", "#" + li.id);
        remember(D.modules[byId.get(li.dataset.id).mi]);
      }
    } else if (t.classList.contains("mod") && t.open) {
      remember(D.modules[mods.indexOf(t)]);
      loadModule(mods.indexOf(t)).catch(() => { /* retried when a lesson opens */ });
    }
  }, true);

  $("mods").addEventListener("click", e => {
    const li = e.target.closest(".it");
    if (!li) return;
    const id = li.dataset.id, s = M.get(id) || 0;
    if (e.target.closest(".ck")) {
      progress.set(id, s === 1 ? 0 : 1);
    } else if (e.target.closest(".nx")) {
      if (s !== 1) progress.set(id, 1);
      li.querySelector(".lz").open = false;
      const nx = nextItems(1, byId.get(id).pos)[0];
      if (nx) openItem(nx.id);
      else li.scrollIntoView({ block: "center" });
    } else if (e.target.closest(".st")) {
      const c = +e.target.closest(".st").dataset.c;
      progress.set(id, s === c ? 0 : c);
    } else if (e.target.closest(".cx")) {
      li.querySelector(".lz").open = false;
      li.scrollIntoView({ block: "nearest" });
      li.querySelector("summary").focus({ preventScroll: true });
    } else if (e.target.closest(".rt")) {
      fill(li);
    }
  });

  $("seg").addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b) return;
    kindFilter = b.dataset.v;
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
  $("stagemap").addEventListener("click", e => {
    const a = e.target.closest("a");
    if (!a) return;
    e.preventDefault();
    const s = stages[+a.dataset.s];
    s.hidden = false;
    s.scrollIntoView({ block: "start" });
  });
  $("queue").addEventListener("click", e => {
    const a = e.target.closest("a[data-id]");
    if (!a) return;
    e.preventDefault();
    openItem(a.dataset.id);
  });
  $("atlasList").addEventListener("click", e => {
    const a = e.target.closest("a[data-id]");
    if (!a) return;
    e.preventDefault();
    openItem(a.dataset.id);
  });
  $("review").addEventListener("click", () => {
    $("flt").value = "r";
    paint();
    const first = rows.find(li => !li.hidden);
    if (first) { first.closest(".mod").open = true; first.scrollIntoView({ block: "start" }); }
  });
  $("jump").addEventListener("change", e => { if (e.target.value) openMod(e.target.value); e.target.value = ""; });
  $("tog").addEventListener("click", () => {
    const open = !mods.filter(d => !d.hidden).every(d => d.open);
    mods.forEach(d => { d.open = open; });
    $("tog").textContent = open ? "Collapse all" : "Expand all";
  });
  const go = () => { const it = nextItems(1)[0]; if (it) openItem(it.id); };
  $("next").addEventListener("click", go);
  $("start").addEventListener("click", go);

  const progress = StudyProgress.mount({
    storageKey: D.storageKey,
    ids: order.map(it => it.id),
    onChange(entries) {
      E = entries;
      M.clear();
      Object.entries(entries).forEach(([id, e]) => { if (e.status && byId.has(id)) M.set(id, e.status); });
      paint();
    }
  });

  function fromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    if (!h) return false;
    const li = document.getElementById(h);
    if (li && li.classList.contains("it")) { openItem(li.dataset.id, false); return true; }
    if (h.startsWith("m-") && $(h)) { openMod(h.slice(2)); return true; }
    if (h.startsWith("s-") && $(h)) { $(h).scrollIntoView({ block: "start" }); return true; }
    return false;
  }
  window.addEventListener("hashchange", fromHash);
  if (!fromHash()) {
    const first = nextItems(1)[0];
    (first ? rowOf.get(first.id).closest(".mod") : mods[0]).open = true;
  }
})();
