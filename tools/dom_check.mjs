/**
 * Executes the real dist/index.html + dist/app.js in a DOM and inspects what the
 * page actually builds. This is the closest thing to a browser we can run here,
 * and it verifies the *behaviour* (grid, hero, pour bottle, dialogs, station
 * board, filters) rather than just the source text.
 *
 * Requires jsdom:   npm install jsdom
 * Run:              node tools/dom_check.mjs [distDir]
 */
import { JSDOM } from "jsdom";
import fs from "node:fs";
import path from "node:path";

const dist = process.argv[2] ?? path.join(process.cwd(), "dist");
const html = fs.readFileSync(path.join(dist, "index.html"), "utf8");
const app = fs.readFileSync(path.join(dist, "app.js"), "utf8");

const fails = [];
const check = (ok, msg) => {
  console.log(`  ${ok ? "PASS" : "FAIL"}  ${msg}`);
  if (!ok) fails.push(msg);
};

function makeDom(headHtml) {
  const dom = new JSDOM(headHtml, { url: "http://localhost/", pretendToBeVisual: true, runScripts: "outside-only" });
  const { window } = dom;
  // Minimal stubs for APIs jsdom does not implement.
  window.matchMedia = (q) => ({
    matches: false, media: q, onchange: null,
    addEventListener() {}, removeEventListener() {},
    addListener() {}, removeListener() {}, dispatchEvent: () => false,
  });
  window.IntersectionObserver = class {
    constructor() {} observe() {} unobserve() {} disconnect() {} takeRecords() { return []; }
  };
  window.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  window.AudioContext = class {
    constructor() { this.currentTime = 0; this.sampleRate = 44100; this.destination = {}; }
    createBuffer() { return { getChannelData: () => new Float32Array(8) }; }
    createBufferSource() { return { buffer: null, loop: false, connect() {}, start() {}, stop() {} }; }
    createBiquadFilter() { return { type: "", Q: { value: 0 }, frequency: { setTargetAtTime() {} }, connect() {} }; }
    createGain() { return { gain: { value: 0, setTargetAtTime() {} }, connect() {} }; }
    createOscillator() {
      return { type: "", frequency: { value: 0, setValueAtTime() {}, exponentialRampToValueAtTime() {} },
               connect() {}, start() {}, stop() {} };
    }
    resume() { return Promise.resolve(); }
  };
  // The page re-measures once webfonts settle.
  if (!window.document.fonts) window.document.fonts = { ready: Promise.resolve() };
  window.Element.prototype.setPointerCapture = function () {};
  window.Element.prototype.releasePointerCapture = function () {};
  window.Element.prototype.scrollIntoView = function () {};
  window.HTMLElement.prototype.showModal = function () { this.open = true; };
  window.HTMLDialogElement && (window.HTMLDialogElement.prototype.showModal = function () { this.open = true; });
  window.HTMLDialogElement && (window.HTMLDialogElement.prototype.close = function () { this.open = false; });
  window.requestAnimationFrame = (fn) => setTimeout(() => fn(performance.now()), 16);
  window.cancelAnimationFrame = (id) => clearTimeout(id);
  window.HTMLMediaElement && (window.HTMLMediaElement.prototype.play = () => Promise.resolve());
  return dom;
}

const dom = makeDom(html);
const { window } = dom;
const { document } = window;

// Run the page script exactly as the browser would.
window.eval(app);
await new Promise((r) => setTimeout(r, 120));

console.log("\n1. product grid");
const grid = document.querySelector("#product-grid");
const buttons = [...grid.querySelectorAll(".product")];
check(buttons.length === 9, `grid renders 9 products (found ${buttons.length})`);

const imgs = [...grid.querySelectorAll(".product-visual svg image")];
const hrefs = imgs.map((i) => i.getAttribute("href"));
check(imgs.length === 9, `each product renders one bottle svg image (found ${imgs.length})`);
check(hrefs.every((h) => h.startsWith("assets/mm-")), `all grid bottles are Saksham Moments assets`);
check(new Set(hrefs).size === 9, `all 9 grid bottles are distinct files`);

