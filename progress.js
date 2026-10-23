(function (root) {
  "use strict";
  const SCOPE = "https://www.googleapis.com/auth/drive.appdata";
  const API = "https://www.googleapis.com/drive/v3/files";
  const UPLOAD = "https://www.googleapis.com/upload/drive/v3/files";
  const ABOUT = "https://www.googleapis.com/drive/v3/about?fields=user(emailAddress)";
  // Browser storage keys shared by every page of the site, so one sign-in and one sync cover all trackers.
  const HINT_KEY = "study-drive-account";
  const SESSION_KEY = "study-drive-session";
  const DEVICE_KEY = "study-drive-device";
  const DIRTY_KEY = "study-drive-dirty";
  const SYNCED_KEY = "study-drive-synced";
  const LOCK = "study-drive-sync";
  const SUFFIX = ":v1";
  // One Drive file per browser holds every tracker; older per-tracker files are still read, then retired.
  const BUNDLE_PROPERTY = "studyProgress";
  const BUNDLE_VERSION = "2";
  const TRACKER_PROPERTY = "studyTracker";
  const TRACKER_KEY = /^[a-z0-9][a-z0-9-]{0,62}$/;
  const MAX_ENTRIES = 20000;
  const MAX_ID_LENGTH = 120;
  const MAX_TRACKERS = 200;
  const MAX_TOKEN_LENGTH = 4096;
  const MAX_BACKUP_BYTES = 5 * 1024 * 1024;

  function validate(value, tracker) {
    if (!value || value.version !== 1 || value.tracker !== tracker ||
        !value.entries || typeof value.entries !== "object" || Array.isArray(value.entries)) {
      throw new Error("Invalid progress file or wrong tracker.");
    }
    const list = Object.entries(value.entries);
    if (list.length > MAX_ENTRIES) throw new Error("Progress file has too many entries.");
    const entries = Object.create(null);
    for (const [id, entry] of list) {
      if (!id || id.length > MAX_ID_LENGTH || !entry || !Number.isInteger(entry.status) ||
          entry.status < 0 || entry.status > 3 || !Number.isSafeInteger(entry.updatedAt) || entry.updatedAt < 0) {
        throw new Error("Invalid progress entry: " + id.slice(0, MAX_ID_LENGTH));
      }
      entries[id] = { status: entry.status, updatedAt: entry.updatedAt };
    }
    return entries;
  }

  // Accepts a whole-site file (version 2) or an older single-tracker file (version 1).
  function validateAll(value) {
    const all = Object.create(null);
    if (value && value.version === 1) {
      if (typeof value.tracker !== "string" || !TRACKER_KEY.test(value.tracker)) throw new Error("Invalid progress file.");
      all[value.tracker] = validate(value, value.tracker);
      return all;
    }
    if (!value || value.version !== 2 || !value.trackers || typeof value.trackers !== "object" || Array.isArray(value.trackers)) {
      throw new Error("Invalid progress file.");
    }
    const keys = Object.keys(value.trackers);
    if (keys.length > MAX_TRACKERS) throw new Error("Progress file has too many trackers.");
    for (const key of keys) {
      if (!TRACKER_KEY.test(key)) throw new Error("Invalid tracker name in progress file: " + key.slice(0, 64));
      all[key] = validate({ version: 1, tracker: key, entries: value.trackers[key] }, key);
    }
    return all;
  }

  function merge(...sources) {
    const entries = Object.create(null);
    for (const source of sources) {
      for (const [id, entry] of Object.entries(source)) {
        const previous = entries[id];
        if (!previous || entry.updatedAt > previous.updatedAt ||
            (entry.updatedAt === previous.updatedAt && entry.status > previous.status)) {
          entries[id] = { ...entry };
        }
      }
    }
    return entries;
  }

  function same(a, b) {
    const ids = Object.keys(a);
    return ids.length === Object.keys(b).length &&
      ids.every(id => b[id] && b[id].status === a[id].status && b[id].updatedAt === a[id].updatedAt);
  }
  function sameAll(a, b) {
    const keys = Object.keys(a);
    return keys.length === Object.keys(b).length && keys.every(key => b[key] && same(a[key], b[key]));
  }

  function legacy(value) {
    if (!value || !["a", "b", "c"].every(k => Array.isArray(value[k]))) {
      throw new Error("Invalid legacy progress.");
    }
    const entries = Object.create(null);
    ["c", "b", "a"].forEach((k, i) => value[k].forEach(id => {
      if (typeof id !== "string" && !Number.isInteger(id)) {
        throw new Error("Invalid legacy item ID.");
      }
      entries[String(id)] = { status: 3 - i, updatedAt: 0 };
    }));
    return entries;
  }

  function read(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }
  function write(key, value) {
    try {
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, value);
      return true;
    } catch (e) { return false; }
  }
  const plural = n => n + (n === 1 ? " tracker" : " trackers");
  function when(time) {
    const date = new Date(time);
    const clock = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    return date.toDateString() === new Date().toDateString()
      ? "at " + clock
      : "on " + date.toLocaleDateString([], { month: "short", day: "numeric" }) + " at " + clock;
  }

  // Trackers are found by their storage format rather than a fixed list, so new trackers sync with no
  // code changes. Keys that other apps on a shared origin (such as github.io) happen to use are skipped.
  function localTrackers() {
    const found = [];
    let names = [];
    try {
      for (let i = 0; i < localStorage.length; i++) names.push(localStorage.key(i));
    } catch (e) { names = []; }
    for (const name of names) {
      if (typeof name !== "string" || !name.endsWith(SUFFIX)) continue;
      const key = name.slice(0, -SUFFIX.length);
      if (!TRACKER_KEY.test(key)) continue;
      try {
        const value = JSON.parse(read(name));
        if (value && value.version === 1 && value.tracker === key) found.push(key);
      } catch (e) { /* not a tracker */ }
    }
    return found;
  }

  const GOOGLE_LOGO = '<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>';
  const ACCOUNT_HTML =
    '<details class="menu" id="backup-menu"><summary class="btn quiet">Backup</summary><div class="pop">' +
    '<p class="pop-h">Backup and restore</p><p class="pop-note" id="local-status" role="status"></p>' +
    '<button type="button" class="mi" id="export-progress">Export all progress as a JSON file</button>' +
    '<button type="button" class="mi" id="import-progress">Import a backup file</button>' +
    '<input type="file" id="progress-file" accept=".json,application/json" hidden></div></details>' +
    '<button type="button" class="gbtn" id="drive-connect">' + GOOGLE_LOGO +
    '<span class="long">Sign in with Google</span><span class="short">Sign in</span></button>' +
    '<button type="button" class="btn" id="drive-sync" title="Sync every tracker with Google Drive" hidden>Sync now</button>' +
    '<details class="menu" id="drive-menu" hidden><summary class="avatar" aria-label="Google account menu"><span id="drive-initial">G</span></summary><div class="pop">' +
    '<p class="pop-h" id="drive-account">Signed in with Google</p>' +
    '<p class="pop-note">One sign-in covers every page. Sync now syncs every tracker to a private app folder in your Google Drive. This site cannot open your other files.</p>' +
    '<button type="button" class="mi" id="drive-sync-menu">Sync now</button>' +
    '<button type="button" class="mi" id="drive-switch">Use another account</button>' +
    '<button type="button" class="mi" id="drive-disconnect">Sign out on this device</button><hr>' +
    '<a class="mi" href="https://myaccount.google.com/connections" target="_blank" rel="noopener">Review access in your Google account</a>' +
    '</div></details>';

  // Every page gets the same account controls from here, so a new page only has to load config.js and progress.js.
  function ensureWidget() {
    if (!document.getElementById("drive-connect")) {
      let bar = document.querySelector(".appbar-in");
      if (!bar) {
        const header = document.createElement("header");
        header.className = "appbar";
        bar = document.createElement("div");
        bar.className = "appbar-in";
        header.append(bar);
        document.body.prepend(header);
      }
      const account = document.createElement("div");
      account.className = "account";
      account.innerHTML = ACCOUNT_HTML;
      bar.append(account);
    }
    if (!document.getElementById("cloud-status")) {
      const wrap = document.createElement("div");
      wrap.className = "cloud-bar";
      wrap.innerHTML = '<p class="cloud" id="cloud-status" role="status" aria-live="polite"></p>';
      document.querySelector(".appbar").after(wrap);
    }
  }

  function configuredClientId() {
    const config = root.STUDY_CONFIG;
    return config && typeof config.googleClientId === "string" ? config.googleClientId : "";
  }

  let hub = null;
  function start(options) {
    if (!hub) hub = createHub(options || {});
    return hub;
  }
  function mount(options) {
    return start().mount(options);
  }

  function createHub({ clientId = configuredClientId(), autoSync = true, syncDelay = 1500 }) {
    ensureWidget();
    const $ = id => document.getElementById(id);
    let token = null, expiresAt = 0, account = read(HINT_KEY) || "";
    let busy = false, timer = null, expiryTimer = null, authClient = null, identity = "idle";
    let current = Promise.resolve(), page = null, deviceId = "";
    const connected = () => !!token && Date.now() < expiresAt;
    const report = (id, text, tone = "") => {
      const el = $(id);
      if (!el) return;
      el.textContent = text;
      if (el.dataset) el.dataset.tone = tone;
    };
    const error = (id, e) => {
      console.error(e);
      report(id, e.message || String(e), "error");
    };
    const idle = () => clientId
      ? "Saved in this browser. Sign in with Google once to sync every tracker across your devices."
      : "Saved in this browser.";
    const markDirty = () => write(DIRTY_KEY, Date.now().toString(36) + "-" + Math.random().toString(36).slice(2));
    const announce = key => {
      try { document.dispatchEvent(new CustomEvent("study:progress", { detail: { tracker: key } })); } catch (e) { /* optional */ }
    };

    try {
      deviceId = localStorage.getItem(DEVICE_KEY) || "";
      if (!/^[A-Za-z0-9-]{8,64}$/.test(deviceId)) {
        deviceId = crypto.randomUUID();
        localStorage.setItem(DEVICE_KEY, deviceId);
      }
    } catch (e) {
      deviceId = "";
    }

    // The access token is shared through this site's storage so every page and tab uses one sign-in.
    // It only allows the drive.appdata scope, expires within an hour and is removed on sign-out.
    function storedSession() {
      try {
        const value = JSON.parse(read(SESSION_KEY) || "null");
        return value && typeof value === "object" ? value : null;
      } catch (e) { return null; }
    }
    function loadSession() {
      const value = storedSession();
      const valid = !!value && typeof value.token === "string" && value.token.length > 0 &&
        value.token.length <= MAX_TOKEN_LENGTH && Number.isSafeInteger(value.expiresAt) && value.expiresAt > Date.now();
      token = valid ? value.token : null;
      expiresAt = valid ? value.expiresAt : 0;
      if (!valid && read(SESSION_KEY) !== null) write(SESSION_KEY, null);
      armExpiry();
      return valid;
    }
    function saveSession() {
      if (connected()) write(SESSION_KEY, JSON.stringify({ token, expiresAt }));
      armExpiry();
    }
    function signOut() {
      clearTimeout(timer);
      timer = null;
      token = null;
      expiresAt = 0;
      write(SESSION_KEY, null);
      armExpiry();
      controls();
    }
    // Drops a rejected token, but keeps a newer one that another tab may already have stored.
    function expire() {
      const stored = storedSession();
      if (!stored || stored.token === token) write(SESSION_KEY, null);
      loadSession();
      controls();
    }
    function armExpiry() {
      clearTimeout(expiryTimer);
      expiryTimer = null;
      if (!connected()) return;
      expiryTimer = setTimeout(() => {
        expiryTimer = null;
        if (loadSession()) return controls();
        controls();
        if (!busy) report("cloud-status", "Your Google sign-in expired. Progress is still saved in this browser. Sign in with Google to sync again.");
      }, Math.min(expiresAt - Date.now() + 100, 2147483647));
    }
    function welcome() {
      const last = Number(read(SYNCED_KEY)) || 0;
      report("cloud-status", (account ? "Signed in as " + account + ". " : "Signed in with Google. ") +
        (last ? "Last synced " + when(last) + "." : "Sync now syncs every tracker."), "ok");
    }

    function controls() {
      const on = connected();
      $("drive-connect").hidden = on;
      $("drive-connect").disabled = busy;
      $("drive-sync").hidden = !on;
      $("drive-sync").disabled = busy || !on;
      $("drive-sync-menu").disabled = busy || !on;
      $("drive-menu").hidden = !on;
      $("drive-disconnect").disabled = busy || !token;
      $("drive-account").textContent = account ? "Signed in as " + account : "Signed in with Google";
      $("drive-initial").textContent = (account[0] || "G").toUpperCase();
    }
    function schedule() {
      clearTimeout(timer);
      timer = setTimeout(() => { timer = null; sync(); }, syncDelay);
    }
    function changed() {
      markDirty();
      if (connected() && autoSync) {
        report("cloud-status", "Saved in this browser. Syncing shortly...", "busy");
        schedule();
      } else if (token) {
        report("cloud-status", "Saved in this browser. Sign in with Google again to sync.");
      } else {
        report("cloud-status", idle());
      }
    }

    function mountTracker({ storageKey, ids, onChange }) {
      if (page) throw new Error("A page can only show one tracker.");
      if (typeof storageKey !== "string" || !TRACKER_KEY.test(storageKey)) throw new Error("Invalid tracker name.");
      const localKey = storageKey + SUFFIX;
      const knownIds = new Set(ids);
      let entries = Object.create(null), readBlocked = false, storageHealthy = true;
      const envelope = () => ({ version: 1, tracker: storageKey, entries });

      function persist() {
        if (readBlocked) {
          storageHealthy = false;
          report("local-status", "Existing local progress could not be read and was not overwritten. Export your visible progress before leaving.", "error");
          return;
        }
        try {
          localStorage.setItem(localKey, JSON.stringify(envelope()));
          storageHealthy = true;
          report("local-status", "Saved locally in this browser.");
        } catch (e) {
          storageHealthy = false;
          error("local-status", new Error("Local saving failed. Export a backup before leaving. " + e.message));
        }
      }
      function refresh() { onChange(entries); }
      function readLatest() {
        const raw = localStorage.getItem(localKey);
        if (raw) entries = merge(entries, validate(JSON.parse(raw), storageKey));
      }
      try {
        const raw = localStorage.getItem(localKey);
        const old = localStorage.getItem(storageKey);
        if (raw) entries = validate(JSON.parse(raw), storageKey);
        else if (old) entries = legacy(JSON.parse(old));
        persist();
      } catch (e) {
        readBlocked = true;
        storageHealthy = false;
        error("local-status", new Error("Could not load local progress; existing storage was not overwritten. Export any visible progress. " + e.message));
      }
      refresh();

      function set(id, status) {
        if (!knownIds.has(id) || !Number.isInteger(status) || status < 0 || status > 3) {
          throw new Error("Invalid tracker update.");
        }
        try { readLatest(); } catch (e) { readBlocked = true; error("local-status", e); }
        const latest = Math.max(0, ...Object.values(entries).map(e => e.updatedAt));
        entries[id] = { status, updatedAt: Math.max(Date.now(), latest + 1) };
        persist();
        refresh();
        changed();
      }

      page = {
        key: storageKey,
        localKey,
        entries: () => entries,
        absorb(incoming, skipped) {
          if (!readBlocked) {
            try { readLatest(); } catch (e) { readBlocked = true; error("local-status", e); }
          }
          entries = merge(entries, incoming);
          persist();
          refresh();
          if (readBlocked) skipped.push(storageKey);
          else if (!storageHealthy) throw new Error("Drive sync stopped because local saving failed. Export a backup first.");
          return entries;
        },
        fromStorage(value) {
          try {
            entries = merge(entries, validate(JSON.parse(value), storageKey));
            refresh();
          } catch (e) { error("local-status", e); }
        }
      };
      return { set, idle: () => current };
    }

    // Merges incoming entries into one tracker's saved progress, whether or not that tracker is open.
    function saveLocal(key, incoming, skipped) {
      if (page && page.key === key) return page.absorb(incoming, skipped);
      const name = key + SUFFIX;
      let stored = Object.create(null);
      const raw = localStorage.getItem(name);
      if (raw !== null) {
        try { stored = validate(JSON.parse(raw), key); }
        catch (e) { skipped.push(key); return incoming; }
      }
      const merged = merge(stored, incoming);
      if (!same(merged, stored)) {
        try { localStorage.setItem(name, JSON.stringify({ version: 1, tracker: key, entries: merged })); }
        catch (e) { throw new Error("Drive sync stopped because local saving failed. Export a backup first. " + e.message); }
        announce(key);
      }
      return merged;
    }
    function snapshot() {
      const all = Object.create(null);
      for (const key of localTrackers()) {
        try { all[key] = validate(JSON.parse(read(key + SUFFIX)), key); } catch (e) { /* unreadable; left out */ }
      }
      if (page) all[page.key] = merge(all[page.key] || Object.create(null), page.entries());
      for (const key of Object.keys(all)) if (!Object.keys(all[key]).length) delete all[key];
      return all;
    }

    $("export-progress").onclick = () => {
      const all = snapshot();
      const url = URL.createObjectURL(new Blob([JSON.stringify({ version: 2, trackers: all }, null, 2)], { type: "application/json" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = "study-progress-" + new Date().toISOString().slice(0, 10) + ".json";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      report("local-status", "Exported " + plural(Object.keys(all).length) + " to one backup file.");
    };
    $("import-progress").onclick = () => $("progress-file").click();
    $("progress-file").onchange = async event => {
      const file = event.target.files[0];
      if (!file) return;
      try {
        if (file.size > MAX_BACKUP_BYTES) throw new Error("Backup exceeds the 5 MB limit.");
        const imported = validateAll(JSON.parse(await file.text()));
        const keys = Object.keys(imported);
        const items = keys.reduce((n, key) => n + Object.keys(imported[key]).length, 0);
        if (!root.confirm("Merge this backup (" + plural(keys.length) + ", " + items + " items) into your progress? Newer item changes win. Export your current progress first if needed.")) return;
        const skipped = [];
        for (const key of keys) saveLocal(key, imported[key], skipped);
        markDirty();
        if (skipped.length) throw new Error("Backup merged, except " + skipped.join(", ") + ": local progress there could not be read and was left unchanged.");
        report("cloud-status", connected() ? "Backup merged. Syncing to Google Drive..." : "Backup merged in this browser.", "ok");
        if (connected()) sync();
      } catch (e) { error("cloud-status", e); }
      finally { event.target.value = ""; }
    };

    async function request(url, options = {}) {
      if (!connected() && !loadSession()) {
        controls();
        throw new Error("Your Google session expired. Sign in with Google again to sync.");
      }
      const response = await fetch(url, {
        ...options, signal: AbortSignal.timeout(30000), credentials: "omit", referrerPolicy: "no-referrer",
        headers: { ...options.headers, Authorization: "Bearer " + token }
      });
      if (response.status === 401) {
        expire();
        throw new Error("Your Google session expired. Sign in with Google again to sync.");
      }
      if (!response.ok) throw new Error("Google Drive request failed (HTTP " + response.status + "). Progress is still saved in this browser; try Sync now again.");
      return response.status === 204 ? null : response.json();
    }
    async function listFiles() {
      const files = [];
      let pageToken = "";
      do {
        const query = new URLSearchParams({
          spaces: "appDataFolder", q: "trashed = false",
          fields: "nextPageToken,files(id,name,appProperties)", pageSize: "1000"
        });
        if (pageToken) query.set("pageToken", pageToken);
        const result = await request(API + "?" + query);
        if (Array.isArray(result.files)) files.push(...result.files);
        pageToken = typeof result.nextPageToken === "string" ? result.nextPageToken : "";
      } while (pageToken);
      return files.filter(file => file && typeof file.id === "string" && file.id);
    }
    const download = file => request(API + "/" + encodeURIComponent(file.id) + "?alt=media");
    function upload(own, name, all) {
      const body = JSON.stringify({ version: 2, trackers: all });
      if (own) {
        return request(UPLOAD + "/" + encodeURIComponent(own.id) + "?uploadType=media",
          { method: "PATCH", headers: { "Content-Type": "application/json" }, body });
      }
      const boundary = "study_" + crypto.randomUUID();
      const metadata = { name, parents: ["appDataFolder"], appProperties: { [BUNDLE_PROPERTY]: BUNDLE_VERSION } };
      return request(UPLOAD + "?uploadType=multipart", {
        method: "POST", headers: { "Content-Type": "multipart/related; boundary=" + boundary },
        body: "--" + boundary + "\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + JSON.stringify(metadata) +
          "\r\n--" + boundary + "\r\nContent-Type: application/json\r\n\r\n" + body + "\r\n--" + boundary + "--"
      });
    }

    async function syncAll() {
      const dirtyAtStart = read(DIRTY_KEY);
      const ownName = "study-progress-" + deviceId + ".json";
      const remote = Object.create(null);
      const ownLegacy = [];
      let own = null, ownTrackers = null;
      for (const file of await listFiles()) {
        const props = file.appProperties || {};
        const tracker = props[TRACKER_PROPERTY];
        let found;
        if (props[BUNDLE_PROPERTY] === BUNDLE_VERSION) {
          found = validateAll(await download(file));
          if (!own && file.name === ownName) { own = file; ownTrackers = found; }
        } else if (typeof tracker === "string" && TRACKER_KEY.test(tracker)) {
          found = Object.create(null);
          found[tracker] = validate(await download(file), tracker);
          if (file.name === tracker + "-" + deviceId + ".json") ownLegacy.push(file);
        } else {
          continue;
        }
        for (const key of Object.keys(found)) remote[key] = merge(remote[key] || Object.create(null), found[key]);
      }
      // Each browser writes only its own file, so devices syncing at the same time cannot overwrite each other.
      const keys = new Set([...localTrackers(), ...Object.keys(remote)]);
      if (page) keys.add(page.key);
      const all = Object.create(null), skipped = [];
      for (const key of [...keys].sort()) {
        const entries = saveLocal(key, remote[key] || Object.create(null), skipped);
        if (Object.keys(entries).length) all[key] = entries;
      }
      if (!(ownTrackers && sameAll(ownTrackers, all)) && (own || Object.keys(all).length)) await upload(own, ownName, all);
      for (const file of ownLegacy) {
        try { await request(API + "/" + encodeURIComponent(file.id), { method: "DELETE" }); }
        catch (e) { /* its data is already in this browser's file; retried on the next sync */ }
      }
      const dirtyNow = read(DIRTY_KEY);
      if (dirtyNow === dirtyAtStart) write(DIRTY_KEY, null);
      write(SYNCED_KEY, String(Date.now()));
      return { count: Object.keys(all).length, skipped, newer: dirtyNow !== null && dirtyNow !== dirtyAtStart };
    }
    function sync() {
      clearTimeout(timer);
      timer = null;
      if (busy) return current;
      busy = true;
      controls();
      report("cloud-status", "Syncing every tracker with Google Drive...", "busy");
      current = (async () => {
        let result = null;
        try {
          if (!navigator.locks) throw new Error("Drive sync needs a current browser with Web Locks support. Use export and import instead.");
          if (!deviceId) throw new Error("Drive sync needs working browser storage. Export a backup instead.");
          result = await navigator.locks.request(LOCK, syncAll);
        } catch (e) { error("cloud-status", e); }
        finally { busy = false; controls(); }
        if (!result) return;
        const time = when(Date.now());
        const done = result.count ? "Synced " + plural(result.count) + " with Google Drive " + time : "Synced with Google Drive " + time + ". There is no progress yet";
        if (result.skipped.length) {
          report("cloud-status", done + ", but local progress for " + result.skipped.join(", ") + " could not be read in this browser and was left unchanged. Export a backup.", "error");
        } else if (result.newer) {
          report("cloud-status", "Earlier changes synced " + time + ". Newer changes will sync next.", "busy");
        } else {
          report("cloud-status", done + ".", "ok");
        }
        if (result.newer && connected() && autoSync) schedule();
      })();
      return current;
    }

    async function identify() {
      try {
        const about = await request(ABOUT);
        const email = about && about.user && typeof about.user.emailAddress === "string" ? about.user.emailAddress : "";
        account = email.slice(0, 254);
        if (account) write(HINT_KEY, account);
      } catch (e) {
        account = "";
      }
      controls();
    }
    function loadIdentity() {
      if (root.google?.accounts?.oauth2) return Promise.resolve();
      return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        const timeout = setTimeout(() => {
          script.remove();
          reject(new Error("Google sign-in did not load. Check your connection and reload the page."));
        }, 15000);
        script.onload = () => { clearTimeout(timeout); resolve(); };
        script.onerror = () => { clearTimeout(timeout); script.remove(); reject(new Error("Could not load Google sign-in. Check your connection or content blocker.")); };
        document.head.append(script);
      });
    }
    function onToken(response) {
      const life = Math.min(Math.max(Number(response.expires_in) || 0, 0), 86400);
      if (response.error || typeof response.access_token !== "string" || !response.access_token ||
          response.access_token.length > MAX_TOKEN_LENGTH) {
        error("cloud-status", new Error("Google sign-in was not completed: " + (response.error_description || response.error || "no access token") + "."));
      } else if (!google.accounts.oauth2.hasGrantedAllScopes(response, SCOPE)) {
        error("cloud-status", new Error("Google Drive app-folder permission was not granted. Sign in again and allow it to sync."));
      } else {
        token = response.access_token;
        expiresAt = Date.now() + life * 1000 - 30000;
        saveSession();
        current = identify().then(sync);
      }
      controls();
    }
    function prepare() {
      if (!clientId || authClient || identity === "loading" || location.protocol === "file:") return;
      identity = "loading";
      loadIdentity().then(() => {
        authClient = google.accounts.oauth2.initTokenClient({
          client_id: clientId, scope: SCOPE, callback: onToken,
          error_callback: response => {
            const closed = response && response.type === "popup_closed";
            report("cloud-status", closed ? "Google sign-in was closed before finishing." : "Google sign-in failed (" + (response && response.type) + "). Allow pop-ups for this site and try again.", closed ? "" : "error");
            controls();
          }
        });
        identity = "ready";
      }).catch(e => {
        identity = "failed";
        error("cloud-status", e);
      });
    }
    function signIn(chooseAccount) {
      if (!clientId) {
        report("cloud-status", "Google sign-in is not configured for this site. See Setup and security.", "error");
        return;
      }
      if (location.protocol === "file:") {
        report("cloud-status", "Google sign-in needs the published HTTPS site or a localhost server, not a file opened from disk.", "error");
        return;
      }
      if (!authClient) {
        if (identity !== "loading") prepare();
        report("cloud-status", "Google sign-in is still loading. Try again in a moment.", "busy");
        return;
      }
      const login = chooseAccount ? "" : read(HINT_KEY) || "";
      // The button stays enabled: browsers can hide pop-up closure from Google's library, so a second click must always work.
      report("cloud-status", "Waiting for Google sign-in in the pop-up window...", "busy");
      // Must run inside the click handler, or the browser blocks the sign-in pop-up.
      try { authClient.requestAccessToken(login ? { prompt: "", login_hint: login } : { prompt: "select_account" }); }
      catch (e) { error("cloud-status", e); controls(); }
    }

    $("drive-connect").onclick = () => signIn(false);
    $("drive-switch").onclick = () => {
      signOut();
      account = "";
      write(HINT_KEY, null);
      controls();
      signIn(true);
    };
    $("drive-sync").onclick = () => sync();
    $("drive-sync-menu").onclick = () => sync();
    $("drive-disconnect").onclick = () => {
      signOut();
      report("cloud-status", "Signed out on every page in this browser. Progress is still saved here and in your Google Drive.");
    };
    // Sign-in, sign-out and syncs in one tab show up in every other open tab of the site.
    root.addEventListener("storage", event => {
      if (page && event.key === page.localKey && event.newValue) page.fromStorage(event.newValue);
      if (event.key !== null && event.key !== SESSION_KEY && event.key !== HINT_KEY && event.key !== SYNCED_KEY) return;
      const was = connected();
      loadSession();
      account = read(HINT_KEY) || "";
      if (!connected()) {
        clearTimeout(timer);
        timer = null;
      }
      controls();
      if (busy || timer) return;
      if (connected()) welcome();
      else if (was) report("cloud-status", "Signed out on every page in this browser. Progress is still saved here and in your Google Drive.");
    });

    report("local-status", "Progress for every tracker is saved in this browser.");
    report("cloud-status", idle());
    loadSession();
    controls();
    if (connected()) {
      welcome();
      // Picks up edits that were saved but not yet synced when the previous page closed.
      if (autoSync && read(DIRTY_KEY) !== null) {
        report("cloud-status", "Syncing your latest changes shortly...", "busy");
        schedule();
      }
    }
    prepare();
    return { mount: mountTracker, sync, idle: () => current };
  }

  root.StudyProgress = { validate, validateAll, merge, legacy, start, mount };
  // Pages that load config.js get the shared account controls without any page-specific code.
  if (typeof document !== "undefined" && typeof document.addEventListener === "function" && root.STUDY_CONFIG) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => start());
    else start();
  }
})(typeof window === "undefined" ? globalThis : window);
