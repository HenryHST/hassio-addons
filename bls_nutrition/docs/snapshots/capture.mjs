#!/usr/bin/env node
/** Capture demo HTML pages as PNG screenshots for documentation. */
import { chromium } from "playwright";
import { mkdir, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const imagesDir = path.join(__dirname, "..", "images");

const ALL_CAPTURES = [
  { id: "navigation", html: "demo-overview.html", png: "ingress-navigation.png" },
  { id: "search", html: "demo-search.html", png: "ingress-search.png" },
  { id: "portion", html: "demo-portion.html", png: "ingress-portion.png" },
  { id: "barcode", html: "demo-barcode.html", png: "ingress-barcode.png" },
  { id: "recipe", html: "demo-recipe.html", png: "ingress-recipe.png" },
  { id: "dark", html: "demo-dark.html", png: "ingress-dark.png" },
];

function parseOnlyArg(argv) {
  const onlyIdx = argv.indexOf("--only");
  if (onlyIdx === -1) return null;
  const value = argv[onlyIdx + 1];
  if (!value) {
    console.error("Error: --only requires a comma-separated list (e.g. search,barcode)");
    process.exit(1);
  }
  return new Set(
    value
      .split(",")
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean)
  );
}

function resolveCaptures(onlySet) {
  if (!onlySet) return ALL_CAPTURES;
  const selected = ALL_CAPTURES.filter((c) => onlySet.has(c.id));
  if (!selected.length) {
    console.error(
      `Error: --only matched no captures. Valid ids: ${ALL_CAPTURES.map((c) => c.id).join(", ")}`
    );
    process.exit(1);
  }
  return selected;
}

async function launchBrowser() {
  const launchOptions = { headless: true };
  try {
    return await chromium.launch(launchOptions);
  } catch (err) {
    console.warn("Chromium launch failed, trying system Chrome channel…");
    try {
      return await chromium.launch({ ...launchOptions, channel: "chrome" });
    } catch (chromeErr) {
      console.error("Failed to launch browser:", chromeErr.message || chromeErr);
      process.exit(1);
    }
  }
}

async function verifyOutput(filePath) {
  const info = await stat(filePath);
  if (!info.size) {
    throw new Error(`Screenshot is empty: ${filePath}`);
  }
}

const onlySet = parseOnlyArg(process.argv.slice(2));
const captures = resolveCaptures(onlySet);

for (const { html } of captures) {
  const htmlPath = path.join(__dirname, html);
  try {
    await stat(htmlPath);
  } catch {
    console.error(`Error: missing demo file ${htmlPath}`);
    process.exit(1);
  }
}

await mkdir(imagesDir, { recursive: true });

const browser = await launchBrowser();
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
});

const written = [];

for (const { html, png } of captures) {
  const page = await context.newPage();
  const fileUrl = `file://${path.join(__dirname, html)}`;
  await page.goto(fileUrl, { waitUntil: "load" });
  await page.waitForSelector(".app");
  const outPath = path.join(imagesDir, png);
  await page.screenshot({ path: outPath, fullPage: false });
  await verifyOutput(outPath);
  await page.close();
  written.push(png);
  console.log(`Wrote ${png}`);
}

await browser.close();
console.log(`\nDone: ${written.length} screenshot(s) → ${imagesDir}/`);
