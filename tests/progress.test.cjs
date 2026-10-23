const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { webcrypto } = require("node:crypto");
const root = path.dirname(require.resolve("../progress.js"));
const source = fs.readFileSync(path.join(root, "progress.js"), "utf8");
const tick = (ms = 0) => new Promise(resolve => setTimeout(resolve, ms));
const ABOUT = "/drive/v3/about";
const SESSION = "study-drive-session";
const DEVICE = "study-drive-device";
const locks = new WeakMap();

// One harness is one page. Pages created with the same `storage` Map behave like pages of one browser.
function harness({ storage = new Map(), initial = {}, fetch, denied = false, clientId = "test-client", onToken,
  protocol = "https:", autoSync = false, syncDelay = 5, storageKey = "py-status", ids = ["one", "two"], tracker = true } = {}) {
  for (const [key, value] of Object.entries(initial)) storage.set(key, value);
  if (!locks.has(storage)) locks.set(storage, Promise.resolve());
  const elements = new Map();
  const listeners = {};
  const requests = [];
  const exported = [];
  let visible;
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, { textContent: "", disabled: false, hidden: false, dataset: {}, click() {} });
      return elements.get(id);
    },
    createElement: () => ({ click() {} })
  };
  const context = {
    document, console: { error() {} }, crypto: webcrypto, AbortSignal, URLSearchParams, Blob, clearTimeout,
    // Session-expiry timers last up to an hour and must not keep the test process alive.
    setTimeout(callback, ms) { const timer = setTimeout(callback, ms); if (ms >= 1000) timer.unref(); return timer; },
    URL: { createObjectURL: blob => { exported.push(blob); return "blob:test"; }, revokeObjectURL() {} },
    location: { protocol },
    navigator: { locks: { request(_name, callback) {
      const run = locks.get(storage).then(() => callback());
      locks.set(storage, run.catch(() => {}));
      return run;
    } } },
    localStorage: {
      get length() { return storage.size; },
      key: index => [...storage.keys()][index] ?? null,
      getItem: key => storage.get(key) ?? null,
      setItem(key, value) { if (denied) throw new Error("Storage denied"); storage.set(key, String(value)); },
      removeItem(key) { storage.delete(key); }
    },
    confirm: () => true,
    addEventListener(name, callback) { (listeners[name] ||= []).push(callback); },
    fetch: fetch || (() => { throw new Error("Unexpected fetch"); }),
    google: { accounts: { oauth2: {
      hasGrantedAllScopes: () => true,
      initTokenClient(options) {
        return { requestAccessToken(request) {
          requests.push(request);
          if (onToken) onToken(options);
          else options.callback({ access_token: "test-token", expires_in: 3600 });
        } };
      }
    } } }
  };
  context.window = context;
  vm.runInNewContext(source, context);
  const api = context.StudyProgress;
  const hub = api.start({ clientId, autoSync, syncDelay });
  const page = tracker
    ? api.mount({ storageKey, ids, onChange: entries => { visible = JSON.parse(JSON.stringify(entries)); } })
    : null;
  const el = id => document.getElementById(id);
  return {
    api, hub, tracker: page, storage, requests, exported, el,
    get visible() { return visible; },
    fire(name, event) { (listeners[name] || []).forEach(callback => callback(event)); },
    async connect() {
      await tick();
      el("drive-connect").onclick();
      await hub.idle();
    },
    async sync() {
      el("drive-sync").onclick();
      await hub.idle();
    }
  };
}
const data = (entries, tracker = "py-status") => ({ version: 1, tracker, entries });
const json = (entries, tracker) => JSON.stringify(data(entries, tracker));
const bundle = trackers => ({ version: 2, trackers });
const response = value => ({ ok: true, status: 200, json: async () => value });
const about = email => response({ user: { emailAddress: email } });
const local = (h, key) => JSON.parse(h.storage.get(key + ":v1")).entries;
const done = updatedAt => ({ status: 1, updatedAt });

