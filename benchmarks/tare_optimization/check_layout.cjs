// Render only the local report artifact, without accessing external sites.
const { chromium } = require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch({headless: true, channel: 'msedge'});
  const page = await browser.newPage({viewport: {width: 1680, height: 1100}});
  await page.goto('file:///D:/STGPlanner/codex/outputs/TARE优化测试报告.html', {waitUntil: 'load'});
  const result = await page.evaluate(() => ({
    title: document.title,
    tableRows: document.querySelector('table').rows.length,
    pageWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    brokenImages: [...document.images].filter(i => !i.complete || !i.naturalWidth).length,
    restored: document.body.innerText.includes('已恢复并重建原生原配置'),
    allResultsPresent: ['1277.279','996.477','976.461','1060.356'].every(s => document.body.innerText.includes(s))
  }));
  if (result.tableRows !== 6 || result.brokenImages || result.pageWidth !== result.scrollWidth || !result.restored || !result.allResultsPresent) {
    throw new Error(JSON.stringify(result));
  }
  await page.screenshot({path: 'D:/STGPlanner/codex/outputs/TARE优化测试报告.preview.png', fullPage: false});
  fs.writeFileSync('D:/STGPlanner/codex/outputs/tare_optimization_20261028/report_layout.json', JSON.stringify({all_passed: true, ...result}, null, 2)+'\n');
  console.log(JSON.stringify(result));
  await browser.close();
})().catch(error => {console.error(error.message); process.exit(1);});
