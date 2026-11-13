// Captures docs/*.png from a running demo (API :8000, web :5173) via headless Edge + CDP.
// Usage: node scripts/screenshots.mjs   (needs Edge; no extra npm packages, Node 22+)
import { spawn } from "node:child_process";
import { writeFileSync, mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const EDGE = process.env.EDGE_PATH ?? "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const WEB = "http://localhost:5173";
const outDir = join(dirname(fileURLToPath(import.meta.url)), "..", "docs");
mkdirSync(outDir, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const login = await fetch(`${WEB}/api/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "demo@reviewdesk.dev", password: "demo-password" }),
}).then((r) => r.json());

const edge = spawn(EDGE, [
  "--headless=new",
  "--remote-debugging-port=9333",
  "--window-size=1280,800",
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "rd-edge-"))}`,
  "about:blank",
]);

let targets;
for (let i = 0; i < 40; i++) {
  try {
    targets = await (await fetch("http://127.0.0.1:9333/json")).json();
    if (targets.length) break;
  } catch {}
  await sleep(250);
}
const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = new Map();
ws.onmessage = (m) => {
  const msg = JSON.parse(m.data);
  if (msg.id && pending.has(msg.id)) pending.get(msg.id)(msg.result);
};
const send = (method, params = {}) =>
  new Promise((res) => {
    const myId = ++id;
    pending.set(myId, res);
    ws.send(JSON.stringify({ id: myId, method, params }));
  });
const evaluate = (expression) => send("Runtime.evaluate", { expression, awaitPromise: true });
async function shot(name) {
  const { data } = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(outDir, name), Buffer.from(data, "base64"));
  console.log("wrote", name);
}

await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
await send("Page.navigate", { url: WEB + "/login" });
await sleep(1500);
await evaluate(`localStorage.setItem("review-desk.token", ${JSON.stringify(login.access_token)})`);

// 1) dashboard
await send("Page.navigate", { url: WEB + "/" });
await sleep(2000);
await shot("dashboard.png");

// 2) new review, streamed with the demo (fake) provider
await send("Page.navigate", { url: WEB + "/new" });
await sleep(1500);
await evaluate(`(async () => {
  const click = (t) => [...document.querySelectorAll("button")].find((b) => b.textContent.includes(t)).click();
  const setVal = (el, v) => {
    const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement : HTMLInputElement;
    Object.getOwnPropertyDescriptor(proto.prototype, "value").set.call(el, v);
    el.dispatchEvent(new Event("input", { bubbles: true }));
  };
  setVal(document.querySelector("input[placeholder^='e.g.']"), "Login handler");
  click("Use sample code");
  await new Promise((r) => setTimeout(r, 200));
  click("Run review");
})()`);
await sleep(9000);
await shot("new-review.png");

ws.close();
edge.kill();
process.exit(0);