// An in-memory appDataFolder that behaves like the Drive endpoints progress.js uses.
function fakeDrive({ email = "me@example.com", files = [] } = {}) {
  const store = new Map();
  let sequence = 0;
  for (const file of files) store.set(file.id || "seed" + (++sequence), { name: file.name, appProperties: file.appProperties || {}, body: file.body });
  const calls = [];
  async function fetch(url, options = {}) {
    calls.push({ url, options });
    const method = options.method || "GET";
    if (url.includes(ABOUT)) return about(email);
    if (url.includes("uploadType=multipart")) {
      const parts = options.body.split("\r\n\r\n");
      const metadata = JSON.parse(parts[1].split("\r\n--")[0]);
      const body = JSON.parse(parts[2].split("\r\n--")[0]);
      const id = "f" + (++sequence);
      store.set(id, { name: metadata.name, appProperties: metadata.appProperties, parents: metadata.parents, body });
      return response({ id });
    }
    const id = decodeURIComponent(url.match(/\/files\/([^?]+)/)?.[1] || "");
    if (url.includes("uploadType=media")) {
      assert.equal(method, "PATCH");
      store.get(id).body = JSON.parse(options.body);
      return response({ id });
    }
    if (method === "DELETE") {
      store.delete(id);
      return { ok: true, status: 204, json: async () => { throw new Error("no body"); } };
    }
    if (url.includes("alt=media")) return response(store.get(id).body);
    return response({ files: [...store].map(([id, file]) => ({ id, name: file.name, appProperties: file.appProperties })) });
  }
  const uploads = () => calls.filter(call => call.url.includes("/upload/"));
  const own = device => [...store.values()].find(file => file.name === "study-progress-" + device + ".json");
  return { fetch, store, calls, uploads, own };
}

test("legacy migration preserves numeric IDs and status priority", () => {
  const h = harness({ initial: { "py-status": JSON.stringify({ a: [1, "one"], b: ["two"], c: ["one"] }) } });
  assert.equal(h.visible["1"].status, 1);
  assert.equal(h.visible.one.status, 1);
  assert.equal(h.visible.two.status, 2);
  assert.equal(JSON.parse(h.storage.get("py-status:v1")).version, 1);
  assert.ok(h.storage.has("py-status"));
});

test("edits and clearing persist with increasing timestamps and survive reload", () => {
  const h = harness();
  h.tracker.set("one", 1);
  const before = h.visible.one.updatedAt;
  h.tracker.set("one", 0);
  assert.equal(h.visible.one.status, 0);
  assert.ok(h.visible.one.updatedAt > before);
  const reloaded = harness({ initial: Object.fromEntries(h.storage) });
  assert.equal(reloaded.visible.one.status, 0);
});

test("unknown item IDs and statuses are rejected", () => {
  const h = harness();
  assert.throws(() => h.tracker.set("<img src=x>", 1));
  assert.throws(() => h.tracker.set("one", 7));
});

test("merge is order independent; preserves tombstones and unknown future items", () => {
  const { api } = harness();
  const a = { one: { status: 3, updatedAt: 1 }, future: { status: 2, updatedAt: 1 } };
  const b = { one: { status: 0, updatedAt: 2 } };
  assert.deepEqual(api.merge(a, b), api.merge(b, a));
  assert.equal(api.merge(a, b).one.status, 0);
  assert.equal(api.merge(a, b).future.status, 2);
  assert.equal(api.merge(a, { one: { status: 1, updatedAt: 1 } }).one.status, 3);
});

test("validation rejects wrong trackers, malformed records, bad tracker names and oversized files", () => {
  const { api } = harness();
  const many = Object.fromEntries(Array.from({ length: 20001 }, (_, i) => ["x" + i, { status: 1, updatedAt: 1 }]));
  for (const bad of [
    null, {}, { ...data({}), tracker: "dsa-status" }, data([]),
    data({ one: { status: 4, updatedAt: 1 } }),
    data({ one: { status: 1, updatedAt: -1 } }),
    data({ one: { status: 1, updatedAt: 1.5 } }),
    data({ ["x".repeat(121)]: { status: 1, updatedAt: 1 } }),
    data(many)
  ]) assert.throws(() => api.validate(bad, "py-status"));
  assert.throws(() => api.legacy({ a: [null], b: [], c: [] }));
  const proto = api.validate(JSON.parse('{"version":1,"tracker":"py-status","entries":{"__proto__":{"status":1,"updatedAt":1}}}'), "py-status");
  assert.equal(Object.getPrototypeOf(proto), null);
  assert.equal({}.status, undefined);

  const tooMany = Object.fromEntries(Array.from({ length: 201 }, (_, i) => ["t" + i, {}]));
  for (const bad of [
    null, { version: 2 }, { version: 2, trackers: [] }, bundle(tooMany),
    bundle({ "Bad Name": {} }), bundle({ "a:v1": {} }), bundle({ "study-x": { one: { status: 9, updatedAt: 1 } } }),
    JSON.parse('{"version":2,"trackers":{"__proto__":{}}}'), { ...data({}), tracker: "<script>" }
  ]) assert.throws(() => api.validateAll(bad));
  const all = api.validateAll(bundle({ "py-status": { one: done(1) }, "rust-status": {} }));
  assert.deepEqual(Object.keys(all), ["py-status", "rust-status"]);
  assert.equal(Object.getPrototypeOf(all), null);
  assert.deepEqual(Object.keys(api.validateAll(data({ one: done(1) }, "dsa-status"))), ["dsa-status"]);
});

