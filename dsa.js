(function () {
  "use strict";
  const D = JSON.parse(document.getElementById("guide-data").textContent);
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = h => /^https:\/\//.test(h) || /^\.\//.test(h) ? h : "#";
  const A = (h, t, c) => `<a${c ? ` class="${c}"` : ""} href="${esc(safeUrl(h))}" target="_blank" rel="noopener">${esc(t)}</a>`;
  const KIND = { primer: "Primer", recap: "Recap", lab: "Lab", build: "Project" };
  const KINDS = { primer: "Primers", recap: "Recap cards", lab: "Labs", build: "Projects" };
  const DIFF = { E: "Easy", M: "Medium", H: "Hard", X: "Other judges" };
  const PMIN = { E: 20, M: 30, H: 45, X: 30 };
  const TIER = { derive: "Derive it", stretch: "Stretch" };
  const REVIEW_DAYS = 3;
  const LSTAT = ["Not started", ...D.statuses];
  const PSTAT = ["Not tried", ...D.pstatuses];
  const PTIP = ["", "Solved: you wrote the brute force and the optimal solution yourself",
    "Brute only: your brute force worked, the optimal solution did not come", "Stuck: you could not solve it; it comes back for review in a few days"];
  const anchor = id => "l-" + id.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
  const panchor = pid => "p-" + pid.replace(/[^a-z0-9]+/gi, "-");
  const hm = m => m < 60 ? m + " min" : Math.floor(m / 60) + " h" + (m % 60 >= 5 ? " " + Math.round(m % 60 / 5) * 5 + " min" : "");
  const plural = (n, w) => n + " " + w + (n === 1 ? "" : "s");

  // ---------- model ----------
  const M = new Map();
  let E = {};
  let view = "all";
  const order = [];
  const byId = new Map();
  const probs = new Map();
  const milestones = new Map();
  D.modules.forEach((m, mi) => {
    const seen = { primer: 0, recap: 0, lab: 0, build: 0 };
    m.items.forEach(it => {
      it.mi = mi;
      it.n = ++seen[it.k];
      it.pos = order.length;
      order.push(it);
      byId.set(it.id, it);
      for (let k = 1; k <= (it.ms || 0); k++) milestones.set(it.id + "#m" + k, it);
    });
    m.practice.forEach((p, i) => probs.set(p.id, { pid: p.id, mi, tier: p.t, i, pat: p.pat, after: p.after === undefined ? -1 : p.after, card: !!p.card, tm: p.tm || 0, lessons: [] }));
    m.bank.forEach((pid, i) => probs.set(pid, { pid, mi, tier: "bank", i, pat: "", after: -1, card: false, tm: 0, lessons: [] }));
  });
  D.modules.forEach(m => m.items.forEach(it => it.p.forEach(pid => {
    const p = probs.get(pid);
    if (p) p.lessons.push(it.id);
  })));
  const learnOrder = order.filter(it => it.k !== "build");
  const builds = order.filter(it => it.k === "build");
  const practiced = [...probs.values()].filter(p => p.tier !== "bank");
  const byPattern = new Map();
  practiced.forEach(p => { if (p.tier !== "mixed" && D.tags[p.pat]) (byPattern.get(p.pat) || byPattern.set(p.pat, []).get(p.pat)).push(p.pid); });
  const rec = pid => D.problems[pid];
  const isLc = pid => rec(pid).length === 6;
  const pdiff = pid => isLc(pid) ? rec(pid)[1] : "X";
  const pmins = pid => (probs.get(pid) && probs.get(pid).tm) || PMIN[pdiff(pid)];
  const pname = pid => (isLc(pid) ? pid + ". " : "") + rec(pid)[0];
  const original = pid => isLc(pid) ? `https://leetcode.com/problems/${rec(pid)[2]}/` : rec(pid)[2];
  function deeper(pid) {
    const r = rec(pid);
    if (!isLc(pid)) return [[`${r[1]}: the original statement, with a free online judge`, r[2]]];
    const out = [[`Reference solutions (doocs): several approaches in Python and other languages, about 5 minutes; compare after you have your own`, `https://leetcode.doocs.org/en/lc/${pid}/`]];
    if (r[3]) out.push(["NeetCode: the same problem in a free editor with tests", `https://neetcode.io/problems/${r[3]}/question`]);
    if (r[4]) out.push([`NeetCode video walkthrough, ${r[5]} min: watch after an honest attempt`, "https://www.youtube.com/watch?v=" + r[4]]);
    return out;
  }
  const allIds = [...order.map(it => it.id), ...milestones.keys(), ...probs.keys()];
  const statusOf = id => M.get(id) || 0;
  const lessonsDone = mi => D.modules[mi].items.filter(it => it.k === "primer" || it.k === "recap").every(it => statusOf(it.id) === 1);

  // ---------- static page ----------
  $("ttl").textContent = D.title;
  $("sub").textContent = D.subtitle;
  $("q").placeholder = D.searchHint;
  // D.routine is trusted build output that may contain <b> emphasis.
  $("routine").innerHTML = D.routine.map(h => `<li>${h}</li>`).join("");
  const VIEWS = [["all", "All"], ["learn", "Cards"], ["practice", "Problems"], ["build", "Projects"], ["review", "Review"]];
  $("seg").innerHTML = VIEWS.map(([v, t]) => `<button type="button" data-v="${v}" aria-pressed="${v === "all"}">${t}</button>`).join("");
  $("flt").innerHTML = `<option value="all">Any status</option><option value="0">Not started</option>` +
    [1, 2, 3].map(i => `<option value="${i}">${esc(D.statuses[i - 1])} / ${esc(D.pstatuses[i - 1])}</option>`).join("");
  $("dif").innerHTML = `<option value="all">Any difficulty</option>` + ["E", "M", "H", "X"].map(k => `<option value="${k}">${DIFF[k]}</option>`).join("");
  $("pat").innerHTML = `<option value="all">Any pattern</option>` + D.stages.map(s => {
    const opts = s.modules.flatMap(mi => D.modules[mi].items.filter(it => it.tag && D.tags[it.tag]).map(it => `<option value="${esc(it.tag)}">${esc(D.tags[it.tag][0])}</option>`));
    return opts.length ? `<optgroup label="${esc(s.short || s.name)}">${opts.join("")}</optgroup>` : "";
  }).join("");
  $("stagemap").innerHTML = D.stages.map((s, si) => `<li><a href="#s-${esc(s.key)}" data-s="${si}"><span class="sn">Stage ${si + 1} · <span class="st"></span></span><b>${esc(s.name)}</b><span class="sc"></span><span class="pb"><i></i></span></a></li>`).join("");

  const lessonRow = it => `<li class="it" id="${anchor(it.id)}" data-id="${esc(it.id)}" data-k="${it.k}"${it.tag ? ` data-tag="${esc(it.tag)}"` : ""} data-s="${esc((it.t + " " + it.g + " " + D.modules[it.mi].name).toLowerCase())}">` +
    `<button type="button" class="ck" aria-label="${esc("Mark done: " + it.t)}" aria-pressed="false"></button>` +
    `<details class="lz"><summary><span class="ih"><span class="ik">${KIND[it.k]} ${it.n}</span><span class="tt">${esc(it.t)}</span><span class="tm">${esc(it.tm)}</span></span><span class="g">${esc(it.g)}</span></summary><div class="lb"></div></details></li>`;

  const statusButtons = (pid) => `<span class="pst" role="group" aria-label="${esc("Status of " + rec(pid)[0])}">${[1, 2, 3].map(c => `<button type="button" class="b b${c}" data-c="${c}" aria-pressed="false" title="${esc(PTIP[c])}">${esc(PSTAT[c])}</button>`).join("")}</span>`;
  const patChip = pid => {
    const p = probs.get(pid), t = p && D.tags[p.pat];
    return t && p.tier !== "mixed" ? `<a class="pat" href="#${anchor(t[1])}" data-go="${esc(t[1])}" title="Open the card this problem relies on">${esc(t[0])}</a>` : "";
  };
  function probRow(pid) {
    const p = probs.get(pid), d = pdiff(pid), r = rec(pid);
    const search = esc((pid + " " + r[0] + " " + D.modules[p.mi].name + " " + (p.tier !== "mixed" && D.tags[p.pat] ? D.tags[p.pat][0] : "")).toLowerCase());
    const head = `<span class="df df-${d}">${esc(isLc(pid) ? DIFF[d] : r[1])}</span>${TIER[p.tier] ? `<span class="tier t-${p.tier}">${TIER[p.tier]}</span>` : ""}`;
    if (p.tier === "bank") {
      return `<li class="pr plain" id="${panchor(pid)}" data-id="${esc(pid)}" data-k="prob" data-f="${d}" data-s="${search}"><div class="ph">` +
        `<span class="pt">${isLc(pid) ? `<span class="nb">${esc(pid)}</span>` : ""}${A(original(pid), r[0], "pn")}${head}</span>` +
        `<span class="lk">${deeper(pid).map(([t, h]) => A(h, t.split(":")[0].replace(/ \(doocs\)$/, ""))).join("")}</span>${statusButtons(pid)}</div></li>`;
    }
    return `<li class="pr" id="${panchor(pid)}" data-id="${esc(pid)}" data-k="prob" data-f="${d}" data-pat="${esc(p.tier === "mixed" ? "" : p.pat)}" data-s="${search}"><div class="ph">` +
      `<button type="button" class="px" aria-expanded="false" aria-controls="pb-${panchor(pid)}"><span class="chev" aria-hidden="true"></span>${isLc(pid) ? `<span class="nb">${esc(pid)}</span>` : ""}<span class="pn">${esc(r[0])}</span></button>` +
      `<span class="pmeta">${head}${patChip(pid)}<span class="tm">${pmins(pid)} min</span></span>${statusButtons(pid)}</div>` +
      `<div class="pbody" id="pb-${panchor(pid)}" hidden></div></li>`;
  }

  const lists = (h, xs, c) => xs.length ? `<div${c ? ` class="${c}"` : ""}><h4>${esc(h)}</h4><ul>${xs.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>` : "";
  const cardMins = m => m.items.filter(i => i.k !== "build").reduce((a, i) => a + i.m, 0);
  const probMins = m => m.practice.reduce((a, p) => a + pmins(p.id), 0);
  const modMeta = m => {
    const c = k => m.items.filter(i => i.k === k).length;
    return [c("primer") && plural(c("primer"), "primer"), c("recap") && plural(c("recap"), "recap card"), c("lab") && plural(c("lab"), "lab"),
      m.practice.length && plural(m.practice.length, "problem"), c("build") && plural(c("build"), "project"),
      cardMins(m) && "~" + hm(cardMins(m)) + " of cards and labs", m.practice.length && "~" + hm(probMins(m)) + " of problems"].filter(Boolean).join(" · ");
  };
  const group = (m, ks, label) => {
    const its = m.items.filter(i => ks.includes(i.k));
    return its.length ? `<section class="grp" data-k="${ks[0]}"><h4 class="gh">${label} <span class="n"></span></h4><ol class="items">${its.map(lessonRow).join("")}</ol></section>` : "";
  };
  function practice(m) {
    if (!m.practice.length && !m.bank.length) return "";
    const ids = ts => m.practice.filter(p => ts.includes(p.t)).map(p => p.id);
    const ladder = ids(["core", "derive", "stretch"]);
    const byDiff = list => ["E", "M", "H", "X"].map(d => {
      const xs = list.filter(pid => pdiff(pid) === d);
      return xs.length ? `<h5 class="bh">${DIFF[d]} <span class="dn"></span></h5><ol class="items">${xs.map(probRow).join("")}</ol>` : "";
    }).join("");
    const sets = [...new Set(m.practice.filter(p => p.t === "mixed").map(p => p.after))].sort((a, b) => a - b);
    const mixed = sets.map((a, n) => `<h5 class="bh rset" data-after="${a}">Review set ${n + 1} · opens after ${a + 1}. ${esc(D.modules[a].name)} <span class="lockn"></span></h5>` +
      `<ol class="items">${m.practice.filter(p => p.t === "mixed" && p.after === a).map(p => probRow(p.id)).join("")}</ol>`).join("");
    const rule = ` Mark <b>${esc(D.pstatuses[0])}</b> only when you wrote the brute force and the optimal solution yourself.`;
    const bank = m.bank.length ? `<details class="bank"><summary>Later list: ${plural(m.bank.length, "more problem")} on these patterns <span class="n"></span></summary>` +
      `<p class="pnote">Extra repetitions from the original tracker, still tracked. They do not have in-page cards yet: use them for second passes once the ladder above is solid.</p>` +
      byDiff(m.bank) + `</details>` : "";
    return `<section class="grp prs" data-k="prob"><h4 class="gh">${sets.length ? "Mixed review sets" : "Problems"} <span class="n"></span></h4>` +
      (ladder.length ? `<p class="pnote">Solve first, check after. Read the card and original statement, then try it in your editor. Use the hints one at a time if stuck and open the solution after an honest attempt.${rule}</p>${byDiff(ladder)}` : "") +
      (mixed ? `<p class="pnote">No topic labels: deciding which idea applies is the skill being trained. Each set opens when you finish the module it follows; Today's session offers one at a time. The last hint names the pattern.${rule}</p>${mixed}` : "") + bank + `</section>`;
  }
  const module = (m, mi) => `<details class="mod" id="m-${esc(m.key)}" data-k="${esc(m.key)}"><summary><span class="mn">${mi + 1}</span><span class="mt"><h3>${esc(m.name)}</h3><span class="ms">${esc(m.summary)}</span><span class="mm">${esc(modMeta(m))}</span></span><span class="mc"></span><span class="pb"><i></i></span></summary>` +
    `<div class="mintro"><div class="why"><h4>Why it matters</h4><p>${esc(m.why)}</p></div><div class="mg">${lists("You will be able to", m.outcomes)}${lists("Spot it", m.cues, "cue")}${lists("Common traps", m.traps)}${lists("In real systems", m.systems)}</div></div>` +
    `<div class="apply">${group(m, ["recap"], "Recap cards")}${group(m, ["primer"], "Primers")}${group(m, ["lab"], "Labs")}${practice(m)}${group(m, ["build"], "Project")}` +
    (m.further.length ? `<details class="further"><summary>Go further: optional chapters and long reads</summary><ul>${m.further.map(f => `<li><span class="fk">${esc(f.k)}</span>${A(f.h, f.t)}</li>`).join("")}</ul></details>` : "") +
    `<p class="empty" hidden>Nothing here matches the current filters.</p></div></details>`;

  $("mods").innerHTML = D.stages.map((s, si) => {
    const ms = s.modules.map(mi => D.modules[mi]);
    const cm = ms.reduce((a, m) => a + cardMins(m), 0), pm = ms.reduce((a, m) => a + probMins(m), 0);
    const np = ms.reduce((a, m) => a + m.practice.length, 0);
    return `<section class="stage" id="s-${esc(s.key)}" data-s="${si}"><header class="sh"><p class="sk">Stage ${si + 1} · ${plural(s.modules.length, "module")} · ~${hm(cm)} of cards and labs${np ? ` · ${plural(np, "problem")} (~${hm(pm)})` : ""}</p><h2>${esc(s.name)}</h2><p>${esc(s.intro)}</p></header>${s.modules.map(mi => module(D.modules[mi], mi)).join("")}</section>`;
  }).join("");
  $("rail").innerHTML = D.stages.map((s, si) => `<li class="rs">Stage ${si + 1} · ${esc(s.short || s.name)}</li>` + s.modules.map(mi => `<li class="rm"><a href="#m-${esc(D.modules[mi].key)}" data-k="${esc(D.modules[mi].key)}"><span class="rn">${mi + 1}</span><span class="rt">${esc(D.modules[mi].name)}</span><span class="rc"></span><span class="rb"><b></b></span></a></li>`).join("")).join("");
  $("jump").innerHTML = `<option value="">Jump to module</option>` + D.stages.map((s, si) => `<optgroup label="Stage ${si + 1}: ${esc(s.name)}">${s.modules.map(mi => `<option value="${esc(D.modules[mi].key)}">${mi + 1}. ${esc(D.modules[mi].name)}</option>`).join("")}</optgroup>`).join("");
  $("projDesc").textContent = D.projects;
  $("projList").innerHTML = builds.map(it => `<li data-id="${esc(it.id)}"><a href="#${anchor(it.id)}" data-go="${esc(it.id)}">${esc(it.t)}</a> <span class="am">${esc(D.modules[it.mi].name)} · ${esc(it.tm)}${it.ms ? ` · <span class="msn"></span>` : ""}</span></li>`).join("");
  $("projects").hidden = !builds.length;

  const rows = [...document.querySelectorAll(".it")];
  const rowOf = new Map(rows.map(li => [li.dataset.id, li]));
  const prows = [...document.querySelectorAll(".pr")];
  const prow = new Map(prows.map(li => [li.dataset.id, li]));
  const mods = [...document.querySelectorAll(".mod")];
  const stages = [...document.querySelectorAll(".stage")];
  const railMods = [...document.querySelectorAll("#rail .rm")];
  const mapStages = [...document.querySelectorAll("#stagemap li")];

  // ---------- content (one data-only script per module, loaded on first use) ----------
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
  function enhance(scope) {
    scope.querySelectorAll(".trace:not(.js)").forEach(s => {
      const li = [...s.querySelectorAll(":scope > ol > li")];
      let i = 0;
      s.classList.add("js");
      const bar = document.createElement("div");
      bar.className = "sx";
      bar.innerHTML = `<button type="button" class="btn sp-prev" aria-label="Previous step">&larr; Back</button><span class="sxn" aria-live="polite"></span><button type="button" class="btn pri sp-next" aria-label="Next step">Next &rarr;</button><button type="button" class="btn quiet sp-all" aria-pressed="false">Show all steps</button>`;
      s.prepend(bar);
      const show = () => {
        const all = s.classList.contains("all");
        li.forEach((x, j) => { x.hidden = !all && j !== i; });
        bar.querySelector(".sxn").textContent = all ? `All ${li.length} steps` : `Step ${i + 1} of ${li.length}`;
        bar.querySelector(".sp-prev").disabled = all || i === 0;
        bar.querySelector(".sp-next").disabled = all || i === li.length - 1;
        bar.querySelector(".sp-all").setAttribute("aria-pressed", all);
        bar.querySelector(".sp-all").textContent = all ? "One step at a time" : "Show all steps";
      };
      bar.addEventListener("click", e => {
        const b = e.target.closest("button");
        if (!b) return;
        if (b.classList.contains("sp-prev") && i > 0) i--;
        else if (b.classList.contains("sp-next") && i < li.length - 1) i++;
        else if (b.classList.contains("sp-all")) s.classList.toggle("all");
        show();
      });
      show();
    });
    scope.querySelectorAll(".code:not(.js)").forEach(c => {
      c.classList.add("js");
      if (!navigator.clipboard) return;
      const b = document.createElement("button");
      b.type = "button";
      b.className = "cp";
      b.textContent = "Copy";
      b.addEventListener("click", () => {
        navigator.clipboard.writeText(c.querySelector("pre").textContent).then(() => {
          b.textContent = "Copied";
          setTimeout(() => { b.textContent = "Copy"; }, 1500);
        }, () => { b.textContent = "Copy failed"; });
      });
      c.append(b);
    });
  }
  // A project's numbered milestones become checkboxes, each saved like any other item.
  function milestoneBoxes(scope, it) {
    if (!it.ms) return;
    const h = [...scope.querySelectorAll(".lc h4")].find(x => x.textContent.trim() === "Milestones");
    const ol = h && h.nextElementSibling && h.nextElementSibling.tagName === "OL" ? h.nextElementSibling : null;
    if (!ol) return;
    ol.classList.add("msl");
    [...ol.children].slice(0, it.ms).forEach((li, k) => {
      const id = it.id + "#m" + (k + 1);
      li.dataset.mid = id;
      li.insertAdjacentHTML("afterbegin", `<button type="button" class="mck" data-mid="${esc(id)}" aria-pressed="false" aria-label="Milestone ${k + 1} done"></button>`);
    });
  }
  function practiseList(it) {
    const ids = [...new Set([...(it.tag ? byPattern.get(it.tag) || [] : []), ...it.p])];
    if (!ids.length) return "";
    return `<aside class="now"><h4>Problems that practise this</h4><ul class="pl">${ids.map(pid => `<li data-pid="${esc(pid)}"><a href="#${panchor(pid)}" data-go="${esc(pid)}">${esc(pname(pid))}</a> <span class="df df-${pdiff(pid)}">${esc(DIFF[pdiff(pid)])}</span>${it.p.includes(pid) ? ` <span class="labm">in the Lab</span>` : ""}<span class="pls"></span></li>`).join("")}</ul></aside>`;
  }
  function body(it, html) {
    const src = it.src.length ? `<aside class="src"><h4>${it.k === "build" ? "References" : "Go deeper (optional)"}</h4><ul>${it.src.map(s => `<li>${A(s.h, s.t)}${s.n ? `<span> · ${esc(s.n)}</span>` : ""}</li>`).join("")}</ul></aside>` : "";
    const next = it.k === "build" ? "Done" : "Done, next card";
    return `<div class="lc">${html}</div>${practiseList(it)}${src}<div class="lf"><button type="button" class="btn pri nx">${next} <span aria-hidden="true">&rarr;</span></button><button type="button" class="btn st" data-c="2" aria-pressed="false">Needs practice</button><button type="button" class="btn st" data-c="3" aria-pressed="false">Revisit later</button><button type="button" class="btn quiet cx">Close</button></div>`;
  }
  const failed = '<p class="ld" role="alert">This content could not be loaded or is incomplete. Check your connection and <button type="button" class="linkish rt">try again</button>.</p>';
  function fill(li) {
    const it = byId.get(li.dataset.id), b = li.querySelector(".lb"), key = D.modules[it.mi].key;
    if (!b.dataset.ok) {
      if (!content.has(key)) {
        b.innerHTML = '<p class="ld" role="status">Loading&hellip;</p>';
        loadModule(it.mi).then(() => fill(li), () => { b.innerHTML = failed; });
        return;
      }
      const html = content.get(key)[it.id];
      if (typeof html !== "string") {
        content.delete(key); loading.delete(key);
        b.innerHTML = failed;
        return;
      }
      // Card HTML is generated at build time by mdlite.py, which escapes all text and allows only https links.
      b.innerHTML = body(it, html);
      b.dataset.ok = "1";
      enhance(b);
      milestoneBoxes(b, it);
    }
    paintRow(li);
  }
  function fillProb(li) {
    const pid = li.dataset.id, p = probs.get(pid), b = li.querySelector(".pbody"), key = D.modules[p.mi].key;
    if (b.dataset.ok) return;
    if (!content.has(key)) {
      b.innerHTML = '<p class="ld" role="status">Loading&hellip;</p>';
      loadModule(p.mi).then(() => fillProb(li), () => { b.innerHTML = failed; });
      return;
    }
    const html = content.get(key)["p:" + pid];
    if (typeof html !== "string") {
      content.delete(key); loading.delete(key);
      b.innerHTML = failed;
      return;
    }
    const orig = `<p class="po">${A(original(pid), (isLc(pid) ? "Open LeetCode " + pid : "Open the original on " + rec(pid)[1]) + " (free) ↗")} <span>to read the official statement and submit.</span></p>`;
    const links = `<aside class="src"><h4>Go deeper (optional)</h4><ul>${deeper(pid).map(([t, h]) => { const [a, ...n] = t.split(": "); return `<li>${A(h, a)}${n.length ? `<span> · ${esc(n.join(": "))}</span>` : ""}</li>`; }).join("")}</ul></aside>`;
    // Problem cards are build output from mdlite.py (escaped text, https links only), like card bodies.
    const note = p.card ? "" : '<p class="pnote">Full in-page solution not yet available. Use the hints below and the reference links after your attempt.</p>';
    b.innerHTML = orig + note + html + links +
      `<div class="lf"><span class="lfn">How did it go?</span>${statusButtons(pid)}<button type="button" class="btn quiet pcx">Close</button></div>`;
    b.dataset.ok = "1";
    enhance(b);
    paintProb(li);
  }
  function openedModule(d) {
    loadModule(mods.indexOf(d)).catch(() => { /* retried when a card opens */ });
  }

  // ---------- painting ----------
  function visible(li) {
    const id = li.dataset.id, s = statusOf(id), k = li.dataset.k, prob = k === "prob";
    const f = $("flt").value, dif = $("dif").value, pat = $("pat").value, q = $("q").value.trim().toLowerCase();
    const kOk = view === "all" || view === "review" || (view === "learn" && (k === "primer" || k === "recap" || k === "lab")) ||
      (view === "practice" && prob) || (view === "build" && k === "build");
    const rOk = view !== "review" || s === 2 || s === 3;
    const sOk = f === "all" || +f === s;
    const dOk = dif === "all" || (prob && li.dataset.f === dif);
    const pOk = pat === "all" || (prob ? li.dataset.pat === pat : li.dataset.tag === pat);
    return kOk && rOk && sOk && dOk && pOk && (!q || li.dataset.s.includes(q));
  }
  function paintRow(li) {
    const s = statusOf(li.dataset.id);
    li.dataset.st = s;
    li.querySelector(".ck").setAttribute("aria-pressed", s === 1);
    li.querySelector(".ck").title = LSTAT[s];
    li.querySelectorAll(".lf .st").forEach(b => b.setAttribute("aria-pressed", +b.dataset.c === s));
    const nx = li.querySelector(".nx");
    if (nx) nx.firstChild.textContent = (s === 1 ? "Done ✓ · next" : (li.dataset.k === "build" ? "Done" : "Done, next card")) + " ";
    li.querySelectorAll(".mck").forEach(b => {
      const on = statusOf(b.dataset.mid) === 1;
      b.setAttribute("aria-pressed", on);
      b.parentElement.classList.toggle("msd", on);
    });
    li.querySelectorAll(".pl li").forEach(x => { const st = statusOf(x.dataset.pid); x.dataset.st = st; x.querySelector(".pls").textContent = st ? " · " + PSTAT[st] : ""; });
  }
  function paintProb(li) {
    const s = statusOf(li.dataset.id);
    li.dataset.st = s;
    li.querySelectorAll(".pst .b").forEach(b => b.setAttribute("aria-pressed", +b.dataset.c === s));
  }
  const filtering = () => view !== "all" || $("flt").value !== "all" || $("dif").value !== "all" || $("pat").value !== "all" || !!$("q").value.trim();

  function paint() {
    const filtered = filtering();
    rows.forEach(li => { paintRow(li); li.hidden = !visible(li); });
    prows.forEach(li => { paintProb(li); li.hidden = !visible(li); });
    mods.forEach((d, i) => {
      const m = D.modules[i];
      const vis = [...d.querySelectorAll(".it, .pr")].filter(x => !x.hidden).length;
      const tracked = [...m.items.map(it => it.id), ...m.practice.map(p => p.id)];
      const done = tracked.filter(id => statusOf(id) === 1).length, pct = tracked.length ? done / tracked.length * 100 : 0;
      d.querySelectorAll(".grp").forEach(g => {
        const all = [...g.querySelectorAll(".it, .pr")];
        const counted = g.dataset.k === "prob" ? all.filter(x => !x.closest(".bank")) : all;
        g.hidden = all.every(x => x.hidden);
        g.querySelector(".gh .n").textContent = counted.length ? counted.filter(x => statusOf(x.dataset.id) === 1).length + "/" + counted.length : "";
        g.querySelectorAll(".bh").forEach(h => {
          const ol = h.nextElementSibling;
          if (!ol) return;
          const xs = [...ol.querySelectorAll(".pr")];
          h.hidden = xs.every(x => x.hidden);
          const dn = h.querySelector(".dn");
          if (dn) dn.textContent = xs.filter(x => statusOf(x.dataset.id) === 1).length + "/" + xs.length;
        });
      });
      d.querySelectorAll(".rset").forEach(h => {
        const open = lessonsDone(+h.dataset.after);
        h.classList.toggle("locked", !open);
        h.querySelector(".lockn").textContent = open ? "· open" : "· not open yet";
      });
      d.querySelectorAll(".bank").forEach(b => {
        const bl = [...b.querySelectorAll(".pr")];
        b.querySelector("summary .n").textContent = bl.filter(x => statusOf(x.dataset.id) === 1).length + " solved";
        if (filtered && bl.some(x => !x.hidden)) b.open = true;
      });
      d.querySelector(".mc").textContent = done + "/" + tracked.length;
      d.querySelector(".pb i").style.width = pct + "%";
      d.querySelector(".empty").hidden = vis > 0;
      d.hidden = filtered && vis === 0;
      d.classList.toggle("done", tracked.length > 0 && done === tracked.length);
      if (vis && ($("q").value.trim() || $("dif").value !== "all" || $("pat").value !== "all" || view === "review")) d.open = true;
      const r = railMods[i];
      r.querySelector(".rc").textContent = done + "/" + tracked.length;
      r.querySelector(".rb b").style.width = pct + "%";
      r.classList.toggle("dim", d.hidden);
      r.classList.toggle("done", tracked.length > 0 && done === tracked.length);
    });
    stages.forEach((s, si) => {
      s.hidden = [...s.querySelectorAll(".mod")].every(d => d.hidden);
      const mis = D.stages[si].modules;
      const its = mis.flatMap(mi => D.modules[mi].items), ps = mis.flatMap(mi => D.modules[mi].practice.map(p => p.id));
      const di = its.filter(i => statusOf(i.id) === 1).length, dp = ps.filter(id => statusOf(id) === 1).length;
      const left = its.filter(i => i.k !== "build" && statusOf(i.id) !== 1).reduce((a, i) => a + i.m, 0);
      const ms = mapStages[si];
      ms.querySelector(".st").textContent = left ? "~" + hm(left) + " left" : its.length ? "cards done" : "";
      ms.querySelector(".sc").textContent = `${di}/${its.length} cards · ${dp}/${ps.length} problems`;
      ms.querySelector(".pb i").style.width = (its.length + ps.length ? (di + dp) / (its.length + ps.length) * 100 : 0) + "%";
      ms.classList.toggle("done", its.length + ps.length > 0 && di + dp === its.length + ps.length);
    });
    paintStats();
    paintSession();
    const bd = builds.filter(it => statusOf(it.id) === 1).length;
    $("projCount").textContent = `${bd} of ${builds.length} built`;
    $("projFill").style.width = (builds.length ? bd / builds.length * 100 : 0) + "%";
    $("projList").querySelectorAll("li").forEach(li => {
      const it = byId.get(li.dataset.id);
      li.dataset.st = statusOf(it.id);
      const n = li.querySelector(".msn");
      if (n) n.textContent = msDone(it) + "/" + it.ms + " milestones";
    });
  }
  const msDone = it => { let n = 0; for (let k = 1; k <= (it.ms || 0); k++) if (statusOf(it.id + "#m" + k) === 1) n++; return n; };

  function paintStats() {
    const done = l => l.filter(id => statusOf(id) === 1).length;
    const cards = order.filter(it => it.k === "primer" || it.k === "recap").map(it => it.id);
    const labs = order.filter(it => it.k === "lab").map(it => it.id);
    const core = practiced.map(p => p.pid), bank = [...probs.values()].filter(p => p.tier === "bank").map(p => p.pid);
    const all = [...order.map(it => it.id), ...core];
    $("fill").style.width = (all.length ? done(all) / all.length * 100 : 0) + "%";
    const left = learnOrder.filter(it => statusOf(it.id) !== 1).reduce((a, it) => a + it.m, 0);
    const review = allIds.filter(id => statusOf(id) === 2 || statusOf(id) === 3).length;
    $("stats").innerHTML = `<span>Cards <b>${done(cards)}</b>/${cards.length}</span><span>Labs <b>${done(labs)}</b>/${labs.length}</span>` +
      `<span>Problems solved <b>${done(core)}</b>/${core.length}</span><span>Projects <b>${done(builds.map(it => it.id))}</b>/${builds.length}</span>` +
      `<span>Later list <b>${done(bank)}</b>/${bank.length}</span><span>To review <b>${review}</b></span><span>About <b>${hm(left)}</b> of cards and labs left</span>`;
  }

  // ---------- today's session ----------
  // Planned once a day and kept, so you can see when you are finished: about 30 minutes of new cards (or one lab),
  // one problem on an idea you have already met, and one review item: the oldest item marked Brute only / Stuck or
  // Needs practice / Revisit at least three days ago, or else the next problem of an open mixed review set.
  const SKEY = "study-session:" + D.storageKey;
  const today = () => { const d = new Date(); return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate(); };
  let plan = null;
  function loadPlan() {
    try {
      const p = JSON.parse(localStorage.getItem(SKEY) || "null");
      if (p && p.day === today() && Array.isArray(p.learn) && Array.isArray(p.practice) && Array.isArray(p.review) && Number.isSafeInteger(p.made)) {
        const ok = id => typeof id === "string" && (byId.has(id) || probs.has(id));
        if ([...p.learn, ...p.practice, ...p.review].every(ok)) return p;
      }
    } catch (e) { /* replanned below */ }
    return null;
  }
  function savePlan() { try { localStorage.setItem(SKEY, JSON.stringify(plan)); } catch (e) { /* optional */ } }
  function ready(p) {
    if (statusOf(p.pid) !== 0 || p.tier === "stretch" || p.tier === "bank" || p.tier === "mixed") return false;
    if (p.lessons.length) return p.lessons.some(id => statusOf(id) === 1);
    const tagged = D.tags[p.pat];
    if (tagged) return statusOf(tagged[1]) === 1;
    return lessonsDone(p.mi);
  }
  function makePlan() {
    const learn = [];
    let budget = 0;
    for (const it of learnOrder) {
      if (M.has(it.id)) continue;
      if (learn.length && (budget + it.m > 32 || it.k === "lab" || byId.get(learn[0]).k === "lab")) break;
      learn.push(it.id);
      budget += it.m;
    }
    const soon = new Set(learn);
    const practice = practiced.filter(p => ready(p) || (statusOf(p.pid) === 0 && p.tier !== "stretch" && p.tier !== "mixed" && (p.lessons.some(id => soon.has(id)) || (D.tags[p.pat] && soon.has(D.tags[p.pat][1])))))
      .sort((a, b) => a.mi - b.mi || a.i - b.i).slice(0, learn.length ? 1 : 2).map(p => p.pid);
    const due = Date.now() - REVIEW_DAYS * 86400000;
    const dueList = Object.entries(E).filter(([id, e]) => (e.status === 2 || e.status === 3) && e.updatedAt < due && (byId.has(id) || probs.has(id)))
      .sort((a, b) => a[1].updatedAt - b[1].updatedAt).map(([id]) => id);
    const mixed = practiced.filter(p => p.tier === "mixed" && statusOf(p.pid) === 0 && p.after >= 0 && lessonsDone(p.after))
      .sort((a, b) => a.after - b.after || a.i - b.i).map(p => p.pid);
    const review = [...dueList, ...mixed].slice(0, 1);
    plan = { day: today(), made: Date.now(), learn, practice, review };
    savePlan();
  }
  const touched = id => { const e = E[id]; return !!e && e.status !== 0 && e.updatedAt >= plan.made; };
  const planIds = () => [...plan.learn, ...plan.practice, ...plan.review];
  const itemMins = id => byId.has(id) ? byId.get(id).m : pmins(id);
  function planLine(id, why) {
    const done = touched(id);
    if (byId.has(id)) {
      const it = byId.get(id);
      return `<li class="${done ? "ok" : ""}"><a href="#${anchor(id)}" data-go="${esc(id)}"><span class="qk">${why ? "Review: " + KIND[it.k] : KIND[it.k]} · ${esc(it.tm)}</span><b>${esc(it.t)}</b><span class="qm">${esc(D.modules[it.mi].name)}</span></a></li>`;
    }
    const p = probs.get(id), d = pdiff(id);
    const kind = p.tier === "mixed" ? "Mixed review, topic hidden" : why ? "Re-solve from a blank file" : "Problem";
    const where = p.tier === "mixed" ? "Work out which idea applies" : D.tags[p.pat] ? D.tags[p.pat][0] : D.modules[p.mi].name;
    return `<li class="${done ? "ok" : ""}"><a href="#${panchor(id)}" data-go="${esc(id)}"><span class="qk">${kind} · ${DIFF[d]} · ${pmins(id)} min</span><b>${esc(pname(id))}</b><span class="qm">${esc(where)}</span></a></li>`;
  }
  function paintSession() {
    if (!plan || plan.day !== today()) { plan = loadPlan(); if (!plan) makePlan(); }
    const ids = planIds(), done = ids.filter(touched).length;
    const sec = (h, list, why) => list.length ? `<h3 class="qh">${h}</h3><ol class="queue">${list.map(id => planLine(id, why)).join("")}</ol>` : "";
    $("plan").innerHTML = sec("Learn", plan.learn) + sec("Practise", plan.practice) + sec("Review", plan.review, true) ||
      `<p class="today">Everything in the guide is done. Use the Review view and the Later lists to stay sharp.</p>`;
    const mins = ids.reduce((a, id) => a + itemMins(id), 0);
    $("qtime").textContent = ids.length ? "About " + hm(mins) : "";
    $("sfill").style.width = (ids.length ? done / ids.length * 100 : 0) + "%";
    const complete = ids.length > 0 && done === ids.length;
    $("today").textContent = complete ? "Session complete. Well done: stop here, or plan another session if you have time."
      : done ? `${done} of ${ids.length} done in this session.` : ids.length ? "Work top to bottom; each item ticks off when you mark it." : "";
    $("start").hidden = complete || !ids.length;
    $("start").textContent = done ? "Continue the session" : M.size ? "Start today's session" : "Start the first card";
    $("replan").hidden = !complete;
    const nb = builds.find(it => statusOf(it.id) !== 1 && lessonsDone(it.mi));
    $("pjnext").hidden = !nb;
    if (nb) {
      const k = nb.ms ? msDone(nb) : 0;
      $("pjnext").innerHTML = `Project ready: <a href="#${anchor(nb.id)}" data-go="${esc(nb.id)}">${esc(nb.t)}</a> (${esc(nb.tm)}${nb.ms ? `, milestone ${Math.min(k + 1, nb.ms)} of ${nb.ms} next` : ""}). Give it its own sessions: one milestone is one to two hours.`;
    }
  }

  // ---------- navigation ----------
  function remember(m) {
    try { localStorage.setItem("study-last:" + D.storageKey, m.name.slice(0, 120)); } catch (e) { /* optional */ }
  }
  function clearFilters() {
    $("flt").value = "all"; $("dif").value = "all"; $("pat").value = "all"; $("q").value = ""; view = "all";
    $("seg").querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x.dataset.v === "all"));
    paint();
  }
  function flash(el) {
    el.classList.remove("flash");
    void el.offsetWidth;
    el.classList.add("flash");
  }
  // Opening a card closes the others (one card at a time). Cards above it shrink when they close, so the page is
  // scrolled by the same amount to keep the header you opened exactly where it was: the card expands below it.
  function closeOthers(keep, header) {
    const top = header.getBoundingClientRect().top;
    document.querySelectorAll(".lz[open]").forEach(o => { if (o !== keep) o.open = false; });
    document.querySelectorAll(".px[aria-expanded=true]").forEach(b => { if (b !== keep) setProb(b.closest(".pr"), false); });
    const shift = header.getBoundingClientRect().top - top;
    if (Math.abs(shift) > 1) window.scrollBy(0, shift);
  }
  function setProb(li, open) {
    const b = li.querySelector(".px"), pb = li.querySelector(".pbody");
    if (!b) return;
    b.setAttribute("aria-expanded", open);
    pb.hidden = !open;
    li.classList.toggle("open", open);
    if (open) fillProb(li);
  }
  const atTop = el => { const r = el.getBoundingClientRect(); return r.top >= 0 && r.top < innerHeight * 0.6; };
  function openItem(id, focus = true) {
    if (probs.has(id)) return openProb(id, focus);
    if (milestones.has(id)) id = milestones.get(id).id;
    const li = rowOf.get(id);
    if (!li) return;
    if (li.hidden) clearFilters();
    li.closest(".mod").open = true;
    li.querySelector(".lz").open = true;
    fill(li);
    li.scrollIntoView({ block: "start" });
    if (focus) li.querySelector("summary").focus({ preventScroll: true });
  }
  function openProb(id, focus = true) {
    const li = prow.get(id);
    if (!li) return;
    if (li.hidden) clearFilters();
    const bank = li.closest(".bank");
    if (bank) bank.open = true;
    li.closest(".mod").open = true;
    const b = li.querySelector(".px");
    if (b) {
      setProb(li, true);
      closeOthers(b, b);
    }
    li.scrollIntoView({ block: "start" });
    flash(li);
    const f = b || li.querySelector(".pn");
    if (focus) f.focus({ preventScroll: true });
  }
  function openMod(k) {
    const d = $("m-" + k);
    if (d) { d.hidden = false; d.open = true; d.scrollIntoView({ block: "start" }); }
  }
  const nextCard = (after = -1) => learnOrder.find(it => it.pos > after && !M.has(it.id));

  $("mods").addEventListener("toggle", e => {
    const t = e.target;
    if (t.classList.contains("lz")) {
      const li = t.closest(".it");
      if (t.open) {
        fill(li);
        closeOthers(t, t.querySelector("summary"));
        history.replaceState(null, "", "#" + li.id);
        remember(D.modules[byId.get(li.dataset.id).mi]);
      }
    } else if (t.classList.contains("mod") && t.open) {
      remember(D.modules[mods.indexOf(t)]);
      openedModule(t);
    }
  }, true);

  $("mods").addEventListener("click", e => {
    const go = e.target.closest("a[data-go]");
    if (go) { e.preventDefault(); openItem(go.dataset.go); return; }
    const pb = e.target.closest(".pst .b");
    if (pb) {
      const id = pb.closest(".pr").dataset.id, c = +pb.dataset.c;
      progress.set(id, statusOf(id) === c ? 0 : c);
      return;
    }
    const px = e.target.closest(".px");
    if (px) {
      const li = px.closest(".pr"), open = px.getAttribute("aria-expanded") !== "true";
      setProb(li, open);
      if (open) {
        closeOthers(px, px);
        history.replaceState(null, "", "#" + li.id);
        remember(D.modules[probs.get(li.dataset.id).mi]);
      }
      return;
    }
    if (e.target.closest(".pcx")) {
      const li = e.target.closest(".pr");
      setProb(li, false);
      if (!atTop(li)) li.scrollIntoView({ block: "nearest" });
      li.querySelector(".px").focus({ preventScroll: true });
      return;
    }
    const mck = e.target.closest(".mck");
    if (mck) {
      progress.set(mck.dataset.mid, statusOf(mck.dataset.mid) === 1 ? 0 : 1);
      return;
    }
    const retry = e.target.closest(".rt");
    if (retry) {
      const problem = retry.closest(".pr");
      if (problem) fillProb(problem);
      else {
        const item = retry.closest(".it");
        if (item) fill(item);
      }
      return;
    }
    const li = e.target.closest(".it");
    if (!li) return;
    const id = li.dataset.id, s = statusOf(id);
    if (e.target.closest(".ck")) {
      progress.set(id, s === 1 ? 0 : 1);
    } else if (e.target.closest(".nx")) {
      if (s !== 1) progress.set(id, 1);
      li.querySelector(".lz").open = false;
      const it = byId.get(id);
      const nx = it.k === "build" ? null : nextCard(it.pos);
      if (nx) openItem(nx.id);
      else li.scrollIntoView({ block: "center" });
    } else if (e.target.closest(".lf .st")) {
      const c = +e.target.closest(".st").dataset.c;
      progress.set(id, s === c ? 0 : c);
    } else if (e.target.closest(".cx")) {
      li.querySelector(".lz").open = false;
      if (!atTop(li)) li.scrollIntoView({ block: "nearest" });
      li.querySelector("summary").focus({ preventScroll: true });
    }
  });
  // Escape closes the card that has focus and returns focus to its header.
  $("mods").addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    const pr = e.target.closest(".pr.open"), it = e.target.closest(".it");
    if (pr) { setProb(pr, false); pr.querySelector(".px").focus(); e.preventDefault(); }
    else if (it && it.querySelector(".lz").open) { it.querySelector(".lz").open = false; it.querySelector("summary").focus(); e.preventDefault(); }
  });

  $("seg").addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b) return;
    view = b.dataset.v;
    $("seg").querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b));
    paint();
  });
  ["flt", "dif", "pat"].forEach(id => $(id).addEventListener("change", paint));
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
  const go = e => {
    const a = e.target.closest("a[data-go]");
    if (!a) return;
    e.preventDefault();
    openItem(a.dataset.go);
  };
  $("plan").addEventListener("click", go);
  $("pjnext").addEventListener("click", go);
  $("projList").addEventListener("click", go);
  $("jump").addEventListener("change", e => { if (e.target.value) openMod(e.target.value); e.target.value = ""; });
  $("tog").addEventListener("click", () => {
    const open = !mods.filter(d => !d.hidden).every(d => d.open);
    mods.forEach(d => { d.open = open; });
    $("tog").textContent = open ? "Collapse all" : "Expand all";
  });
  $("start").addEventListener("click", () => {
    const id = planIds().find(x => !touched(x));
    if (id) openItem(id);
  });
  $("replan").addEventListener("click", () => { makePlan(); paint(); });
  $("next").addEventListener("click", () => { const it = nextCard(); if (it) openItem(it.id); });

  const progress = StudyProgress.mount({
    storageKey: D.storageKey,
    ids: allIds,
    onChange(entries) {
      E = entries;
      M.clear();
      Object.entries(entries).forEach(([id, e]) => { if (e.status && (byId.has(id) || probs.has(id) || milestones.has(id))) M.set(id, e.status); });
      paint();
    }
  });

  function fromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    if (!h) return false;
    const el = document.getElementById(h);
    if (el && el.classList.contains("it")) { openItem(el.dataset.id, false); return true; }
    if (el && el.classList.contains("pr")) { openProb(el.dataset.id, false); return true; }
    if (h.startsWith("m-") && el) { openMod(h.slice(2)); return true; }
    if (h.startsWith("s-") && el) { el.scrollIntoView({ block: "start" }); return true; }
    return false;
  }
  // Keep opened cards clear of the sticky bars, whatever height the controls wrap to.
  function pad() {
    const bar = document.querySelector(".ctl");
    const sticky = getComputedStyle(bar).position === "sticky";
    document.documentElement.style.scrollPaddingTop = (sticky ? bar.getBoundingClientRect().height + 66 : 66) + "px";
  }
  pad();
  window.addEventListener("resize", pad);
  window.addEventListener("hashchange", fromHash);
  if (!fromHash()) {
    const first = nextCard();
    (first ? rowOf.get(first.id).closest(".mod") : mods[0]).open = true;
  }
})();
