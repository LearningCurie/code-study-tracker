const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const { webcrypto } = require("node:crypto");
const source = fs.readFileSync(require.resolve("../progress.js"), "utf8");

function harness({ initial = {}, fetch, denied = false, clientId = "test-client", onToken } = {}) {
  const storage = new Map(Object.entries(initial));
  const elements = new Map();
  const events = {};
  let visible, tokenOptions;
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, { textContent: "", disabled: false, click() {} });
      return elements.get(id);
    }
  };
  const context = {
    document, console: { error() {} }, crypto: webcrypto,
    setTimeout, clearTimeout, AbortSignal, URL, URLSearchParams, Blob,
    location: { protocol: "https:" },
    navigator: { locks: { request: async (_name, callback) => callback() } },
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem(key, value) { if (denied) throw new Error("Storage denied"); storage.set(key, value); }
    },
    confirm: () => true,
    addEventListener(name, callback) { events[name] = callback; },
    fetch: fetch || (() => { throw new Error("Unexpected fetch"); }),
    google: { accounts: { oauth2: {
      hasGrantedAllScopes: () => true,
      initTokenClient(options) {
        tokenOptions = options;
        return { requestAccessToken() {
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
    storageKey: "py-status", ids: ["one", "two"], clientId,
    onChange: entries => { visible = JSON.parse(JSON.stringify(entries)); }
  });
  return {
    api, tracker, storage, events, context,
    get visible() { return visible; },
    el: id => document.getElementById(id),
    async connect() {
      await document.getElementById("drive-connect").onclick();
      await document.getElementById("drive-connect").onclick();
    },
    get tokenOptions() { return tokenOptions; }
  };
}
const data = entries => ({ version: 1, tracker: "py-status", entries });
const json = entries => JSON.stringify(data(entries));
const response = value => ({ ok: true, status: 200, json: async () => value });

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

test("merge is order independent; preserves tombstones and unknown future items", () => {
  const { api } = harness();
  const a = { one: { status: 3, updatedAt: 1 }, future: { status: 2, updatedAt: 1 } };
  const b = { one: { status: 0, updatedAt: 2 } };
  assert.deepEqual(api.merge(a, b), api.merge(b, a));
  assert.equal(api.merge(a, b).one.status, 0);
  assert.equal(api.merge(a, b).future.status, 2);
  assert.equal(api.merge(a, { one: { status: 1, updatedAt: 1 } }).one.status, 3);
});

test("backup validation rejects wrong trackers and malformed records", () => {
  const { api } = harness();
  for (const bad of [
    null, {}, { ...data({}), tracker: "dsa-status" }, data([]),
    data({ one: { status: 4, updatedAt: 1 } }),
    data({ one: { status: 1, updatedAt: -1 } }),
    data({ one: { status: 1, updatedAt: 1.5 } })
  ]) assert.throws(() => api.validate(bad, "py-status"));
  assert.throws(() => api.legacy({ a: [null], b: [], c: [] }));
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

test("unconfigured Google provides setup instructions without fetching", async () => {
  const h = harness({ clientId: "" });
  await h.el("drive-connect").onclick();
  assert.match(h.el("cloud-status").textContent, /not configured/);
});

test("Drive reads all pages and merges snapshots before creating its own", async () => {
  const calls = [];
  const h = harness({ fetch: async (url, options) => {
    calls.push({ url, options });
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
  await h.el("drive-sync").onclick();
  assert.equal(calls.length, 4);
  assert.equal(h.visible.two.status, 2);
  assert.match(h.el("cloud-status").textContent, /Synced with Google Drive/);
  assert.equal(calls[0].options.headers.Authorization, "Bearer test-token");
  assert.ok(![...h.storage.values()].some(value => value.includes("test-token")));
});

test("Drive updates only this device snapshot and preserves a remote unmark", async () => {
  const device = "existing-device";
  let uploaded;
  const h = harness({
    initial: { "study-drive-device": device, "py-status:v1": json({ one: { status: 1, updatedAt: 1 } }) },
    fetch: async (url, options) => {
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
  await h.el("drive-sync").onclick();
  assert.equal(h.visible.one.status, 0);
  assert.equal(uploaded.entries.one.status, 0);
});

test("failed Drive requests never report success or remove local progress", async () => {
  const h = harness({ fetch: async () => ({ ok: false, status: 403 }) });
  h.tracker.set("one", 1);
  await h.connect();
  await h.el("drive-sync").onclick();
  assert.match(h.el("cloud-status").textContent, /HTTP 403/);
  assert.equal(h.visible.one.status, 1);
  assert.equal(h.el("drive-sync").disabled, false);
});

test("expired credentials require reconnect; disconnect preserves local progress", async () => {
  const h = harness({ onToken: options => options.callback({ access_token: "expired", expires_in: 0 }) });
  h.tracker.set("one", 1);
  await h.connect();
  await h.el("drive-sync").onclick();
  assert.match(h.el("cloud-status").textContent, /expired/);
  assert.equal(h.el("drive-sync").disabled, true);
  h.el("drive-disconnect").onclick();
  assert.equal(h.visible.one.status, 1);
});

test("two devices converge without clobbering edits or resurrecting an unmarked item", async () => {
  const cloud = new Map();
  let sequence = 0;
  async function drive(url, options) {
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
  await Promise.all([a.el("drive-sync").onclick(), b.el("drive-sync").onclick()]);
  await a.el("drive-sync").onclick();
  await b.el("drive-sync").onclick();
  assert.deepEqual(a.visible, b.visible);
  assert.equal(a.visible.one.status, 1);
  assert.equal(a.visible.two.status, 2);
  a.tracker.set("one", 0);
  await a.el("drive-sync").onclick();
  await b.el("drive-sync").onclick();
  assert.equal(b.visible.one.status, 0);
  assert.equal(cloud.size, 2);
});

test("upload failures retain merged progress and explicitly report failure", async () => {
  const h = harness({ fetch: async (url) => {
    if (url.includes("uploadType")) return { ok: false, status: 503 };
    if (url.includes("alt=media")) return response(data({ two: { status: 2, updatedAt: 10 } }));
    return response({ files: [{ id: "other", name: "other.json" }] });
  } });
  await h.connect();
  await h.el("drive-sync").onclick();
  assert.equal(h.visible.two.status, 2);
  assert.match(h.el("cloud-status").textContent, /HTTP 503/);
  assert.ok(!h.el("cloud-status").textContent.includes("Synced"));
});

test("generated pages retain every DATA item and match the shared template", () => {
  const path = require("node:path");
  const root = path.dirname(require.resolve("../progress.js"));
  const template = fs.readFileSync(path.join(root, "_build/template.html"), "utf8");
  for (const name of ["Python track_ Intermediate to Senior.html", "DSA problem tracker_ Easy, Medium, Hard.html"]) {
    const html = fs.readFileSync(path.join(root, name), "utf8");
    const payload = html.match(/^const DATA=(.*);$/m)[1];
    const value = JSON.parse(payload);
    assert.equal(html, template.replace("/*DATA*/null", () => payload).replace("__TITLE__", value.title));
    const ids = value.modules.flatMap(m => m.groups.flatMap(g => g.items.map(i => String(i.id))));
    assert.equal(new Set(ids).size, ids.length);
    assert.ok(ids.length > 200);
    assert.ok(!html.includes("claude.use"));
  }
});
