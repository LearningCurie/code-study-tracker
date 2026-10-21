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

function harness({ initial = {}, fetch, denied = false, clientId = "test-client", onToken, protocol = "https:", autoSync = false, syncDelay = 5 } = {}) {
  const storage = new Map(Object.entries(initial));
  const elements = new Map();
  const events = {};
  const requests = [];
  let visible;
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, { textContent: "", disabled: false, hidden: false, dataset: {}, click() {} });
      return elements.get(id);
    }
  };
  const context = {
    document, console: { error() {} }, crypto: webcrypto,
    setTimeout, clearTimeout, AbortSignal, URL, URLSearchParams, Blob,
    location: { protocol },
    navigator: { locks: { request: async (_name, callback) => callback() } },
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem(key, value) { if (denied) throw new Error("Storage denied"); storage.set(key, value); },
      removeItem(key) { storage.delete(key); }
    },
    confirm: () => true,
    addEventListener(name, callback) { events[name] = callback; },
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
  const tracker = api.mount({
    storageKey: "py-status", ids: ["one", "two"], clientId, autoSync, syncDelay,
    onChange: entries => { visible = JSON.parse(JSON.stringify(entries)); }
  });
  const el = id => document.getElementById(id);
  return {
    api, tracker, storage, events, requests, el,
    get visible() { return visible; },
    async connect() {
      await tick();
      el("drive-connect").onclick();
      await tracker.idle();
    },
    async sync() {
      el("drive-sync").onclick();
      await tracker.idle();
    }
  };
}
const data = entries => ({ version: 1, tracker: "py-status", entries });
const json = entries => JSON.stringify(data(entries));
const response = value => ({ ok: true, status: 200, json: async () => value });
const about = email => response({ user: { emailAddress: email } });

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

test("backup validation rejects wrong trackers, malformed records and oversized files", () => {
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
  h.events.storage({ key: "py-status:v1", newValue: json({ two: { status: 3, updatedAt: Date.now() + 10000 } }) });
  assert.equal(h.visible.two.status, 3);
});

test("backup import merges and wrong-tracker import leaves state unchanged", async () => {
  const h = harness();
  h.tracker.set("one", 1);
  await h.el("progress-file").onchange({ target: { files: [{ size: 100, text: async () => json({ two: { status: 2, updatedAt: 1 } }) }], value: "file" } });
  assert.equal(h.visible.one.status, 1);
  assert.equal(h.visible.two.status, 2);
  await h.el("progress-file").onchange({ target: { files: [{ size: 100, text: async () => JSON.stringify({ ...data({}), tracker: "dsa-status" }) }], value: "file" } });
  assert.equal(h.visible.one.status, 1);
  assert.match(h.el("cloud-status").textContent, /wrong tracker/);
});

test("signed-out state shows the Google sign-in button and hides account controls", async () => {
  const h = harness();
  await tick();
  assert.equal(h.el("drive-connect").hidden, false);
  assert.equal(h.el("drive-sync").hidden, true);
  assert.equal(h.el("drive-menu").hidden, true);
  assert.match(h.el("cloud-status").textContent, /Sign in with Google/);
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
  const calls = [];
  const h = harness({ fetch: async (url, options) => {
    calls.push({ url, options });
    if (url.includes(ABOUT)) return about("me@example.com");
    if (url.includes("uploadType=multipart")) return response({ id: "new" });
    return response({ files: [] });
  } });
  await h.connect();
  assert.equal(h.requests.length, 1);
  assert.deepEqual({ ...h.requests[0] }, { prompt: "select_account" });
  assert.equal(h.el("drive-connect").hidden, true);
  assert.equal(h.el("drive-menu").hidden, false);
  assert.equal(h.el("drive-account").textContent, "Signed in as me@example.com");
  assert.equal(h.el("drive-initial").textContent, "M");
  assert.equal(h.storage.get("study-drive-account"), "me@example.com");
  assert.match(h.el("cloud-status").textContent, /Synced with Google Drive/);
  for (const call of calls) {
    assert.ok(call.url.startsWith("https://www.googleapis.com/"));
    assert.equal(call.options.headers.Authorization, "Bearer test-token");
    assert.equal(call.options.credentials, "omit");
  }
  assert.ok(![...h.storage.values()].some(value => value.includes("test-token")));

  const again = harness({ initial: Object.fromEntries(h.storage), fetch: async url => url.includes(ABOUT) ? about("me@example.com") : response({ files: [] }) });
  await again.connect();
  assert.deepEqual({ ...again.requests[0] }, { prompt: "", login_hint: "me@example.com" });
});