test("corrupt local data is surfaced and never overwritten by edits", () => {
  const h = harness({ initial: { "py-status:v1": "{broken" } });
  assert.match(h.el("local-status").textContent, /Could not load/);
  h.tracker.set("one", 1);
  assert.equal(h.storage.get("py-status:v1"), "{broken");
  assert.match(h.el("local-status").textContent, /not overwritten/);
  assert.equal(h.visible.one.status, 1);
});

test("storage failure still permits in-memory work and warns to export", () => {
  const h = harness({ denied: true });
  h.tracker.set("one", 1);
  assert.equal(h.visible.one.status, 1);
  assert.match(h.el("local-status").textContent, /Export/);
});

test("cross-tab changes merge, and a new edit reads the latest stored state", () => {
  const h = harness();
  h.storage.set("py-status:v1", json({ two: { status: 2, updatedAt: 10 } }));
  h.tracker.set("one", 1);
  assert.equal(h.visible.two.status, 2);
  h.fire("storage", { key: "py-status:v1", newValue: json({ two: { status: 3, updatedAt: Date.now() + 10000 } }) });
  assert.equal(h.visible.two.status, 3);
});

test("export writes one backup file holding every tracker", async () => {
  const h = harness({ initial: {
    "dsa-status:v1": json({ "1": done(5) }, "dsa-status"),
    "settings:v1": JSON.stringify({ theme: "dark" })
  } });
  h.tracker.set("one", 1);
  h.el("export-progress").onclick();
  const file = JSON.parse(await h.exported[0].text());
  assert.equal(file.version, 2);
  assert.deepEqual(Object.keys(file.trackers).sort(), ["dsa-status", "py-status"]);
  assert.equal(file.trackers["py-status"].one.status, 1);
  assert.equal(file.trackers["dsa-status"]["1"].status, 1);
  assert.match(h.el("local-status").textContent, /2 trackers/);
});

test("import merges every tracker in a backup, including older single-tracker files", async () => {
  const h = harness();
  h.tracker.set("one", 1);
  const load = async value => h.el("progress-file").onchange({ target: { files: [{ size: 100, text: async () => JSON.stringify(value) }], value: "file" } });
  await load(bundle({ "py-status": { two: { status: 2, updatedAt: 1 } }, "ml-status": { "c:x": done(3) } }));
  assert.equal(h.visible.one.status, 1);
  assert.equal(h.visible.two.status, 2);
  assert.equal(local(h, "ml-status")["c:x"].status, 1);
  await load(data({ "7": done(4) }, "dsa-status"));
  assert.equal(local(h, "dsa-status")["7"].status, 1);
  assert.match(h.el("cloud-status").textContent, /Backup merged/);
  const before = JSON.stringify([...h.storage]);
  await load(bundle({ "py-status": { one: { status: 0, updatedAt: 1 } }, "Bad Name": {} }));
  assert.match(h.el("cloud-status").textContent, /Invalid tracker name/);
  assert.equal(JSON.stringify([...h.storage]), before);
});

test("signed-out state shows the Google sign-in button and hides account controls", async () => {
  const h = harness();
  await tick();
  assert.equal(h.el("drive-connect").hidden, false);
  assert.equal(h.el("drive-sync").hidden, true);
  assert.equal(h.el("drive-menu").hidden, true);
  assert.match(h.el("cloud-status").textContent, /Sign in with Google once to sync every tracker/);
});

test("unconfigured Google explains setup without fetching", async () => {
  const h = harness({ clientId: "" });
  await h.el("drive-connect").onclick();
  assert.match(h.el("cloud-status").textContent, /not configured/);
  assert.equal(h.requests.length, 0);
});