const names = [...grid.querySelectorAll(".product-name")].map((n) => n.textContent);
const expected = ["Premium Grain Vodka", "Triple Distilled", "Dazzle Gold", "Verve Super Premium",
  "Verve Cranberry", "Verve Orange", "Remix Green Apple", "Remix Lemongrass & Ginger",
  "Remix Raspberry"];
check(JSON.stringify(names) === JSON.stringify(expected), `product names in order: ${names.join(", ")}`);

console.log("\n2. hero + pour bottle geometry");
const heroImg = document.querySelector("#hero-bottle svg image");
check(heroImg?.getAttribute("href") === "assets/mm-premium-grain.webp",
  `hero shows the Saksham Moments bottle (${heroImg?.getAttribute("href")})`);
const heroSvg = document.querySelector("#hero-bottle svg");
check(heroSvg.getAttribute("width") === "234" && heroSvg.getAttribute("height") === "886",
  `hero viewBox/size unchanged: ${heroSvg.getAttribute("width")}x${heroSvg.getAttribute("height")}`);

const pourBottle = document.querySelector("#pour-bottle image");
const bw = 62, expectBh = (bw * 886 / 234).toFixed(1);
check(pourBottle?.getAttribute("href") === "assets/mm-premium-grain.webp",
  `pour scene uses the same bottle (${pourBottle?.getAttribute("href")})`);
check(pourBottle.getAttribute("width") === String(bw) &&
      pourBottle.getAttribute("height") === expectBh,
  `pour bottle length bh = ${pourBottle.getAttribute("height")} (expected ${expectBh} - unchanged)`);
const pourGroup = pourBottle.closest("g");
check(/translate\(214 128\)/.test(pourGroup.getAttribute("transform")),
  `pour transform origin still P(214,128): ${pourGroup.getAttribute("transform")}`);

console.log("\n3. interactions");
const first = buttons[0];
first.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
const dialog = document.querySelector("#dialog-content");
check(dialog.textContent.includes("Premium Grain Vodka"),
  `clicking a product opens its detail dialog (${dialog.querySelector("h2")?.textContent})`);
check(dialog.querySelector(".detail-art svg image")?.getAttribute("href") === "assets/mm-premium-grain.webp",
  "dialog art shows the same bottle");

const stationBtns = [...document.querySelectorAll(".departure")];
check(document.querySelector(".footer")?.textContent.includes("Made by Saksham"),
  "footer shows the Made by Saksham credit");

check(stationBtns.length === 8, `station board renders 8 cities (found ${stationBtns.length})`);
stationBtns[1].dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
const plate = document.querySelector("#station-plate");
check(plate.textContent.includes("Saksham Moments "),
  `station pairing names a Saksham Moments product: "${plate.querySelector(".plate-pair")?.textContent}"`);
check(plate.querySelector(".plate-bottle svg image")?.getAttribute("href")?.startsWith("assets/mm-"),
  "station plate shows a Saksham Moments bottle");

const filters = [...document.querySelectorAll(".filters button")];
filters.find((b) => b.dataset.filter === "flavour")
  .dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
const visible = buttons.filter((b) => !b.hidden);
check(visible.length === 3, `'Remix flavours' filter shows 3 products (found ${visible.length})`);
filters.find((b) => b.dataset.filter === "all")
  .dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
check(buttons.filter((b) => !b.hidden).length === 9, "the 'All products' filter restores all 9");

console.log("\n4. indian layer intact");
check(document.querySelectorAll(".diya").length === 6, `6 diyas under the headline`);
check(document.querySelector(".toran-rope") !== null, "marigold toran still drawn");
check(document.querySelectorAll(".departure").length === 8, "departures board intact");

console.log("\n" + (fails.length ? `${fails.length} FAILURE(S)` : "ALL DOM CHECKS PASSED"));
process.exit(fails.length ? 1 : 0);
