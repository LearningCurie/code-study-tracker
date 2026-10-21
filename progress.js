(function (root) {
  "use strict";
  const SCOPE = "https://www.googleapis.com/auth/drive.appdata";
  const API = "https://www.googleapis.com/drive/v3/files";

  function validate(value, tracker) {
    if (!value || value.version !== 1 || value.tracker !== tracker ||
        !value.entries || typeof value.entries !== "object" || Array.isArray(value.entries)) {
      throw new Error("Invalid progress file or wrong tracker.");
    }
    const entries = Object.create(null);
    for (const [id, entry] of Object.entries(value.entries)) {
      if (!entry || !Number.isInteger(entry.status) || entry.status < 0 || entry.status > 3 ||
          !Number.isSafeInteger(entry.updatedAt) || entry.updatedAt < 0) {
        throw new Error("Invalid progress entry: " + id);
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

  function mount({ storageKey, ids, clientId, onChange }) {
    const $ = id => document.getElementById(id);
    const localKey = storageKey + ":v1";
    const knownIds = new Set(ids);
    let entries = Object.create(null);
    let token = null, expiresAt = 0, busy = false, authClient = null;
    let deviceId, storageHealthy = true, readBlocked = false;
    const envelope = () => ({ version: 1, tracker: storageKey, entries });
    const report = (id, text) => { $(id).textContent = text; };
    const error = (id, e) => {
      console.error(e);
      report(id, e.message || String(e));
    };
    function persist() {
      if (readBlocked) {
        storageHealthy = false;
        report("local-status", "Existing local progress could not be read and was not overwritten. Export your visible progress before leaving.");
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

    function set(id, status) {
      if (!knownIds.has(id) || !Number.isInteger(status) || status < 0 || status > 3) {
        throw new Error("Invalid tracker update.");
      }
      try { readLatest(); } catch (e) { readBlocked = true; error("local-status", e); }
      const latest = Math.max(0, ...Object.values(entries).map(e => e.updatedAt));
      entries[id] = { status, updatedAt: Math.max(Date.now(), latest + 1) };
      persist();
      refresh();
      report("cloud-status", "Changes are local. Click Sync now to update Google Drive.");
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
        report("cloud-status", "Backup merged locally. Sync now to upload it to Drive.");
      } catch (e) { error("cloud-status", e); }
      finally { event.target.value = ""; }
    };
    window.addEventListener("storage", event => {
      if (event.key !== localKey || !event.newValue) return;
      try {
        entries = merge(entries, validate(JSON.parse(event.newValue), storageKey));
        refresh();
        report("cloud-status", "Progress updated from another tab. Sync now to update Drive.");
      } catch (e) { error("local-status", e); }
    });

    function controls() {
      $("drive-connect").disabled = busy;
      $("drive-sync").disabled = busy || !token;
      $("drive-disconnect").disabled = busy || !token;
    }
    async function request(url, options = {}) {
      if (!token || Date.now() >= expiresAt) {
        token = null;
        controls();
        throw new Error("Google access expired. Connect Google Drive again, then sync.");
      }
      const response = await fetch(url, {
        ...options, signal: AbortSignal.timeout(30000),
        headers: { ...options.headers, Authorization: "Bearer " + token }
      });
      if (response.status === 401) {
        token = null;
        controls();
        throw new Error("Google access expired. Connect Google Drive again.");
      }
      if (!response.ok) throw new Error("Google Drive request failed (HTTP " + response.status + "). Progress remains local; retry sync.");
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
        url = "https://www.googleapis.com/upload/drive/v3/files/" + encodeURIComponent(own.id) + "?uploadType=media";
        options = { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(envelope()) };
      } else {
        url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart";
        const boundary = "study_" + crypto.randomUUID();
        const metadata = { name, parents: ["appDataFolder"], appProperties: { studyTracker: storageKey } };
        const body = "--" + boundary + "\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" +
          JSON.stringify(metadata) + "\r\n--" + boundary + "\r\nContent-Type: application/json\r\n\r\n" +
          JSON.stringify(envelope()) + "\r\n--" + boundary + "--";
        options = { method: "POST", headers: { "Content-Type": "multipart/related; boundary=" + boundary }, body };
      }
      const sent = JSON.stringify(envelope());
      await request(url, options);
      report("cloud-status", JSON.stringify(envelope()) === sent
        ? "Synced with Google Drive. Sync on your other device to pick up these changes."
        : "Earlier changes synced. New local changes need another sync.");
    }
    async function sync() {
      if (busy) return;
      busy = true;
      controls();
      report("cloud-status", "Syncing with Google Drive...");
      try {
        if (!navigator.locks) throw new Error("Drive sync needs a browser with Web Locks support. Use a current Chrome, Edge, Firefox or Safari, or use export/import.");
        if (!deviceId) throw new Error("Drive sync needs working browser storage. Export a backup instead.");
        await navigator.locks.request("study-drive:" + storageKey, syncFiles);
      } catch (e) { error("cloud-status", e); }
      finally { busy = false; controls(); }
    }

    function loadIdentity() {
      if (window.google?.accounts?.oauth2) return Promise.resolve();
      return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://accounts.google.com/gsi/client";
        const timer = setTimeout(() => {
          script.remove();
          reject(new Error("Google sign-in timed out. Check your connection and try again."));
        }, 15000);
        script.onload = () => { clearTimeout(timer); resolve(); };
        script.onerror = () => { clearTimeout(timer); script.remove(); reject(new Error("Could not load Google sign-in. Check your connection or content blocker.")); };
        document.head.append(script);
      });
    }
    $("drive-connect").onclick = async () => {
      if (!clientId) {
        report("cloud-status", "Google Drive is not configured. Follow Hosting and Google Drive setup to add your OAuth client ID.");
        return;
      }
      if (location.protocol === "file:") {
        report("cloud-status", "Google Drive needs an HTTP localhost server or your HTTPS GitHub Pages site, not a file URL.");
        return;
      }
      if (!authClient) {
        busy = true;
        token = null;
        expiresAt = 0;
        controls();
        try {
          await loadIdentity();
          authClient = google.accounts.oauth2.initTokenClient({
            client_id: clientId, scope: SCOPE,
            callback: response => {
              busy = false;
              if (response.error || !response.access_token) {
                error("cloud-status", new Error(response.error_description || response.error || "Google did not return an access token."));
              } else if (!google.accounts.oauth2.hasGrantedAllScopes(response, SCOPE)) {
                error("cloud-status", new Error("Drive app-data permission was not granted. Connect again and allow it."));
              } else {
                token = response.access_token;
                expiresAt = Date.now() + Number(response.expires_in) * 1000 - 30000;
                report("cloud-status", "Connected. Click Sync now. This browser's progress will merge with the selected Google account.");
              }
              controls();
            },
            error_callback: response => {
              busy = false;
              error("cloud-status", new Error("Google sign-in failed: " + response.type + ". Retry Connect Google Drive."));
              controls();
            }
          });
          report("cloud-status", "Google sign-in is ready. Click Connect Google Drive again to open sign-in.");
        } catch (e) { error("cloud-status", e); }
        finally { busy = false; controls(); }
        return;
      }
      busy = true;
      controls();
      try { authClient.requestAccessToken({ prompt: "select_account" }); }
      catch (e) { busy = false; error("cloud-status", e); controls(); }
    };
    $("drive-sync").onclick = sync;
    $("drive-disconnect").onclick = () => {
      token = null;
      expiresAt = 0;
      controls();
      report("cloud-status", "Disconnected locally. Local progress is unchanged. To revoke permission, remove this app in your Google account settings.");
    };
    window.addEventListener("beforeunload", event => {
      if (!busy) return;
      event.preventDefault();
      event.returnValue = "";
    });
    return { set };
  }
  root.StudyProgress = { validate, merge, legacy, mount };
})(typeof window === "undefined" ? globalThis : window);