test("file URLs never load Google sign-in", async () => {
  const h = harness({ protocol: "file:" });
  await tick();
  h.el("drive-connect").onclick();
  assert.match(h.el("cloud-status").textContent, /HTTPS site or a localhost server/);
  assert.equal(h.requests.length, 0);
});

test("one click signs in, remembers the account, and syncs immediately", async () => {
  const drive = fakeDrive();
  const h = harness({ fetch: drive.fetch });
  await h.connect();
  assert.equal(h.requests.length, 1);
  assert.deepEqual({ ...h.requests[0] }, { prompt: "select_account" });
  assert.equal(h.el("drive-connect").hidden, true);
  assert.equal(h.el("drive-menu").hidden, false);
  assert.equal(h.el("drive-account").textContent, "Signed in as me@example.com");
  assert.equal(h.el("drive-initial").textContent, "M");
  assert.equal(h.storage.get("study-drive-account"), "me@example.com");
  assert.match(h.el("cloud-status").textContent, /Synced with Google Drive/);
  for (const call of drive.calls) {
    assert.ok(call.url.startsWith("https://www.googleapis.com/"));
    assert.equal(call.options.headers.Authorization, "Bearer test-token");
    assert.equal(call.options.credentials, "omit");
  }
  const session = JSON.parse(h.storage.get(SESSION));
  assert.equal(session.token, "test-token");
  assert.ok(session.expiresAt > Date.now() && session.expiresAt <= Date.now() + 3600 * 1000);
  assert.deepEqual(Object.keys(session).sort(), ["expiresAt", "token"]);
  assert.equal([...h.storage.values()].filter(value => value.includes("test-token")).length, 1);

  const again = harness({ initial: { "study-drive-account": "me@example.com" }, fetch: drive.fetch });
  await again.connect();
  assert.deepEqual({ ...again.requests[0] }, { prompt: "", login_hint: "me@example.com" });
});

test("use another account forgets the hint and opens the account chooser", async () => {
  const h = harness({ initial: { "study-drive-account": "old@example.com" }, fetch: fakeDrive({ email: "new@example.com" }).fetch });
  await tick();
  h.el("drive-switch").onclick();
  await h.hub.idle();
  assert.deepEqual({ ...h.requests[0] }, { prompt: "select_account" });
  assert.equal(h.storage.get("study-drive-account"), "new@example.com");
});

test("one sign-in is shared by every page and tab of the site", async () => {
  const drive = fakeDrive();
  const storage = new Map();
  const python = harness({ storage, fetch: drive.fetch });
  const openTab = harness({ storage, fetch: drive.fetch, storageKey: "dsa-status", ids: ["1"] });
  python.tracker.set("one", 1);
  await python.connect();
  assert.equal(openTab.el("drive-connect").hidden, false);
  openTab.fire("storage", { key: SESSION, newValue: storage.get(SESSION) });
  assert.equal(openTab.el("drive-connect").hidden, true);
  assert.equal(openTab.el("drive-sync").hidden, false);

  // Opening another page later, including the home page with no tracker, needs no new sign-in.
  const home = harness({ storage, fetch: drive.fetch, tracker: false });
  assert.equal(home.requests.length, 0);
  assert.equal(home.el("drive-connect").hidden, true);
  assert.equal(home.el("drive-menu").hidden, false);
  assert.equal(home.el("drive-account").textContent, "Signed in as me@example.com");
  assert.match(home.el("cloud-status").textContent, /Signed in as me@example.com\. Last synced at/);
  const before = drive.calls.length;
  await home.sync();
  assert.equal(home.requests.length, 0);
  assert.ok(drive.calls.length > before);
  assert.ok(drive.calls.slice(before).every(call => call.options.headers.Authorization === "Bearer test-token"));
  assert.match(home.el("cloud-status").textContent, /Synced 1 tracker with Google Drive/);
});

