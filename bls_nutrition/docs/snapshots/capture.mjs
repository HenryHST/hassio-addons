#!/usr/bin/env node
/** Capture demo HTML pages as PNG screenshots for documentation. */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const imagesDir = path.join(__dirname, "..", "images");

const captures = [
  ["demo-overview.html", "ingress-navigation.png"],
  ["demo-search.html", "ingress-search.png"],
  ["demo-portion.html", "ingress-portion.png"],
];

await mkdir(imagesDir, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
});

for (const [htmlFile, pngFile] of captures) {
  const page = await context.newPage();
  const fileUrl = `file://${path.join(__dirname, htmlFile)}`;
  await page.goto(fileUrl, { waitUntil: "networkidle" });
  await page.screenshot({
    path: path.join(imagesDir, pngFile),
    fullPage: false,
  });
  await page.close();
  console.log(`Wrote ${pngFile}`);
}

await browser.close();
