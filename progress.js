(function (root) {
  "use strict";
  const SCOPE = "https://www.googleapis.com/auth/drive.appdata";
  const API = "https://www.googleapis.com/drive/v3/files";
  const UPLOAD = "https://www.googleapis.com/upload/drive/v3/files";
  const ABOUT = "https://www.googleapis.com/drive/v3/about?fields=user(emailAddress)";
  const HINT_KEY = "study-drive-account";
  const MAX_ENTRIES = 20000;
  const MAX_ID_LENGTH = 120;

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

  function mount({ storageKey, ids, clientId, onChange, autoSync = true, syncDelay = 1500 }) {
    const $ = id => document.getElementById(id);
    const localKey = storageKey + ":v1";
    const knownIds = new Set(ids);
    let entries = Object.create(null);
    let token = null, expiresAt = 0, busy = false, authClient = null, identity = "idle";
    let deviceId, storageHealthy = true, readBlocked = false, account = "", timer = null;
    let current = Promise.resolve();
    const envelope = () => ({ version: 1, tracker: storageKey, entries });
    const connected = () => !!token && Date.now() < expiresAt;
    const report = (id, text, tone = "") => {
      const el = $(id);
      el.textContent = text;
      if (el.dataset) el.dataset.tone = tone;
    };
    const error = (id, e) => {
      console.error(e);
      report(id, e.message || String(e), "error");
    };
    const remember = value => { try { if (value) localStorage.setItem(HINT_KEY, value); else localStorage.removeItem(HINT_KEY); } catch (e) { /* hint is optional */ } };
    const hint = () => { try { return localStorage.getItem(HINT_KEY) || ""; } catch (e) { return ""; } };
    const idle = () => clientId
      ? "Saved in this browser. Sign in with Google to sync across devices."
      : "Saved in this browser.";

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
      deviceId = localStorage.getItem("study-drive-device");
      if (!deviceId) {
        deviceId = crypto.randomUUID();
        localStorage.setItem("study-drive-device", deviceId);
      }
      persist();
    } catch (e) {
      readBlocked = true;
      storageHealthy = false;
      error("local-status", new Error("Could not load local progress; existing storage was not overwritten. Export any visible progress. " + e.message));
    }
    refresh();
    report("cloud-status", idle());

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

    function set(id, status) {
      if (!knownIds.has(id) || !Number.isInteger(status) || status < 0 || status > 3) {
        throw new Error("Invalid tracker update.");
      }
      try { readLatest(); } catch (e) { readBlocked = true; error("local-status", e); }
      const latest = Math.max(0, ...Object.values(entries).map(e => e.updatedAt));
      entries[id] = { status, updatedAt: Math.max(Date.now(), latest + 1) };
      persist();
      refresh();
      if (connected() && autoSync) {
        report("cloud-status", "Saved in this browser. Syncing shortly...", "busy");
        clearTimeout(timer);
        timer = setTimeout(() => { timer = null; current = sync(); }, syncDelay);
      } else if (token) {
        report("cloud-status", "Saved in this browser. Sign in with Google again to sync.");
      } else {
        report("cloud-status", idle());
      }
    }

    $("export-progress").onclick = () => {
      const url = URL.createObjectURL(new Blob([JSON.stringify(envelope(), null, 2)], { type: "application/json" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = storageKey + "-progress.json";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    };
    $("import-progress").onclick = () => $("progress-file").click();
    $("progress-file").onchange = async event => {
      const file = event.target.files[0];
      if (!file) return;
      try {
        if (file.size > 5 * 1024 * 1024) throw new Error("Backup exceeds the 5 MB limit.");
        const imported = validate(JSON.parse(await file.text()), storageKey);
        if (!window.confirm("Merge this backup into your progress? Newer item changes win. Export your current progress first if needed.")) return;
        readLatest();
        entries = merge(entries, imported);
        persist();
        refresh();
        report("cloud-status", connected() ? "Backup merged. Syncing to Google Drive..." : "Backup merged in this browser.", "ok");
        if (connected()) current = sync();
      } catch (e) { error("cloud-status", e); }
      finally { event.target.value = ""; }
    };
    window.addEventListener("storage", event => {
      if (event.key !== localKey || !event.newValue) return;
      try {
        entries = merge(entries, validate(JSON.parse(event.newValue), storageKey));
        refresh();
      } catch (e) { error("local-status", e); }
    });

    async function request(url, options = {}) {
      if (!connected()) {
        token = null;
        controls();
        throw new Error("Your Google session expired. Sign in with Google again to sync.");
      }
      const response = await fetch(url, {
        ...options, signal: AbortSignal.timeout(30000), credentials: "omit", referrerPolicy: "no-referrer",
        headers: { ...options.headers, Authorization: "Bearer " + token }
      });
      if (response.status === 401) {
        token = null;
        controls();
        throw new Error("Your Google session expired. Sign in with Google again to sync.");
      }
      if (!response.ok) throw new Error("Google Drive request failed (HTTP " + response.status + "). Progress is still saved in this browser; try Sync now again.");
      return response.json();
    }
    async function syncFiles() {
      readLatest();
      const files = [];
      let pageToken = "";
      do {
        const query = new URLSearchParams({
          spaces: "appDataFolder",
          q: "trashed = false and appProperties has { key='studyTracker' and value='" + storageKey + "' }",
          fields: "nextPageToken,files(id,name)", pageSize: "100"
        });
        if (pageToken) query.set("pageToken", pageToken);
        const page = await request(API + "?" + query);
        files.push(...page.files);
        pageToken = page.nextPageToken || "";
      } while (pageToken);
      let combined = entries;
      for (const file of files) {
        const value = await request(API + "/" + encodeURIComponent(file.id) + "?alt=media");
        combined = merge(combined, validate(value, storageKey));
      }
      // Each browser writes only its own snapshot, so concurrent devices cannot overwrite each other.
      readLatest();
      entries = merge(entries, combined);
      persist();
      refresh();
      if (!storageHealthy) throw new Error("Drive sync stopped because local saving failed. Export a backup first.");
      const name = storageKey + "-" + deviceId + ".json";
      const own = files.find(file => file.name === name);
      let url, options;
      if (own) {
        url = UPLOAD + "/" + encodeURIComponent(own.id) + "?uploadType=media";
        options = { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(envelope()) };
      } else {
        url = UPLOAD + "?uploadType=multipart";
        const boundary = "study_" + crypto.randomUUID();
        const metadata = { name, parents: ["appDataFolder"], appProperties: { studyTracker: storageKey } };
        const body = "--" + boundary + "\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" +
          JSON.stringify(metadata) + "\r\n--" + boundary + "\r\nContent-Type: application/json\r\n\r\n" +
          JSON.stringify(envelope()) + "\r\n--" + boundary + "--";
        options = { method: "POST", headers: { "Content-Type": "multipart/related; boundary=" + boundary }, body };
      }
      const sent = JSON.stringify(envelope());
      await request(url, options);
      const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      if (JSON.stringify(envelope()) === sent) {
        report("cloud-status", "Synced with Google Drive at " + time + ".", "ok");
      } else {
        report("cloud-status", "Earlier changes synced at " + time + ". Newer changes will sync next.", "busy");
      }
    }
    async function sync() {
      if (busy) return;
      clearTimeout(timer);
      timer = null;
      busy = true;
      controls();
      report("cloud-status", "Syncing with Google Drive...", "busy");
      try {
        if (!navigator.locks) throw new Error("Drive sync needs a current browser with Web Locks support. Use export and import instead.");
        if (!deviceId) throw new Error("Drive sync needs working browser storage. Export a backup instead.");
        await navigator.locks.request("study-drive:" + storageKey, syncFiles);
      } catch (e) { error("cloud-status", e); }
      finally { busy = false; controls(); }
    }
    async function identify() {
      try {
        const about = await request(ABOUT);
        const email = about && about.user && typeof about.user.emailAddress === "string" ? about.user.emailAddress : "";
        account = email.slice(0, 254);
        remember(account);
      } catch (e) {
        account = "";
      }
      controls();
    }

    function loadIdentity() {
      if (window.google?.accounts?.oauth2) return Promise.resolve();
      return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        const timer = setTimeout(() => {
          script.remove();
          reject(new Error("Google sign-in did not load. Check your connection and reload the page."));
        }, 15000);
        script.onload = () => { clearTimeout(timer); resolve(); };
        script.onerror = () => { clearTimeout(timer); script.remove(); reject(new Error("Could not load Google sign-in. Check your connection or content blocker.")); };
        document.head.append(script);
      });
    }
    function onToken(response) {
      if (response.error || !response.access_token) {
        error("cloud-status", new Error("Google sign-in was not completed: " + (response.error_description || response.error || "no access token") + "."));
      } else if (!google.accounts.oauth2.hasGrantedAllScopes(response, SCOPE)) {
        error("cloud-status", new Error("Google Drive app-folder permission was not granted. Sign in again and allow it to sync."));
      } else {
        token = response.access_token;
        expiresAt = Date.now() + Number(response.expires_in) * 1000 - 30000;
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
      const login = chooseAccount ? "" : hint();
      // The button stays enabled: browsers can hide pop-up closure from Google's library, so a second click must always work.
      report("cloud-status", "Waiting for Google sign-in in the pop-up window...", "busy");
      // Must run inside the click handler, or the browser blocks the sign-in pop-up.
      try { authClient.requestAccessToken(login ? { prompt: "", login_hint: login } : { prompt: "select_account" }); }
      catch (e) { error("cloud-status", e); controls(); }
    }

    $("drive-connect").onclick = () => signIn(false);
    $("drive-switch").onclick = () => { token = null; expiresAt = 0; account = ""; remember(""); controls(); signIn(true); };
    $("drive-sync").onclick = () => (current = sync());
    $("drive-sync-menu").onclick = () => (current = sync());
    $("drive-disconnect").onclick = () => {
      clearTimeout(timer);
      timer = null;
      token = null;
      expiresAt = 0;
      controls();
      report("cloud-status", "Signed out on this device. Progress is still saved in this browser and in your Google Drive.");
    };
    window.addEventListener("beforeunload", event => {
      if (!busy && !timer) return;
      event.preventDefault();
      event.returnValue = "";
    });
    controls();
    prepare();
    return { set, idle: () => current };
  }
  root.StudyProgress = { validate, merge, legacy, mount };
})(typeof window === "undefined" ? globalThis : window);