test("signing out on one page signs out every page and removes the token", async () => {
  const drive = fakeDrive();
  const storage = new Map();
  const a = harness({ storage, fetch: drive.fetch });
  await a.connect();
  const b = harness({ storage, fetch: drive.fetch, tracker: false });
  assert.equal(b.el("drive-connect").hidden, true);
  a.el("drive-disconnect").onclick();
  assert.equal(storage.has(SESSION), false);
  assert.ok(![...storage.values()].some(value => value.includes("test-token")));
  b.fire("storage", { key: SESSION, newValue: null });
  assert.equal(b.el("drive-connect").hidden, false);
  assert.equal(b.el("drive-menu").hidden, true);
  assert.match(b.el("cloud-status").textContent, /Signed out on every page/);
  const c = harness({ storage, fetch: drive.fetch, tracker: false });
  assert.equal(c.el("drive-connect").hidden, false);
});

test("expired or malformed stored sessions are ignored and removed", () => {
  for (const value of [
    JSON.stringify({ token: "old", expiresAt: Date.now() - 1 }),
    JSON.stringify({ token: "", expiresAt: Date.now() + 60000 }),
    JSON.stringify({ token: 7, expiresAt: Date.now() + 60000 }),
    JSON.stringify({ token: "x".repeat(5000), expiresAt: Date.now() + 60000 }),
    "{broken"
  ]) {
    const h = harness({ initial: { [SESSION]: value }, tracker: false });
    assert.equal(h.el("drive-connect").hidden, false);
    assert.equal(h.storage.has(SESSION), false);
  }
});

test("Sync now syncs every tracker, including ones not open here and ones added later", async () => {
  const device = "this-device";
  const drive = fakeDrive({ files: [
    { id: "phone", name: "study-progress-phone.json", appProperties: { studyProgress: "2" },
      body: bundle({ "ai-status": { "c:llm": done(3) }, "rust-status": { "b:cli": done(4) }, "py-status": { two: { status: 2, updatedAt: 6 } } }) },
    { id: "old-laptop", name: "cpp-status-laptop.json", appProperties: { studyTracker: "cpp-status" }, body: data({ "c:raii": done(2) }, "cpp-status") },
    { id: "mine-old", name: "py-status-" + device + ".json", appProperties: { studyTracker: "py-status" }, body: data({ one: { status: 3, updatedAt: 1 } }) },
    { id: "unrelated", name: "notes.json", appProperties: {}, body: { hello: "world" } }
  ] });
  const h = harness({ fetch: drive.fetch, initial: {
    [DEVICE]: device,
    "dsa-status:v1": json({ "1": done(5) }, "dsa-status")
  } });
  h.tracker.set("one", 1);
  await h.connect();

  assert.match(h.el("cloud-status").textContent, /Synced 5 trackers with Google Drive/);
  assert.equal(h.visible.one.status, 1);
  assert.equal(h.visible.two.status, 2);
  assert.equal(local(h, "ai-status")["c:llm"].status, 1);
  assert.equal(local(h, "rust-status")["b:cli"].status, 1);
  assert.equal(local(h, "cpp-status")["c:raii"].status, 1);
  const own = drive.own(device);
  assert.deepEqual(own.appProperties, { studyProgress: "2" });
  assert.deepEqual(own.parents, ["appDataFolder"]);
  assert.deepEqual(Object.keys(own.body.trackers).sort(), ["ai-status", "cpp-status", "dsa-status", "py-status", "rust-status"]);
  assert.equal(own.body.trackers["py-status"].one.status, 1);
  assert.equal(drive.store.has("mine-old"), false, "this browser's old per-tracker file is retired");
  assert.equal(drive.store.has("old-laptop"), true, "other devices' files are never deleted");
  assert.equal(drive.store.has("phone"), true);
  assert.equal(drive.store.has("unrelated"), true);
});

