const puppeteer = require("puppeteer-core");
const path = require("path");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true,
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844 });
  const fixture = "file://" + path.join(__dirname, "debug-layout-fixture.html");
  await page.goto(fixture);
  const metrics = await page.evaluate(() => {
    const input = document.querySelector(".portion-custom-input");
    const column = document.querySelector(".search-column");
    const wrap = document.querySelector(".result-item-wrap");
    const grid = document.getElementById("grid");
    const ir = input.getBoundingClientRect();
    const cr = column.getBoundingClientRect();
    const cs = getComputedStyle(input);
    return {
      viewport: window.innerWidth,
      gridWidth: grid.getBoundingClientRect().width,
      columnWidth: cr.width,
      wrapWidth: wrap.getBoundingClientRect().width,
      inputWidth: ir.width,
      inputRight: ir.right,
      columnRight: cr.right,
      overflow: ir.right > cr.right + 1,
      computedWidth: cs.width,
      computedMinWidth: cs.minWidth,
      computedFlex: cs.flex,
      inputClasses: input.className,
    };
  });
  console.log(JSON.stringify(metrics, null, 2));
  await browser.close();
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
