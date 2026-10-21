(function () {
  "use strict";
  // Refuse to render inside another site's frame (clickjacking); GitHub Pages cannot send frame-ancestors.
  if (window.top !== window.self) {
    document.documentElement.classList.add("framed");
    return;
  }

  function closeMenus(except) {
    document.querySelectorAll("details.menu[open]").forEach(d => { if (d !== except) d.open = false; });
  }
  document.addEventListener("click", e => {
    const menu = e.target.closest("details.menu");
    closeMenus(menu);
    if (menu && e.target.closest(".mi")) menu.open = false;
  });
  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    const open = document.querySelector("details.menu[open]");
    if (open) { open.open = false; open.querySelector("summary").focus(); }
  });

  function count(key) {
    try {
      const stored = JSON.parse(localStorage.getItem(key + ":v1") || "null");
      if (stored && stored.entries && typeof stored.entries === "object") {
        return Object.values(stored.entries).filter(e => e && e.status === 1).length;
      }
      const old = JSON.parse(localStorage.getItem(key) || "null");
      return old && Array.isArray(old.a) ? old.a.length : 0;
    } catch (e) {
      return 0;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const here = location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".appnav a").forEach(a => {
      if (a.getAttribute("href").replace("./", "") === here) a.setAttribute("aria-current", "page");
    });

    const tracks = window.STUDY_TRACKS || {};
    document.querySelectorAll("[data-track]").forEach(card => {
      const t = tracks[card.dataset.track];
      if (!t) return;
      const done = Math.min(count(card.dataset.track), t.total);
      const set = (sel, text) => { const el = card.querySelector(sel); if (el) el.textContent = text; };
      set("[data-f=topics]", String(t.topics));
      set("[data-f=total]", String(t.total));
      set("[data-f=done]", done + " of " + t.total + " " + t.unit);
      const bar = card.querySelector(".meter i");
      if (bar) bar.style.width = (t.total ? done / t.total * 100 : 0) + "%";
      let last = "";
      try { last = localStorage.getItem("study-last:" + card.dataset.track) || ""; } catch (e) { /* optional */ }
      const next = card.querySelector("[data-f=next]");
      if (next) {
        next.textContent = last && done ? "Continue with " + last : "Start with " + t.first;
      }
    });
  });
})();