test("Drive listing follows every page of results", async () => {
  const pages = [];
  const h = harness({ fetch: async (url, options) => {
    if (url.includes(ABOUT)) return about("me@example.com");
    if (url.includes("uploadType=multipart")) {
      assert.match(options.body, /"two":\{"status":2/);
      return response({ id: "new" });
    }
    if (url.includes("/remote?alt=media")) return response(bundle({ "py-status": { two: { status: 2, updatedAt: 10 } } }));
    pages.push(url);
    if (url.includes("pageToken=next")) return response({ files: [{ id: "remote", name: "study-progress-x.json", appProperties: { studyProgress: "2" } }] });
    return response({ files: [], nextPageToken: "next" });
  } });
  await h.connect();
  assert.equal(pages.length, 2);
  assert.equal(h.visible.two.status, 2);
});

test("Drive updates only this browser's file and preserves a remote unmark", async () => {
  const device = "existing-device";
  const drive = fakeDrive({ files: [
    { id: "own", name: "study-progress-" + device + ".json", appProperties: { studyProgress: "2" }, body: bundle({ "py-status": { one: done(1) } }) },
    { id: "other", name: "study-progress-other.json", appProperties: { studyProgress: "2" }, body: bundle({ "py-status": { one: { status: 0, updatedAt: 2 } } }) }
  ] });
  const h = harness({ fetch: drive.fetch, initial: { [DEVICE]: device, "py-status:v1": json({ one: done(1) }) } });
  await h.connect();
  assert.equal(h.visible.one.status, 0);
  assert.equal(drive.store.get("own").body.trackers["py-status"].one.status, 0);
  assert.equal(drive.uploads().length, 1);
  assert.ok(drive.uploads()[0].url.includes("/files/own?uploadType=media"));
  assert.equal(drive.store.size, 2);
});

test("Sync skips the upload when Drive already has this browser's progress", async () => {
  const drive = fakeDrive();
  const h = harness({ fetch: drive.fetch });
  h.tracker.set("one", 1);
  await h.connect();
  assert.equal(drive.uploads().length, 1);
  await h.sync();
  assert.equal(drive.uploads().length, 1);
  assert.match(h.el("cloud-status").textContent, /Synced 1 tracker/);
  h.tracker.set("two", 2);
  await h.sync();
  assert.equal(drive.uploads().length, 2);
});

test("edits made while signed in sync automatically", async () => {
  const drive = fakeDrive();
  const h = harness({ autoSync: true, fetch: drive.fetch });
  await h.connect();
  h.tracker.set("one", 1);
  assert.match(h.el("cloud-status").textContent, /Syncing shortly/);
  await tick(40);
  await h.hub.idle();
  assert.equal(drive.uploads().length, 1);
  assert.match(h.el("cloud-status").textContent, /Synced 1 tracker with Google Drive/);
  assert.equal(h.storage.has("study-drive-dirty"), false);
});

test("a change not yet synced when leaving a page is synced by the next page", async () => {
  const drive = fakeDrive();
  const storage = new Map();
  const first = harness({ storage, autoSync: true, syncDelay: 10000, fetch: drive.fetch });
  await first.connect();
  first.tracker.set("one", 1);
  assert.ok(storage.has("study-drive-dirty"));
  const next = harness({ storage, autoSync: true, fetch: drive.fetch, storageKey: "dsa-status", ids: ["1"] });
  assert.match(next.el("cloud-status").textContent, /Syncing your latest changes shortly/);
  await tick(40);
  await next.hub.idle();
  const own = drive.own(storage.get(DEVICE));
  assert.equal(own.body.trackers["py-status"].one.status, 1);
  assert.equal(storage.has("study-drive-dirty"), false);
  assert.equal(next.requests.length, 0);
});

test("keys that other apps on the same site use are left alone", async () => {
  const drive = fakeDrive();
  const initial = { "settings:v1": JSON.stringify({ theme: "dark" }), "notes:v1": "plain text", "Other:v1": json({}, "Other") };
  const h = harness({ fetch: drive.fetch, initial });
  h.tracker.set("one", 1);
  await h.connect();
  assert.match(h.el("cloud-status").textContent, /Synced 1 tracker/);
  for (const [key, value] of Object.entries(initial)) assert.equal(h.storage.get(key), value);
  assert.deepEqual(Object.keys(drive.own(h.storage.get(DEVICE)).body.trackers), ["py-status"]);
});

test("unreadable local progress for one tracker does not block the others or lose its Drive copy", async () => {
  const drive = fakeDrive({ files: [
    { id: "phone", name: "study-progress-phone.json", appProperties: { studyProgress: "2" },
      body: bundle({ "dsa-status": { "1": done(3) }, "ml-status": { "c:x": done(3) } }) }
  ] });
  const h = harness({ fetch: drive.fetch, initial: { "dsa-status:v1": "{broken" } });
  h.tracker.set("one", 1);
  await h.connect();
  assert.equal(h.storage.get("dsa-status:v1"), "{broken");
  assert.equal(local(h, "ml-status")["c:x"].status, 1);
  assert.match(h.el("cloud-status").textContent, /dsa-status could not be read/);
  const own = drive.own(h.storage.get(DEVICE));
  assert.equal(own.body.trackers["dsa-status"]["1"].status, 1);
  assert.equal(own.body.trackers["py-status"].one.status, 1);
});

test("failed Drive requests never report success or remove local progress", async () => {
  const h = harness({ fetch: async () => ({ ok: false, status: 403 }) });
  h.tracker.set("one", 1);
  await h.connect();
  assert.match(h.el("cloud-status").textContent, /HTTP 403/);
  assert.equal(h.visible.one.status, 1);
  assert.equal(h.el("drive-sync").disabled, false);
  assert.equal(h.el("drive-account").textContent, "Signed in with Google");
});

test("expired credentials require signing in again; sign-out preserves local progress", async () => {
  const h = harness({ onToken: options => options.callback({ access_token: "expired", expires_in: 0 }) });
  h.tracker.set("one", 1);
  await h.connect();
  assert.match(h.el("cloud-status").textContent, /expired/);
  assert.equal(h.el("drive-sync").disabled, true);
  assert.equal(h.el("drive-connect").hidden, false);
  assert.equal(h.storage.has(SESSION), false);
  h.el("drive-disconnect").onclick();
  assert.equal(h.visible.one.status, 1);
});

test("a rejected token signs every page out", async () => {
  const storage = new Map();
  let reject = false;
  const drive = fakeDrive();
  const fetch = async (url, options) => reject ? { ok: false, status: 401 } : drive.fetch(url, options);
  const h = harness({ storage, fetch });
  await h.connect();
  reject = true;
  await h.sync();
  assert.match(h.el("cloud-status").textContent, /expired/);
  assert.equal(h.el("drive-connect").hidden, false);
  assert.equal(storage.has(SESSION), false);
});

test("refused permission and closed pop-ups leave the user signed out", async () => {
  let refuse = true;
  const h = harness({ onToken: options => refuse
    ? options.callback({ error: "access_denied" })
    : options.error_callback({ type: "popup_closed" }) });
  await h.connect();
  assert.match(h.el("cloud-status").textContent, /access_denied/);
  assert.equal(h.el("drive-connect").hidden, false);
  assert.equal(h.el("drive-connect").disabled, false);
  assert.equal(h.storage.has(SESSION), false);
  refuse = false;
  await h.connect();
  assert.match(h.el("cloud-status").textContent, /closed/);
  assert.equal(h.el("drive-connect").disabled, false);
});

test("two devices converge without clobbering edits or resurrecting an unmarked item", async () => {
  const drive = fakeDrive();
  const a = harness({ fetch: drive.fetch });
  const b = harness({ fetch: drive.fetch, storageKey: "dsa-status", ids: ["1"] });
  await a.connect();
  await b.connect();
  a.tracker.set("one", 1);
  b.tracker.set("1", 2);
  await Promise.all([a.sync(), b.sync()]);
  await a.sync();
  await b.sync();
  assert.deepEqual(local(a, "py-status"), local(b, "py-status"));
  assert.deepEqual(local(a, "dsa-status"), local(b, "dsa-status"));
  assert.equal(local(b, "py-status").one.status, 1);
  assert.equal(local(a, "dsa-status")["1"].status, 2);
  a.tracker.set("one", 0);
  await a.sync();
  await b.sync();
  assert.equal(local(b, "py-status").one.status, 0);
  assert.equal(drive.store.size, 2);
});

test("upload failures retain merged progress and explicitly report failure", async () => {
  const h = harness({ fetch: async (url) => {
    if (url.includes(ABOUT)) return about("me@example.com");
    if (url.includes("uploadType")) return { ok: false, status: 503 };
    if (url.includes("alt=media")) return response(bundle({ "py-status": { two: { status: 2, updatedAt: 10 } } }));
    return response({ files: [{ id: "other", name: "other.json", appProperties: { studyProgress: "2" } }] });
  } });
  await h.connect();
  assert.equal(h.visible.two.status, 2);
  assert.match(h.el("cloud-status").textContent, /HTTP 503/);
  assert.ok(!h.el("cloud-status").textContent.includes("Synced"));
  assert.equal(h.storage.has("study-drive-synced"), false);
});

const escapeHtml = s => s.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;" }[c]));

test("generated pages keep every item, match the shared template and contain no inline code", () => {
  const template = fs.readFileSync(path.join(root, "_build/template.html"), "utf8");
  for (const name of ["python.html", "dsa.html", "cpp.html", "math.html", "ml.html", "ai.html"]) {
    const html = fs.readFileSync(path.join(root, name), "utf8");
    const payload = html.match(/<script type="application\/json" id="tracker-data">(.*?)<\/script>/s)[1];
    assert.ok(!payload.includes("<"));
    const value = JSON.parse(payload);
    const expected = template.replace("/*DATA*/", () => payload)
      .replace("__TITLE__", escapeHtml(value.title)).replace("__DESC__", escapeHtml(value.subtitle));
    assert.equal(html, expected);
    assert.match(value.storageKey, /^[a-z0-9][a-z0-9-]{0,62}$/);
    const ids = value.modules.flatMap(m => m.groups.flatMap(g => g.items.map(i => String(i.id))));
    assert.equal(new Set(ids).size, ids.length);
    assert.ok(ids.length > 200);
    const links = value.modules.flatMap(m => [...m.read, ...m.watch, ...m.groups.flatMap(g => g.items.flatMap(i => [i, ...(i.links || [])]))]);
    assert.ok(links.every(l => l.h.startsWith("https://")));
  }
});

test("every page has a strict Content Security Policy and no inline scripts or handlers", () => {
  const pages = fs.readdirSync(root).filter(f => f.endsWith(".html"));
  assert.ok(pages.length >= 6);
  for (const name of pages) {
    const html = fs.readFileSync(path.join(root, name), "utf8");
    const csp = html.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/);
    assert.ok(csp, name + " has a CSP");
    assert.match(csp[1], /default-src 'none'/);
    assert.match(csp[1], /base-uri 'none'/);
    assert.ok(!/unsafe-inline|unsafe-eval|\*/.test(csp[1]), name + " CSP is strict");
    for (const tag of html.match(/<script\b[^>]*>/g) || []) {
      assert.ok(/\bsrc="\.\/[a-z]+\.js"/.test(tag) || tag.includes('type="application/json"'), name + ": " + tag);
    }
    assert.ok(!/\son[a-z]+=/i.test(html.replace(/<script type="application\/json"[\s\S]*?<\/script>/, "")), name + " has no inline event handlers");
    for (const a of html.match(/<a [^>]*target="_blank"[^>]*>/g) || []) assert.match(a, /rel="noopener"/);
  }
});