test("use another account forgets the hint and opens the account chooser", async () => {
  const h = harness({ initial: { "study-drive-account": "old@example.com" }, fetch: async url => url.includes(ABOUT) ? about("new@example.com") : response({ files: [] }) });
  await tick();
  h.el("drive-switch").onclick();
  await h.tracker.idle();
  assert.deepEqual({ ...h.requests[0] }, { prompt: "select_account" });
  assert.equal(h.storage.get("study-drive-account"), "new@example.com");
});

test("Drive reads all pages and merges snapshots before creating its own", async () => {
  const calls = [];
  const h = harness({ fetch: async (url, options) => {
    calls.push({ url, options });
    if (url.includes(ABOUT)) return about("me@example.com");
    if (url.includes("uploadType=multipart")) {
      assert.match(options.body, /"one":\{"status":1/);
      assert.match(options.body, /"two":\{"status":2/);
      assert.match(options.body, /"parents":\["appDataFolder"\]/);
      return response({ id: "new" });
    }
    if (url.includes("/remote?alt=media")) return response(data({ two: { status: 2, updatedAt: 10 } }));
    if (url.includes("pageToken=next")) return response({ files: [] });
    return response({ files: [{ id: "remote", name: "other-device.json" }], nextPageToken: "next" });
  } });
  h.tracker.set("one", 1);
  await h.connect();
  assert.equal(calls.length, 5);
  assert.equal(h.visible.two.status, 2);
  assert.match(h.el("cloud-status").textContent, /Synced with Google Drive/);
});

test("Drive updates only this device snapshot and preserves a remote unmark", async () => {
  const device = "existing-device";
  let uploaded;
  const h = harness({
    initial: { "study-drive-device": device, "py-status:v1": json({ one: { status: 1, updatedAt: 1 } }) },
    fetch: async (url, options) => {
      if (url.includes(ABOUT)) return about("me@example.com");
      if (url.includes("uploadType=media")) {
        assert.equal(options.method, "PATCH");
        uploaded = JSON.parse(options.body);
        return response({ id: "own" });
      }
      if (url.includes("?alt=media")) return response(data({ one: { status: 0, updatedAt: 2 } }));
      return response({ files: [{ id: "own", name: "py-status-" + device + ".json" }] });
    }
  });
  await h.connect();
  assert.equal(h.visible.one.status, 0);
  assert.equal(uploaded.entries.one.status, 0);
});

test("edits made while signed in sync automatically", async () => {
  let uploads = 0;
  const h = harness({ autoSync: true, fetch: async url => {
    if (url.includes(ABOUT)) return about("me@example.com");
    if (url.includes("uploadType")) { uploads++; return response({ id: "own" }); }
    if (url.includes("alt=media")) return response(data({}));
    return response({ files: uploads ? [{ id: "own", name: "x" }] : [] });
  } });
  await h.connect();
  assert.equal(uploads, 1);
  h.tracker.set("one", 1);
  assert.match(h.el("cloud-status").textContent, /Syncing shortly/);
  await tick(40);
  await h.tracker.idle();
  assert.equal(uploads, 2);
  assert.match(h.el("cloud-status").textContent, /Synced with Google Drive/);
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
  h.el("drive-disconnect").onclick();
  assert.equal(h.visible.one.status, 1);
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
  refuse = false;
  await h.connect();
  assert.match(h.el("cloud-status").textContent, /closed/);
  assert.equal(h.el("drive-connect").disabled, false);
});

test("two devices converge without clobbering edits or resurrecting an unmarked item", async () => {
  const cloud = new Map();
  let sequence = 0;
  async function drive(url, options) {
    if (url.includes(ABOUT)) return about("me@example.com");
    if (url.includes("uploadType=multipart")) {
      const parts = options.body.split("\r\n\r\n");
      const metadata = JSON.parse(parts[1].split("\r\n--")[0]);
      const progress = JSON.parse(parts[2].split("\r\n--")[0]);
      const id = String(++sequence);
      cloud.set(id, { name: metadata.name, progress });
      return response({ id });
    }
    const id = url.match(/\/files\/([^?]+)/)?.[1];
    if (url.includes("uploadType=media")) {
      cloud.get(id).progress = JSON.parse(options.body);
      return response({ id });
    }
    if (url.includes("alt=media")) return response(cloud.get(id).progress);
    return response({ files: [...cloud].map(([id, file]) => ({ id, name: file.name })) });
  }
  const a = harness({ fetch: drive });
  const b = harness({ fetch: drive });
  await a.connect();
  await b.connect();
  a.tracker.set("one", 1);
  b.tracker.set("two", 2);
  await Promise.all([a.sync(), b.sync()]);
  await a.sync();
  await b.sync();
  assert.deepEqual(a.visible, b.visible);
  assert.equal(a.visible.one.status, 1);
  assert.equal(a.visible.two.status, 2);
  a.tracker.set("one", 0);
  await a.sync();
  await b.sync();
  assert.equal(b.visible.one.status, 0);
  assert.equal(cloud.size, 2);
});

test("upload failures retain merged progress and explicitly report failure", async () => {
  const h = harness({ fetch: async (url) => {
    if (url.includes(ABOUT)) return about("me@example.com");
    if (url.includes("uploadType")) return { ok: false, status: 503 };
    if (url.includes("alt=media")) return response(data({ two: { status: 2, updatedAt: 10 } }));
    return response({ files: [{ id: "other", name: "other.json" }] });
  } });
  await h.connect();
  assert.equal(h.visible.two.status, 2);
  assert.match(h.el("cloud-status").textContent, /HTTP 503/);
  assert.ok(!h.el("cloud-status").textContent.includes("Synced"));
});

const escapeHtml = s => s.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;" }[c]));

test("generated pages keep every item, match the shared template and contain no inline code", () => {
  const template = fs.readFileSync(path.join(root, "_build/template.html"), "utf8");
  for (const name of ["python.html", "dsa.html"]) {
    const html = fs.readFileSync(path.join(root, name), "utf8");
    const payload = html.match(/<script type="application\/json" id="tracker-data">(.*?)<\/script>/s)[1];
    assert.ok(!payload.includes("<"));
    const value = JSON.parse(payload);
    const expected = template.replace("/*DATA*/", () => payload)
      .replace("__TITLE__", escapeHtml(value.title)).replace("__DESC__", escapeHtml(value.subtitle));
    assert.equal(html, expected);
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

test("config holds only a public OAuth client ID and the scope is app-data only", () => {
  const config = fs.readFileSync(path.join(root, "config.js"), "utf8");
  assert.match(config, /googleClientId: "\d+-[a-z0-9]+\.apps\.googleusercontent\.com"/);
  assert.ok(!/secret|GOCSPX|AIza|ya29\./i.test(config.replace("not a client secret", "")));
  const scopes = source.match(/https:\/\/www\.googleapis\.com\/auth\/[a-z.]+/g);
  assert.deepEqual([...new Set(scopes)], ["https://www.googleapis.com/auth/drive.appdata"]);
  assert.ok(!/localStorage\.setItem\([^)]*token/i.test(source));
});