test("every page with the app bar shares one sign-in: it loads config.js then progress.js and allows Google sign-in", () => {
  const pages = fs.readdirSync(root).filter(f => f.endsWith(".html"));
  const withBar = pages.filter(name => fs.readFileSync(path.join(root, name), "utf8").includes('class="appbar"'));
  assert.ok(withBar.length >= 8, withBar.join(", "));
  for (const name of withBar) {
    const html = fs.readFileSync(path.join(root, name), "utf8");
    const scripts = [...html.matchAll(/<script src="\.\/([a-z]+)\.js"><\/script>/g)].map(m => m[1]);
    assert.ok(scripts.indexOf("config") >= 0 && scripts.indexOf("config") < scripts.indexOf("progress"), name + " loads config.js then progress.js");
    assert.ok(!html.includes('id="drive-connect"'), name + " gets its account controls from progress.js");
    const csp = html.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)[1];
    assert.match(csp, /script-src 'self' https:\/\/accounts\.google\.com\/gsi\/client;/, name);
    assert.match(csp, /connect-src https:\/\/www\.googleapis\.com https:\/\/accounts\.google\.com\/gsi\/;/, name);
  }
});

test("config holds only a public OAuth client ID and the scope is app-data only", () => {
  const config = fs.readFileSync(path.join(root, "config.js"), "utf8");
  assert.match(config, /googleClientId: "\d+-[a-z0-9]+\.apps\.googleusercontent\.com"/);
  assert.ok(!/secret|GOCSPX|AIza|ya29\./i.test(config.replace("not a client secret", "")));
  const scopes = source.match(/https:\/\/www\.googleapis\.com\/auth\/[a-z.]+/g);
  assert.deepEqual([...new Set(scopes)], ["https://www.googleapis.com/auth/drive.appdata"]);
  // The token is only ever written to the one session key, together with its expiry.
  const writes = source.match(/write\(SESSION_KEY, [^;]+;/g);
  assert.deepEqual(writes.filter(w => !w.includes("null")), ["write(SESSION_KEY, JSON.stringify({ token, expiresAt }));"]);
  assert.ok(!/localStorage\.setItem\([^)]*token/i.test(source));
});
